#!/usr/bin/python3

from gi.repository import Gtk, GObject, Gdk

from util import trackers
import status

class BaseWindow(Gtk.Revealer):
    """
    BaseWindow is the base class for all of the Stage GtkOverlay's immediate
    children.  It provides functionality for smooth fade-in and -out.
    """
    REVEALER_DURATION = 250

    def __init__(self, *args):
        super(BaseWindow, self).__init__()

        self.disabled = False

        c = Gdk.RGBA(0, 0, 0, 0)
        self.override_background_color (Gtk.StateFlags.NORMAL, c);

        self.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.set_transition_duration(self.REVEALER_DURATION)

    def _reveal_idle_callback(self):
        self.show_all()
        self.set_reveal_child(True)

    def reveal(self):
        if self.disabled:
            return
        GObject.idle_add(self._reveal_idle_callback)

    def unreveal(self):
        if self.disabled:
            return

        GObject.idle_add(self.set_reveal_child, False)

    def blink(self):
        self.set_reveal_child(False)
        GObject.timeout_add(self.REVEALER_DURATION + 10, self._blink_callback)

    def _blink_callback(self):
        self.set_reveal_child(True)

        return False

    def destroy_window(self):
        trackers.con_tracker_get().connect_after(self,
                                                 "notify::child-revealed",
                                                 self.destroy_after_hiding)

        self.unreveal()

    def destroy_after_hiding(self, pspec, data):
        trackers.con_tracker_get().disconnect(self,
                                              "notify::child-revealed",
                                              self.destroy_after_hiding)

        self.destroy()

    def update_geometry(self):
        if status.Spanned:
            self.rect = status.screen.get_screen_geometry()
        else:
            self.rect = status.screen.get_monitor_geometry(self.monitor_index)
