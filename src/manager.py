#! /usr/bin/python3

import gi
from gi.repository import Gdk, Gio

from overlay import ScreensaverOverlayWindow
from wallpaperWindow import WallpaperWindow
from pluginWindow import PluginWindow
from unlock import UnlockDialog
from clock import ClockWidget
import constants as c

import trackers
import utils
import time
import settings
from grabHelper import GrabHelper

import status
from status import Status

class ScreensaverManager:
    def __init__(self):
        self.grab_helper = GrabHelper(self)

        self.screen = Gdk.Screen.get_default()

        self.activated_timestamp = 0

        status.ScreensaverStatus = Status.UNLOCKED

##### Service handlers (from service.py)

    def is_locked(self):
        return status.ScreensaverStatus > Status.UNLOCKED

    def lock(self, msg):
        self.show_screensaver(msg)

    def unlock(self):
        self.kill_screensaver()

    def get_active_time(self):
        if self.activated_timestamp != 0:
            return int(time.time() - self.activated_timestamp)
        else:
            return 0

    def set_active(self, active):
        if active:
            self.show_screensaver("")
        else:
            self.kill_screensaver()

    def simulate_user_activity(self):
        self.raise_unlock_widget()
        self.reset_timeout()

    def set_plug_id(self, plug_id):
        self.overlay.set_plug_id(plug_id)

#####

    def show_screensaver(self, away_message):
        if self.grab_helper.grab_offscreen(True):
            self.overlay = ScreensaverOverlayWindow(self.screen, self, away_message)
            self.overlay.show_all()
            status.ScreensaverStatus = Status.LOCKED_IDLE
            self.activated_timestamp = time.time()
        else:
            print("Could not acquire grabs.  Screensaver not activated")

    def kill_screensaver(self):
        if self.activated_timestamp != 0:
            self.set_timeout_active(None, False)

            self.overlay.destroy()
            self.overlay = None

            self.grab_helper.release()

            status.ScreensaverStatus = Status.UNLOCKED
            self.activated_timestamp = 0























# GnomeBG stuff #

    def on_bg_changed(self, bg):
        pass

    def on_bg_settings_changed(self, settings, keys, n_keys):
        self.bg.load_from_preferences(self.bg_settings)
        self.refresh_backgrounds()

