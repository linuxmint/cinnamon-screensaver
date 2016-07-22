#! /usr/bin/python3

from gi.repository import Gdk
import time

import trackers
import utils
import settings
import status
from sessionProxy import SessionProxy
from fader import Fader
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
                        self.create_overlay(msg)
                        self.overlay_fader = Fader(self.overlay)
                        self.overlay_fader.fade_in(300, self.grab_overlay)
                    status.Active = True
                    self.service_message_cb("ActiveChanged", True)

                    self.activated_timestamp = time.time()
                    self.start_lock_delay()
                    self.start_logout_delay()
                    return True
                else:
                    status.Active = False
                    return False
            else:
                self.overlay.set_message(msg)
                return True
        else:
            if status.Active:
                status.Active = False
                self.service_message_cb("ActiveChanged", False)

                self.overlay_fader.fade_out(300, self.destroy_overlay)
                self.activated_timestamp = 0
                self.stop_lock_delay()
                self.stop_logout_delay()

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
        else:
            self.set_active(False)

#####

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
            status.LogoutEnabled = True
        else:
            trackers.timer_tracker_get().start_seconds("logout-button-delay",
                                                       logout_delay,
                                                       self.on_logout_delay_timeout)

    def stop_logout_delay(self):
        trackers.timer_tracker_get().cancel("logout-button-delay")

    def create_overlay(self, away_message):
        self.overlay = ScreensaverOverlayWindow(self.screen, self, away_message)
        self.overlay.show_all()

    def destroy_overlay(self):
        self.overlay.destroy_overlay()
        self.overlay = None

    def cancel_unlock_widget(self):
        self.overlay.cancel_unlock_widget();

##### EventHandler calls

    def queue_dialog_key_event(self, event):
        self.overlay.queue_dialog_key_event(event)

    def on_session_idle_changed(self, proxy, idle):
        if idle and not status.Active:
            if self.grab_helper.grab_offscreen(False):
                self.create_overlay("")
                self.overlay_fader = Fader(self.overlay)
                self.overlay_fader.fade_in(10 * 1000, self.session_idle_fade_in_complete)
            else:
                print("Can't fade in screensaver, unable to grab the keyboard")
        else:
            if not status.Active:
                if self.overlay_fader:
                    self.overlay_fader.cancel()
                    self.overlay_fader = None
                if self.overlay:
                    self.destroy_overlay()
                trackers.timer_tracker_get().start_seconds("release-grab-timeout",
                                                           1,
                                                           self.on_release_grab_timeout)

    def session_idle_fade_in_complete(self):
        self.set_active(True)
        self.grab_overlay()

    def grab_overlay(self):
        self.grab_helper.move_to_window(self.overlay.get_window(), True)

    def on_release_grab_timeout(self):
        if not status.Active:
            self.grab_helper.release()

        return False















