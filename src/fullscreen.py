#! /usr/bin/python3

from gi.repository import Gtk, Gdk, GObject
import utils

# FullscreenWindow is just a dummy OR window that takes care of putting
# us in fullscreen mode for all monitors.

class FullscreenWindow(Gtk.Window):
    def __init__(self, screen, index):
        super(FullscreenWindow, self).__init__(type=Gtk.WindowType.POPUP,
                                               decorated=False,
                                               skip_taskbar_hint=True,
                                               skip_pager_hint=True)

        self.screen = screen
        self.monitor_index = index

        c = self.get_style_context()
        c.remove_class("background")

        self.update_geometry()

        self.connect("realize", self.on_realized)
        self.connect("map", self.on_mapped)

        self.show()

        self.set_opacity(.1)

    def do_get_preferred_height(self):
        if self.get_realized():
            self.get_window().move(self.rect.x, self.rect.y)
            return self.rect.height, self.rect.height
        else:
            return 0, 0

    def do_get_preferred_width(self):
        if self.get_realized():
            self.get_window().move(self.rect.x, self.rect.y)
            return self.rect.width, self.rect.width
        else:
            return 0, 0

    def on_realized(self, widget):
        self.get_window().move_resize(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
        utils.override_user_time(self.get_window())
        self.fullscreen_on_monitor(self.screen, self.monitor_index)

    def on_mapped(self, widget):
        window = widget.get_window()
        # window.fullscreen()
        window.lower()

    def update_geometry(self):
        self.rect = rect = self.screen.get_monitor_geometry(self.monitor_index)
        print(rect.x, rect.y, rect.width, rect.height)

