#! /usr/bin/python3

from gi.repository import Gtk, GObject

from util import trackers
import singletons

class PowerWidget(Gtk.Frame):
    __gsignals__ = {
        'power-state-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(PowerWidget, self).__init__()
        self.get_style_context().add_class("powerwidget")

        self.path_widget_pairs = []

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.box)

        self.box.show_all()

        self.power_client = singletons.UPowerClient

        trackers.con_tracker_get().connect(self.power_client,
                                           "power-state-changed",
                                           self.on_power_state_changed)

        self.power_client.rescan_devices()

    def on_power_state_changed(self, client):
        for widget in self.box.get_children():
            widget.destroy()

        self.construct_icons()

        self.emit("power-state-changed")

    def construct_icons(self):
        batteries = self.power_client.get_batteries()

        for path, battery in batteries:
            image = Gtk.Image.new_from_icon_name(battery.get_property("icon-name"), Gtk.IconSize.LARGE_TOOLBAR)

            self.box.pack_start(image, False, False, 4)
            self.path_widget_pairs.append((path, image))

        self._should_show = True
        self.box.show_all()

    def should_show(self):
        return not self.power_client.full_and_on_ac_or_no_batteries()


