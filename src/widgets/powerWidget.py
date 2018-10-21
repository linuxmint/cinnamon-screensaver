#!/usr/bin/python3

from gi.repository import Gtk, GObject

from util import trackers
import singletons
import constants as c
import status

class PowerWidget(Gtk.Frame):
    """
    PowerWidget is a child of InfoPanel, and is only shown if we're on
    a system that can run on battery power.  It is usually only visible
    if the system is actually currently running on battery power.
    """
    __gsignals__ = {
        'power-state-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(PowerWidget, self).__init__()
        self.set_shadow_type(Gtk.ShadowType.NONE)
        self.get_style_context().add_class("powerwidget")

        self.path_widget_pairs = []

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.box)

        self.box.show_all()

        self.power_client = singletons.UPowerClient

        self.battery_critical = False

        trackers.con_tracker_get().connect(self.power_client,
                                           "power-state-changed",
                                           self.on_power_state_changed)

        trackers.con_tracker_get().connect(self.power_client,
                                           "percentage-changed",
                                           self.on_percentage_changed)

        self.power_client.rescan_devices()

        self.on_power_state_changed(self.power_client)

    def refresh(self):
        self.on_power_state_changed(self.power_client)

    def on_power_state_changed(self, client):
        for widget in self.box.get_children():
            widget.destroy()

        self.path_widget_pairs = []
        self.battery_critical = False

        self.construct_icons()

        self.emit("power-state-changed")

    def on_percentage_changed(self, client, battery):
        battery_path = battery.get_object_path()

        for path, widget in self.path_widget_pairs:
            if path == battery_path:
                self.update_battery_tooltip(widget, battery)
                break

    def construct_icons(self):
        """
        The upower dbus interface actually tells us what icon name to use.
        """
        batteries = self.power_client.get_batteries()

        for path, battery in batteries:
            if status.Debug:
                print("powerWidget: Updating battery info: %s - icon: %s - percentage: %s" %
                    (path, battery.get_property("icon-name"), battery.get_property("percentage")))

            image = Gtk.Image.new_from_icon_name(battery.get_property("icon-name"), Gtk.IconSize.LARGE_TOOLBAR)
            self.update_battery_tooltip(image, battery)

            self.box.pack_start(image, False, False, 4)
            self.path_widget_pairs.append((path, image))

        self._should_show = True
        self.box.show_all()

    def update_battery_tooltip(self, widget, battery):
        text = ""

        try:
            pct = int(battery.get_property("percentage"))

            if pct > 0:
                text = _("%d%%" % pct)
                if pct < c.BATTERY_CRITICAL_PERCENT:
                    self.battery_critical = True
        except Exception as e:
            pass

        widget.set_tooltip_text(text)

    def should_show(self):
        return not self.power_client.full_and_on_ac_or_no_batteries()
