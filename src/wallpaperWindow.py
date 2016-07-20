#! /usr/bin/python3

from gi.repository import Gtk
from baseWindow import BaseWindow
import trackers

class WallpaperWindow(BaseWindow):
    def __init__(self, screen, index):
        super(WallpaperWindow, self).__init__()

        self.screen = screen
        self.monitor_index = index

        self.update_geometry()

        self.bg_image = Gtk.Image()
        self.bg_image.show()
        self.bg_image.set_halign(Gtk.Align.FILL)
        self.bg_image.set_valign(Gtk.Align.FILL)

        self.add(self.bg_image)

        trackers.con_tracker_get().connect_after(self.bg_image,
                                                 "draw",
                                                 self.on_image_draw)

        self.show_all()

    def on_image_draw(self, widget, cr):
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.paint()
        return False


