#! /usr/bin/python3

from gi.repository import Gtk, Gdk
import utils
import trackers

class ScreensaverOverlayWindow(Gtk.Window):
    def __init__(self, screen):
        super(ScreensaverOverlayWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL,
                                                       decorated=False,
                                                       skip_taskbar_hint=True,
                                                       skip_pager_hint=True)

        self.screen = screen

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

    def update_geometry(self):
        self.rect = Gdk.Rectangle()
        self.rect.x = 0
        self.rect.y = 0
        self.rect.width = self.screen.get_width()
        self.rect.height = self.screen.get_height()
