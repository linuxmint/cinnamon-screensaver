#! /usr/bin/python3

from gi.repository import Gtk, Gdk, GLib, GObject
import dbus

import trackers
import status
from uPowerProxy import UPowerProxy

class PowerWidget(Gtk.Frame):
    __gsignals__ = {
        'power-state-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(PowerWidget, self).__init__()
        self.get_style_context().add_class("powerwidget")

        self._should_show = False
        self.path_widget_pairs = []

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.box)

        self.power_proxy = UPowerProxy()

        trackers.con_tracker_get().connect(self.power_proxy,
                                           "ready",
                                           self.on_proxy_loaded)

        trackers.con_tracker_get().connect(self.power_proxy,
                                           "power-state-changed",
                                           self.on_power_state_changed)

    def on_proxy_loaded(self, proxy):
        self.construct_icons()

    def on_power_state_changed(self, proxy):
        for widget in self.box.get_children():
            widget.destroy()

        self.construct_icons()

        self.emit("power-state-changed")

    def construct_icons(self):
        if self.power_proxy.full_and_on_ac_or_no_batteries():
            self._should_show = False
            return

        batteries = self.power_proxy.get_batteries()

        for path, battery in batteries:
            image = Gtk.Image.new_from_icon_name(self.power_proxy.get_battery_icon_name(path), Gtk.IconSize.LARGE_TOOLBAR)

            self.box.pack_start(image, False, False, 4)
            self.path_widget_pairs.append((path, image))

        self._should_show = True
        self.box.show_all()

    def should_show(self):
        return self._should_show


