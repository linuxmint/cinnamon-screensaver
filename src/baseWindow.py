#! /usr/bin/python3

from gi.repository import Gtk, GObject

from util import trackers

class BaseWindow(Gtk.Revealer):
    REVEALER_DURATION = 250

    def __init__(self):
        super(BaseWindow, self).__init__()

        self.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.set_transition_duration(self.REVEALER_DURATION)

    def _reveal_idle_callback(self):
        self.show_all()
        self.set_reveal_child(True)

    def reveal(self):
        GObject.idle_add(self._reveal_idle_callback)

    def unreveal(self):
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
        self.rect = self.screen.get_monitor_geometry(self.monitor_index)