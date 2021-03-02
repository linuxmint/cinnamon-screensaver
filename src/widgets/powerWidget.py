#!/usr/bin/python3

from gi.repository import Gtk, GObject, Gio

from util import trackers
import singletons
import constants as c
import status

UPOWER_STATE_CHARGING = 1
UPOWER_STATE_DISCHARGING = 2
UPOWER_STATE_FULLY_CHARGED = 4
UPOWER_STATE_PENDING_CHARGE = 5
UPOWER_STATE_PENDING_DISCHARGE = 6

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
            percentage = battery.get_property("percentage")
            gicon = self.get_gicon_for_current_level(battery);

            if status.Debug:
                print("powerWidget: Updating battery info: %s - icon: %s - percentage: %s" %
                    (path, gicon.to_string(), percentage))

            image = Gtk.Image.new_from_gicon(gicon, Gtk.IconSize.LARGE_TOOLBAR)
            self.update_battery_tooltip(image, battery)

            self.box.pack_start(image, False, False, 4)
            self.path_widget_pairs.append((path, image))

        self._should_show = True
        self.box.show_all()

    def get_gicon_for_current_level(self, battery):
        percentage = battery.get_property("percentage")
        state = battery.get_property("state")

        names = None

        if state in (UPOWER_STATE_CHARGING, UPOWER_STATE_DISCHARGING,
                     UPOWER_STATE_PENDING_CHARGE, UPOWER_STATE_PENDING_DISCHARGE):
            if percentage < 10:
                names = ["battery-level-0", "battery-caution"]
            elif percentage < 20:
                names = ["battery-level-10", "battery-low"]
            elif percentage < 30:
                names = ["battery-level-20", "battery-low"]
            elif percentage < 40:
                names = ["battery-level-30", "battery-good"]
            elif percentage < 50:
                names = ["battery-level-40", "battery-good"]
            elif percentage < 60:
                names = ["battery-level-50", "battery-good"]
            elif percentage < 70:
                names = ["battery-level-60", "battery-full"]
            elif percentage < 80:
                names = ["battery-level-70", "battery-full"]
            elif percentage < 90:
                names = ["battery-level-80", "battery-full"]
            elif percentage < 99:
                names = ["battery-level-90", "battery-full"]
            else:
                names = ["battery-level-100", "battery-full"]

            if state in (UPOWER_STATE_CHARGING, UPOWER_STATE_PENDING_CHARGE):
                names[0] += "-charging"
                names[1] += "-charging"

            names[0] += "-symbolic"
            names[1] += "-symbolic"
        elif state == UPOWER_STATE_FULLY_CHARGED:
            names = ["battery-level-100-charged-symbolic",
                     "battery-full-charged-symbolic",
                     "battery-full-charging-symbolic"]
        else:
            names = (battery.get_property("icon-name"),)

        return Gio.ThemedIcon.new_from_names(names)

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
