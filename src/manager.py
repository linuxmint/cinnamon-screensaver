#! /usr/bin/python3

from gi.repository import Gdk
import time
import traceback

import constants as c
import utils
import trackers
import settings
import status
from focusNavigator import FocusNavigator
from sessionProxy import SessionProxy
from logindProxy import LogindProxy, LogindConnectionError
from consoleKitProxy import ConsoleKitProxy, ConsoleKitConnectionError
from stage import Stage
from grabHelper import GrabHelper

class ScreensaverManager:
    def __init__(self, service_message_cb):
        self.screen = Gdk.Screen.get_default()
        self.service_message_cb = service_message_cb

        self.activated_timestamp = 0

        self.stage = None
        self.stage_fader = None

        # Ensure our state
        status.Active = False
        status.Locked = False
        status.Awake = False
        status.LogoutEnabled = False

        self.grab_helper = GrabHelper(self)
        self.focus_nav = FocusNavigator()

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
                if utils.user_can_lock():
                    status.Locked = True
        else:
            if utils.user_can_lock():
                status.Locked = True
            self.stage.set_message(msg)

    def unlock(self):
        self.set_active(False)
        status.Locked = False
        status.Awake = False

    def set_active(self, active, msg=None):
        if active:
            if not status.Active:
                if self.grab_helper.grab_root(False):
                    if not self.stage:
                        self.spawn_stage(msg, c.STAGE_SPAWN_TRANSITION, self.on_spawn_stage_complete)
                    return True
                else:
                    status.Active = False
                    return False
            else:
                self.stage.set_message(msg)
                return True
        else:
            if self.stage:
                self.despawn_stage(c.STAGE_DESPAWN_TRANSITION, self.on_despawn_stage_complete)
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
            self.stage.raise_unlock_widget()
            self.grab_helper.release_mouse()
        else:
            self.set_active(False)

        self.stage.maybe_update_layout()

#####

    def spawn_stage(self, away_message, effect_time=c.STAGE_SPAWN_TRANSITION, callback=None):
        try:
            self.stage = Stage(self.screen, self, away_message)
            self.stage.transition_in(effect_time, callback)
        except Exception:
            print("Could not spawn screensaver stage:\n")
            traceback.print_exc()
            self.grab_helper.release()
            status.Active = False
            self.cancel_timers()

    def despawn_stage(self, effect_time=c.STAGE_DESPAWN_TRANSITION, callback=None):
        self.stage.transition_out(effect_time, callback)

    def on_spawn_stage_complete(self):
        self.grab_stage()

        status.Active = True

        self.service_message_cb("ActiveChanged", True)

        self.start_timers()

    def on_despawn_stage_complete(self):
        was_active = status.Active == True
        status.Active = False

        if was_active:
            self.service_message_cb("ActiveChanged", False)

        self.cancel_timers()

        self.stage.destroy_stage()
        self.stage = None

    def grab_stage(self):
        self.grab_helper.move_to_window(self.stage.get_window(), True)

    def start_timers(self):
        self.activated_timestamp = time.time()
        self.start_lock_delay()

    def cancel_timers(self):
        self.activated_timestamp = 0
        self.stop_lock_delay()

    def cancel_unlock_widget(self):
        self.grab_stage()
        self.stage.cancel_unlock_widget();

    def on_lock_delay_timeout(self):
        status.Locked = True

        return False

    def start_lock_delay(self):
        if not settings.get_idle_lock_enabled():
            return

        if not utils.user_can_lock():
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

##### EventHandler/GrabHelper/FocusNavigator calls

    def queue_dialog_key_event(self, event):
        self.stage.queue_dialog_key_event(event)

    def propagate_tab_event(self, shifted):
        self.focus_nav.navigate(shifted)

    def propagate_activation(self):
        self.focus_nav.activate_focus()

    def get_focused_widget(self):
        return self.focus_nav.get_focused_widget()

# Session watcher handler:

    def on_session_idle_changed(self, proxy, idle):
        if idle and not status.Active:
            if self.grab_helper.grab_offscreen(False):
                self.spawn_stage("", c.STAGE_IDLE_SPAWN_TRANSITION, self.on_spawn_stage_complete)
            else:
                print("Can't fade in screensaver, unable to grab the keyboard")
        else:
            if not status.Active:
                if self.stage:
                    self.despawn_stage(c.STAGE_IDLE_CANCEL_SPAWN_TRANSITION, self.on_despawn_stage_complete)

                trackers.timer_tracker_get().start("release-grab-timeout",
                                                   c.GRAB_RELEASE_TIMEOUT,
                                                   self.on_release_grab_timeout)

    def on_release_grab_timeout(self):
        if not status.Active:
            self.grab_helper.release()

        return False















