#! /usr/bin/python3

import gi
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import CinnamonDesktop, Gdk, Gio

from overlay import ScreensaverOverlayWindow
from window import ScreensaverWindow
from unlock import UnlockDialog
from clock import ClockWidget
import constants as c

import trackers
import utils
import time
from grabHelper import GrabHelper

class ScreensaverManager:
    __singleton = None

    def get():
        if ScreensaverManager.__singleton == None:
            ScreensaverManager()
        return ScreensaverManager.__singleton

    def __init__(self):
        ScreensaverManager.__singleton = self

        self.bg = CinnamonDesktop.BG()

        self.grab_helper = GrabHelper()

        trackers.con_tracker_get().connect(self.bg,
                                           "changed", 
                                           self.on_bg_changed)

        self.bg_settings = Gio.Settings(schema_id="org.cinnamon.desktop.background")

        trackers.con_tracker_get().connect(self.bg_settings,
                                           "change-event",
                                           self.on_bg_settings_changed)

        self.bg.load_from_preferences(self.bg_settings)

        self.windows = []

        self.screen = Gdk.Screen.get_default()

        self.saved_key_events = []

        self.away_message = None

        self.overlay = None
        self.clock_widget = None
        self.unlock_dialog = None

        self.activated_timestamp = 0

        self.unlock_raised = False

##### Service handlers (from service.py)

    def is_locked(self):
        return self.activated_timestamp != 0

    def lock(self, msg):
        if self.grab_helper.grab_offscreen(True):
            self.away_message = msg
            self.setup_overlay()
            self.activated_timestamp = time.time()
        else:
            print("Could not acquire grabs.  Screensaver not activated")

    def unlock(self):
        if self.activated_timestamp != 0:
            self.set_timeout_active(None, False)
            self.overlay.destroy()
            self.overlay = None
            self.unlock_dialog = None
            self.clock_widget = None
            self.away_message = None
            self.activated_timestamp = 0
            self.windows = []
            self.unlock_raised = False
            self.grab_helper.release()

    def get_active_time(self):
        if self.activated_timestamp != 0:
            return int(time.time() - self.activated_timestamp)
        else:
            return 0

    def simulate_user_activity(self):
        self.raise_unlock_widget()
        self.reset_timeout()

# Create all the widgets, connections when the screensaver is activated #

    def setup_overlay(self):
        self.overlay = ScreensaverOverlayWindow(self.screen)

        trackers.con_tracker_get().connect(self.overlay,
                                           "realize",
                                           self.on_overlay_realized)

        self.overlay.show_all()

    def on_overlay_realized(self, widget):
        self.setup_windows()
        self.setup_clock()
        self.setup_unlock()

    def setup_windows(self):
        n = self.screen.get_n_monitors()

        for index in range(n):
            primary = self.screen.get_primary_monitor() == index

            window = ScreensaverWindow(self.screen, index, primary)

            trackers.con_tracker_get().connect(window.bg_image,
                                               "realize",
                                               self.on_window_bg_image_realized,
                                               window)

            self.windows.append(window)

            window.reveal()

            self.overlay.add_child(window)
            self.overlay.put_on_bottom(window)

            window.queue_draw()

    def on_window_bg_image_realized(self, widget, window):
        trackers.con_tracker_get().disconnect(window.bg_image,
                                              "realize",
                                              self.on_window_bg_image_realized)
        self.bg.create_and_set_gtk_image (widget, window.rect.width, window.rect.height)
        widget.queue_draw()

    def setup_clock(self):
        self.clock_widget = ClockWidget(self.away_message, utils.get_mouse_monitor())
        self.overlay.add_child(self.clock_widget)
        self.overlay.put_on_top(self.clock_widget)

        self.clock_widget.show_all()

        self.clock_widget.reveal()
        self.clock_widget.start_positioning()

    def setup_unlock(self):
        self.unlock_dialog = UnlockDialog()
        self.overlay.add_child(self.unlock_dialog)

        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "inhibit-timeout",
                                           self.set_timeout_active, False)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "uninhibit-timeout",
                                           self.set_timeout_active, True)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "auth-success",
                                           self.authentication_result_callback, True)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "auth-failure",
                                           self.authentication_result_callback, False)

# Timer stuff - after a certain time, the unlock dialog will cancel itself.
# This timer is suspended during authentication, and any time a new user event is received

    def reset_timeout(self):
        self.set_timeout_active(None, True)

    def set_timeout_active(self, dialog, active):
        if active:
            trackers.timer_tracker_get().start("wake-timeout",
                                               c.UNLOCK_TIMEOUT * 1000,
                                               self.on_wake_timeout)
        else:
            trackers.timer_tracker_get().cancel("wake-timeout")

    def authentication_result_callback(self, dialog, success):
        if success:
            self.unlock()
        else:
            self.unlock_dialog.blink()

    def on_wake_timeout(self):
        self.set_timeout_active(None, False)
        self.cancel_lock_widget()

        return False

# Methods that manipulate the unlock dialog

    def raise_unlock_widget(self):
        if self.unlock_raised:
            return

        self.clock_widget.stop_positioning()
        self.unlock_raised = True

        self.unlock_dialog.reveal()
        self.clock_widget.reveal()

    def cancel_lock_widget(self):
        if not self.unlock_raised:
            return

        self.set_timeout_active(None, False)

        self.unlock_dialog.cancel()
        self.unlock_raised = False

        self.clock_widget.start_positioning()

# GnomeBG stuff #

    def on_bg_changed(self, bg):
        pass

    def on_bg_settings_changed(self, settings, keys, n_keys):
        self.bg.load_from_preferences(self.bg_settings)
        self.refresh_backgrounds()

