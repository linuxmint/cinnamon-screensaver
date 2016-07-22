#! /usr/bin/python3

import gi
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, Gdk, CinnamonDesktop
import random

import utils
import trackers
import settings
import status
import constants as c
from eventHandler import EventHandler
from wallpaperWindow import WallpaperWindow
from pluginWindow import PluginWindow
from unlock import UnlockDialog
from clock import ClockWidget

class ScreensaverOverlayWindow(Gtk.Window):
    def __init__(self, screen, manager, away_message):
        Gtk.Window.__init__(self,
                            type=Gtk.WindowType.POPUP,
                            decorated=False,
                            skip_taskbar_hint=True,
                            skip_pager_hint=True)

        self.bg = CinnamonDesktop.BG()
        trackers.con_tracker_get().connect(self.bg,
                                           "changed", 
                                           self.on_bg_changed)
        self.bg.load_from_preferences(settings.bg_settings)

        self.manager = manager
        self.screen = screen

        self.away_message = away_message

        self.windows = []
        self.overlay = None
        self.clock_widget = None
        self.unlock_dialog = None

        self.event_handler = EventHandler(manager)

        self.get_style_context().remove_class("background")

        self.set_events(self.get_events() |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.KEY_RELEASE_MASK |
                        Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.VISIBILITY_NOTIFY_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK |
                        Gdk.EventMask.FOCUS_CHANGE_MASK)

        self.update_geometry()

        self.set_keep_above(True)
        self.fullscreen()

        self.overlay = Gtk.Overlay()

        trackers.con_tracker_get().connect(self.overlay,
                                           "realize",
                                           self.on_realized)

        trackers.con_tracker_get().connect(self.overlay,
                                           "get-child-position",
                                           self.position_overlay_child)

        self.overlay.show_all()
        self.add(self.overlay)

    def focus_and_present(self):
        utils.override_user_time(self.get_window())
        self.present()

    def on_realized(self, widget):
        window = self.get_window()
        window.set_fullscreen_mode(Gdk.FullscreenMode.ALL_MONITORS)
        window.move_resize(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

        self.setup_children()

        self.focus_and_present()

    def setup_children(self):
        self.setup_windows()
        self.setup_clock()
        self.setup_unlock()

    def destroy_overlay(self):
        self.set_timeout_active(None, False)

        for window in self.windows:
            window.destroy()

        self.unlock_dialog = None
        self.clock_widget = None
        self.away_message = None
        self.windows = []
        self.destroy()

    def set_plug_id(self, plug_id):
        for window in self.windows:
            if window.has_plug():
                continue
            window.set_plug_id(plug_id)
            break

    def setup_windows(self):
        n = self.screen.get_n_monitors()

        for index in range(n):
            name = settings.get_screensaver_name()
            path = utils.lookup_plugin_path(name)
            if path is not None:
                window = PluginWindow(self.screen, index, path)
            else:
                window = WallpaperWindow(self.screen, index)
                trackers.con_tracker_get().connect(window.bg_image,
                                                   "realize",
                                                   self.on_wallpaper_window_bg_image_realized,
                                                   window)

            self.windows.append(window)

            window.reveal()

            self.add_child_widget(window)
            self.put_on_bottom(window)

            window.queue_draw()

    def on_wallpaper_window_bg_image_realized(self, widget, window):
        trackers.con_tracker_get().disconnect(window.bg_image,
                                              "realize",
                                              self.on_wallpaper_window_bg_image_realized)
        self.bg.create_and_set_gtk_image (widget, window.rect.width, window.rect.height)
        widget.queue_draw()

    def on_bg_changed(self, bg):
        pass

    def setup_clock(self):
        self.clock_widget = ClockWidget(self.away_message, utils.get_mouse_monitor())
        self.add_child_widget(self.clock_widget)
        self.put_on_top(self.clock_widget)

        self.clock_widget.show_all()

        self.clock_widget.reveal()
        self.clock_widget.start_positioning()

    def setup_unlock(self):
        self.unlock_dialog = UnlockDialog()
        self.add_child_widget(self.unlock_dialog)

        # Prevent a dialog timeout during authentication
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "inhibit-timeout",
                                           self.set_timeout_active, False)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "uninhibit-timeout",
                                           self.set_timeout_active, True)

        # Respond to authentication success/failure
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "auth-success",
                                           self.authentication_result_callback, True)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "auth-failure",
                                           self.authentication_result_callback, False)

    def queue_dialog_key_event(self, event):
        self.unlock_dialog.queue_key_event(event)

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

    def on_wake_timeout(self):
        self.set_timeout_active(None, False)
        self.cancel_lock_widget()

        return False

    def authentication_result_callback(self, dialog, success):
        if success:
            self.manager.unlock()
        else:
            self.unlock_dialog.blink()

    def simulate_user_activity(self):
        if not status.Active:
            return

        if status.Locked:
            self.raise_unlock_widget()
            self.reset_timeout()
        else:
            self.manager.set_active(False)

    def set_message(self, msg):
        self.clock_widget.set_message(msg)

    def update_logout_button(self):
        self.unlock_dialog.update_logout_button()

# Methods that manipulate the unlock dialog

    def raise_unlock_widget(self):
        if status.Awake:
            return

        self.clock_widget.stop_positioning()

        self.unlock_dialog.reveal()
        self.clock_widget.reveal()

        status.Awake = True

    def cancel_unlock_widget(self):
        if not status.Awake:
            return

        self.set_timeout_active(None, False)

        self.unlock_dialog.cancel()
        status.Awake = False

        self.clock_widget.start_positioning()

    def do_get_preferred_height(self):
        if self.get_realized():
            self.get_window().move(0, 0)
            return self.rect.height, self.rect.height
        else:
            return 0, 0

    def do_get_preferred_width(self):
        if self.get_realized():
            self.get_window().move(0, 0)
            return self.rect.width, self.rect.width
        else:
            return 0, 0

    def do_motion_notify_event(self, event):
        return self.event_handler.on_motion_event(event)

    def do_key_press_event(self, event):
        return self.event_handler.on_key_press_event(event)

    def do_button_press_event(self, event):
        return self.event_handler.on_button_press_event(event)

    # Override BaseWindow.update_geometry
    def update_geometry(self):
        self.rect = Gdk.Rectangle()
        self.rect.x = 0
        self.rect.y = 0
        self.rect.width = self.screen.get_width()
        self.rect.height = self.screen.get_height()

# Overlay window management #

    def add_child_widget(self, widget):
        self.overlay.add_overlay(widget)

    def put_on_top(self, widget):
        self.overlay.reorder_overlay(widget, -1)
        self.overlay.queue_draw()

    def put_on_bottom(self, widget):
        self.overlay.reorder_overlay(widget, 0)
        self.overlay.queue_draw()

    def position_overlay_child(self, overlay, child, allocation):
        if isinstance(child, WallpaperWindow) or isinstance(child, PluginWindow):
            allocation.x = child.rect.x
            allocation.y = child.rect.y
            allocation.width = child.rect.width
            allocation.height = child.rect.height

            return True

        if isinstance(child, UnlockDialog):
            monitor = utils.get_mouse_monitor()
            monitor_rect = self.screen.get_monitor_geometry(monitor)

            min_rect, nat_rect = child.get_preferred_size()

            allocation.width = nat_rect.width
            allocation.height = nat_rect.height

            allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (nat_rect.width / 2)
            allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)

            return True

        if isinstance(child, ClockWidget):
            min_rect, nat_rect = child.get_preferred_size()

            if status.Awake:
                monitor_rect = self.screen.get_monitor_geometry(utils.get_mouse_monitor())

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
