#! /usr/bin/python3

from gi.repository import Gdk

from overlay import ScreensaverOverlayWindow

import trackers
import utils
import time
import settings
from grabHelper import GrabHelper

import status

class ScreensaverManager:
    def __init__(self):
        self.grab_helper = GrabHelper(self)

        self.screen = Gdk.Screen.get_default()

        self.activated_timestamp = 0
        self.lock_delay_id = 0

        # Ensure our state
        status.Active = False
        status.Locked = False
        status.Awake = False
        status.LogoutEnabled = False

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
                if self.show_screensaver(msg):
                    status.Active = True
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
                self.kill_screensaver()
                self.activated_timestamp = 0
                self.stop_lock_delay()
                self.stop_logout_delay()
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
        self.overlay.simulate_user_activity()

    def set_plug_id(self, plug_id):
        self.overlay.set_plug_id(plug_id)

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


    def show_screensaver(self, away_message):
        if self.grab_helper.grab_offscreen(True):
            self.overlay = ScreensaverOverlayWindow(self.screen, self, away_message)
            self.overlay.show_all()
            return True
        else:
            print("Could not acquire grabs.  Screensaver not activated")
            return False

    def kill_screensaver(self):
        self.overlay.destroy_overlay()
        self.overlay = None
        self.grab_helper.release()

    def cancel_unlock_widget(self):
        self.overlay.cancel_unlock_widget();

##### EventHandler calls

    def queue_dialog_key_event(self, event):
        self.overlay.queue_dialog_key_event(event)
















