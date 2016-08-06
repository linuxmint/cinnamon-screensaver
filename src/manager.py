#! /usr/bin/python3

from gi.repository import Gdk
import time
import sys
import traceback

import constants as c
import trackers
import utils
import settings
import status
from sessionProxy import SessionProxy
from logindProxy import LogindProxy, LogindConnectionError
from consoleKitProxy import ConsoleKitProxy, ConsoleKitConnectionError
from overlay import ScreensaverOverlayWindow
from grabHelper import GrabHelper

class ScreensaverManager:
    def __init__(self, service_message_cb):
        self.screen = Gdk.Screen.get_default()
        self.service_message_cb = service_message_cb

        self.activated_timestamp = 0
        self.lock_delay_id = 0

        self.overlay = None
        self.overlay_fader = None

        # Ensure our state
        status.Active = False
        status.Locked = False
        status.Awake = False
        status.LogoutEnabled = False

        self.grab_helper = GrabHelper(self)

        self.session_watcher = SessionProxy()
        trackers.con_tracker_get().connect(self.session_watcher,
                                           "idle-changed", 
                                           self.on_session_idle_changed)

        try:
            self.logind_watcher = LogindProxy()
            trackers.con_tracker_get().connect(self.logind_watcher,
                                               "lock",
                                               lambda proxy: self.lock())
            trackers.con_tracker_get().connect(self.logind_watcher,
                                               "unlock",
                                               lambda proxy: self.unlock())
            trackers.con_tracker_get().connect(self.logind_watcher,
                                               "active",
                                               lambda proxy: self.simulate_user_activity())
        except LogindConnectionError:
            print("no logind, trying ConsoleKit")
            try:
                self.ck_watcher = ConsoleKitProxy()
                trackers.con_tracker_get().connect(self.ck_watcher,
                                                   "lock",
                                                   lambda proxy: self.lock())
                trackers.con_tracker_get().connect(self.ck_watcher,
                                                   "unlock",
                                                   lambda proxy: self.unlock())
                trackers.con_tracker_get().connect(self.ck_watcher,
                                                   "active",
                                                   lambda proxy: self.simulate_user_activity())
            except ConsoleKitConnectionError:
                print("ConsoleKit failed, continuing, but certain functionality will be limited")

##### Service handlers (from service.py)

    def is_locked(self):
        return status.Locked

    def lock(self, msg=""):
        if not status.Active:
            if self.set_active(True, msg):
                self.stop_lock_delay()
                status.Locked = True
        else:
            status.Locked = True
            self.overlay.set_message(msg)

    def unlock(self):
        self.set_active(False)
        status.Locked = False
        status.Awake = False

    def set_active(self, active, msg=None):
        if active:
            if not status.Active:
                if self.grab_helper.grab_root(False):
                    if not self.overlay:
                        self.spawn_overlay(msg, c.OVERLAY_SPAWN_TRANSITION, self.on_spawn_overlay_complete)
                    return True
                else:
                    status.Active = False
                    return False
            else:
                self.overlay.set_message(msg)
                return True
        else:
            if self.overlay:
                self.despawn_overlay(c.OVERLAY_DESPAWN_TRANSITION, self.on_despawn_overlay_complete)
            self.grab_helper.release()
            return True
        return False

    def get_active(self):
        return status.Active

    def get_active_time(self):
        if self.activated_timestamp != 0:
            return int(time.time() - self.activated_timestamp)
        else:
            return 0

    def simulate_user_activity(self):
        if not status.Active:
            return

        if status.Locked:
            self.overlay.raise_unlock_widget()
            self.grab_helper.release_mouse()
        else:
            self.set_active(False)

        self.overlay.maybe_update_layout()

#####

    def spawn_overlay(self, away_message, effect_time=c.OVERLAY_SPAWN_TRANSITION, callback=None):
        try:
            self.overlay = ScreensaverOverlayWindow(self.screen, self, away_message)
            self.overlay.transition_in(effect_time, callback)
        except Exception:
            print("Could not spawn screensaver overlay:\n")
            traceback.print_exc()
            self.grab_helper.release()
            status.Active = False
            self.cancel_timers()
            raise e

    def despawn_overlay(self, effect_time=c.OVERLAY_DESPAWN_TRANSITION, callback=None):
        self.overlay.transition_out(effect_time, callback)

    def on_spawn_overlay_complete(self):
        self.grab_overlay()

        status.Active = True

        self.service_message_cb("ActiveChanged", True)

        self.start_timers()

    def on_despawn_overlay_complete(self):
        was_active = status.Active == True
        status.Active = False

        if was_active:
            self.service_message_cb("ActiveChanged", False)

        self.cancel_timers()

        self.overlay.destroy_overlay()
        self.overlay = None

    def grab_overlay(self):
        self.grab_helper.move_to_window(self.overlay.get_window(), True)

    def start_timers(self):
        self.activated_timestamp = time.time()
        self.start_lock_delay()
        self.start_logout_delay()

    def cancel_timers(self):
        self.activated_timestamp = 0
        self.stop_lock_delay()
        self.stop_logout_delay()

    def cancel_unlock_widget(self):
        self.grab_overlay()
        self.overlay.cancel_unlock_widget();

    def on_lock_delay_timeout(self):
        status.Locked = True

        return False

    def start_lock_delay(self):
        if not settings.get_idle_lock_enabled():
            return

        lock_delay = settings.get_idle_lock_delay()

        if lock_delay == 0:
            self.on_lock_delay_timeout()
        else:
            trackers.timer_tracker_get().start_seconds("idle-lock-delay",
                                                       lock_delay,
                                                       self.on_lock_delay_timeout)

    def stop_lock_delay(self):
        trackers.timer_tracker_get().cancel("idle-lock-delay")

    def on_logout_delay_timeout(self):
        status.LogoutEnabled = True
        self.overlay.update_logout_button()

        return False

    def start_logout_delay(self):
        if not utils.should_show_logout():
            return

        logout_delay = settings.get_logout_delay()

        if logout_delay == 0:
            self.on_logout_delay_timeout()
        else:
            trackers.timer_tracker_get().start_seconds("logout-button-delay",
                                                       logout_delay,
                                                       self.on_logout_delay_timeout)

    def stop_logout_delay(self):
        trackers.timer_tracker_get().cancel("logout-button-delay")

##### EventHandler call

    def queue_dialog_key_event(self, event):
        self.overlay.queue_dialog_key_event(event)

# Session watcher handler:

    def on_session_idle_changed(self, proxy, idle):
        if idle and not status.Active:
            if self.grab_helper.grab_offscreen(False):
                self.spawn_overlay("", c.OVERLAY_IDLE_SPAWN_TRANSITION, self.on_spawn_overlay_complete)
            else:
                print("Can't fade in screensaver, unable to grab the keyboard")
        else:
            if not status.Active:
                if self.overlay:
                    self.despawn_overlay(c.OVERLAY_IDLE_CANCEL_SPAWN_TRANSITION, self.on_despawn_overlay_complete)

                trackers.timer_tracker_get().start("release-grab-timeout",
                                                   c.GRAB_RELEASE_TIMEOUT,
                                                   self.on_release_grab_timeout)

    def on_release_grab_timeout(self):
        if not status.Active:
            self.grab_helper.release()

        return False















