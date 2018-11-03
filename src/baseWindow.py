#!/usr/bin/python3

from gi.repository import Gtk, GObject, Gdk

from util import trackers
import status

class BaseWindow(Gtk.Bin):
    """
    BaseWindow is the base class for all of the Stage GtkOverlay's immediate
    children.
    """

    def __init__(self, *args):
        super(BaseWindow, self).__init__()

        self.disabled = False

        c = Gdk.RGBA(0, 0, 0, 0)
        self.override_background_color (Gtk.StateFlags.NORMAL, c);

    def destroy_window(self):
        self.destroy()

    def update_geometry(self):
        if status.Spanned:
            self.rect = status.screen.get_screen_geometry()
        else:
            self.rect = status.screen.get_monitor_geometry(self.monitor_index)
