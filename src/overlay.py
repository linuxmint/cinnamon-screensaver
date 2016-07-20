#! /usr/bin/python3

from gi.repository import Gtk, Gdk
import utils
import trackers

from eventHandler import EventHandler

from wallpaperWindow import WallpaperWindow
from pluginWindow import PluginWindow
from unlock import UnlockDialog
from clock import ClockWidget

import status
from status import Status

import random

class ScreensaverOverlayWindow(Gtk.Window):
    def __init__(self, screen, manager):
        super(ScreensaverOverlayWindow, self).__init__(type=Gtk.WindowType.POPUP,
                                                       decorated=False,
                                                       skip_taskbar_hint=True,
                                                       skip_pager_hint=True)

        self.screen = screen

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

    def on_realized(self, widget):
        window = self.get_window()
        window.set_fullscreen_mode(Gdk.FullscreenMode.ALL_MONITORS)
        window.move_resize(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

        self.focus_and_present()

    def focus_and_present(self):
        utils.override_user_time(self.get_window())
        self.present()

    def add_child(self, widget):
        self.overlay.add_overlay(widget)

    def put_on_top(self, widget):
        self.overlay.reorder_overlay(widget, -1)
        self.overlay.queue_draw()

    def put_on_bottom(self, widget):
        self.overlay.reorder_overlay(widget, 0)
        self.overlay.queue_draw()

    def update_geometry(self):
        self.rect = Gdk.Rectangle()
        self.rect.x = 0
        self.rect.y = 0
        self.rect.width = self.screen.get_width()
        self.rect.height = self.screen.get_height()

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
        # print("OverlayWindow: do_motion_notify_event")
        return self.event_handler.on_motion_event(event)

    def do_key_press_event(self, event):
        # print("OverlayWindow: do_key_press_event")
        return self.event_handler.on_key_press_event(event)

    def do_button_press_event(self, event):
        # print("OverlayWindow: do_button_press_event")
        return self.event_handler.on_button_press_event(event)


# Overlay window management #

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

            if status.ScreensaverStatus == Status.LOCKED_AWAKE:
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
