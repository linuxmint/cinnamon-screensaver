#! /usr/bin/python3

import gi
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, CinnamonDesktop, Gdk, Gio
import random

from overlay import ScreensaverOverlayWindow
from window import ScreensaverWindow
from lock import LockDialog
from clock import ClockWidget
import trackers
import utils
import time

UNLOCK_TIMEOUT = 5

class ScreensaverManager:
    def __init__(self):
        self.bg = CinnamonDesktop.BG()

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
        self.lock_dialog = None

        self.activated_timestamp = 0

        self.focus_monitor = self.get_monitor_at_pointer_position()

        self.lock_raised = False

    def is_locked(self):
        return self.activated_timestamp != 0

    def lock(self, msg):
        self.away_message = msg
        self.setup_overlay()
        self.activated_timestamp = time.time()

    def unlock(self):
        if self.activated_timestamp != 0:
            self.set_timeout_active(None, False)
            self.disconnect_events()
            self.overlay.destroy()
            self.overlay = None
            self.lock_dialog = None
            self.clock_widget = None
            self.away_message = None
            self.activated_timestamp = 0
            self.windows = []
            self.lock_raised = False

    def get_active_time(self):
        if self.activated_timestamp != 0:
            return int(time.time() - self.activated_timestamp)
        else:
            return 0

    def simulate_user_activity(self):
        self.on_event(self, self.overlay, None)

# Setup the stuff #

    def setup_overlay(self):
        self.overlay = ScreensaverOverlayWindow(self.screen)

        trackers.con_tracker_get().connect(self.overlay.overlay,
                                           "get-child-position",
                                           self.position_overlay_child)

        trackers.con_tracker_get().connect(self.overlay,
                                           "realize",
                                           self.on_overlay_realized)

        self.overlay.show_all()

    def on_overlay_realized(self, widget):
        self.setup_windows()
        self.setup_clock()
        self.setup_lock()
        self.setup_events()

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
        self.clock_widget = ClockWidget(self.away_message, self.focus_monitor)

        self.overlay.add_child(self.clock_widget)
        self.overlay.put_on_top(self.clock_widget)

        self.clock_widget.show_all()

        self.clock_widget.reveal()
        self.clock_widget.start_positioning()

    def setup_events(self):
        trackers.con_tracker_get().connect(self.overlay,
                                           "button-press-event",
                                           self.on_event)
        trackers.con_tracker_get().connect(self.overlay,
                                           "button-release-event",
                                           self.on_event)
        trackers.con_tracker_get().connect(self.overlay,
                                           "key-press-event",
                                           self.on_key_press)
        trackers.con_tracker_get().connect(self.overlay,
                                           "key-release-event",
                                           self.on_event)
        trackers.con_tracker_get().connect(self.overlay,
                                           "motion-notify-event",
                                           self.on_event)

    def disconnect_events(self):
        trackers.con_tracker_get().disconnect(self.overlay,
                                              "button-press-event",
                                              self.on_event)
        trackers.con_tracker_get().disconnect(self.overlay,
                                              "button-release-event",
                                              self.on_event)
        trackers.con_tracker_get().disconnect(self.overlay,
                                              "key-press-event",
                                              self.on_key_press)
        trackers.con_tracker_get().disconnect(self.overlay,
                                              "key-release-event",
                                              self.on_event)
        trackers.con_tracker_get().disconnect(self.overlay,
                                              "motion-notify-event",
                                              self.on_event)

    def setup_lock(self):
        self.lock_dialog = LockDialog()
        self.overlay.add_child(self.lock_dialog)
        self.overlay.set_default(self.lock_dialog.auth_unlock_button)

        trackers.con_tracker_get().connect(self.lock_dialog,
                                           "inhibit-timeout",
                                           self.set_timeout_active, False)
        trackers.con_tracker_get().connect(self.lock_dialog,
                                           "uninhibit-timeout",
                                           self.set_timeout_active, True)
        trackers.con_tracker_get().connect(self.lock_dialog,
                                           "auth-success",
                                           self.authentication_result_callback, True)
        trackers.con_tracker_get().connect(self.lock_dialog,
                                           "auth-failure",
                                           self.authentication_result_callback, False)

    def set_timeout_active(self, dialog, active):
        if active:
            trackers.timer_tracker_get().start("wake-timeout",
                                               UNLOCK_TIMEOUT * 1000,
                                               self.on_wake_timeout)
        else:
            trackers.timer_tracker_get().cancel("wake-timeout")

    def authentication_result_callback(self, dialog, success):
        if success:
            self.unlock()
        else:
            self.lock_dialog.blink()

# Event Handling #

    def on_event(self, widget, event):
        cont = Gdk.EVENT_PROPAGATE

        self.focus_monitor = self.get_monitor_at_pointer_position()

        if not self.lock_raised:
            self.raise_lock_widget()
            cont = Gdk.EVENT_STOP

        if self.lock_raised:
            self.overlay.put_on_top(self.clock_widget)
            self.overlay.put_on_top(self.lock_dialog)
            # cont = self.handle_event_with_lock(event)

        self.set_timeout_active(None, True)

        return cont

    def on_key_press(self, widget, event):
        if not self.lock_dialog.entry_is_focus() and event.string != "":
            self.lock_dialog.queue_key_event(event)

        return self.on_event(widget, event)

    def on_wake_timeout(self):
        self.set_timeout_active(None, False)
        self.cancel_lock_widget()

        return False

    def raise_lock_widget(self):
        self.clock_widget.stop_positioning()
        self.lock_raised = True

        self.lock_dialog.reveal()
        self.clock_widget.reveal()

        self.overlay.focus_and_present()

    def cancel_lock_widget(self):
        self.lock_dialog.unreveal()
        self.lock_raised = False

        self.clock_widget.start_positioning()

# GnomeBG stuff #

    def on_bg_changed(self, bg):
        pass

    def on_bg_settings_changed(self, settings, keys, n_keys):
        self.bg.load_from_preferences(self.bg_settings)
        self.refresh_backgrounds()

# Overlay window management #

    def position_overlay_child(self, overlay, child, allocation):
        if isinstance(child, ScreensaverWindow):
            allocation.x = child.rect.x
            allocation.y = child.rect.y
            allocation.width = child.rect.width
            allocation.height = child.rect.height

            return True

        if isinstance(child, LockDialog):
            monitor = self.get_monitor_at_pointer_position()
            monitor_rect = self.screen.get_monitor_geometry(monitor)

            min_rect, nat_rect = child.get_preferred_size()

            allocation.width = nat_rect.width
            allocation.height = nat_rect.height

            allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (nat_rect.width / 2)
            allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)

            return True

        if isinstance(child, ClockWidget):
            min_rect, nat_rect = child.get_preferred_size()

            if self.lock_raised:
                monitor_rect = self.screen.get_monitor_geometry(self.focus_monitor)

                allocation.width = nat_rect.width
                allocation.height = nat_rect.height

                allocation.x = monitor_rect.x
                allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)

                return True
            else:
                current_monitor = child.current_monitor

                monitor_rect = self.screen.get_monitor_geometry(current_monitor)

                allocation.width = nat_rect.width
                allocation.height = nat_rect.height

                halign = child.get_halign()
                valign = child.get_valign()

                if halign == Gtk.Align.START:
                    allocation.x = monitor_rect.x
                elif halign == Gtk.Align.CENTER:
                    allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (nat_rect.width / 2)
                elif halign == Gtk.Align.END:
                    allocation.x = monitor_rect.x + monitor_rect.width - nat_rect.width

                if valign == Gtk.Align.START:
                    allocation.y = monitor_rect.y
                elif valign == Gtk.Align.CENTER:
                    allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)
                elif valign == Gtk.Align.END:
                    allocation.y = monitor_rect.y + monitor_rect.height - nat_rect.height

                if self.screen.get_n_monitors() > 1:
                    new_monitor = current_monitor
                    while new_monitor == current_monitor:
                        new_monitor = random.randint(0, self.screen.get_n_monitors() - 1)
                    child.current_monitor = new_monitor

                # utils.debug_allocation(allocation)

                return True

        return False

# Utilities #

    def get_monitor_at_pointer_position(self):
        if self.overlay == None:
            return 0

        manager = Gdk.Display.get_default().get_device_manager()
        pointer = manager.get_client_pointer()

        window, x, y, mask = self.overlay.get_window().get_device_position(pointer)

        return self.screen.get_monitor_at_point(x, y)
