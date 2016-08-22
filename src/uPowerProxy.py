#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib
import os
from enum import IntEnum
import dbus

import constants as c
import trackers

class DeviceType(IntEnum):
    Unknown = 0
    LinePower = 1
    Battery = 2
    Ups = 3
    Monitor = 4
    Mouse = 5
    Keyboard = 6
    Pda = 7
    Phone = 8

class DeviceState(IntEnum):
    Unknown = 0
    Charging = 1
    Discharging = 2
    Empty = 3
    FullyCharged = 4
    PendingCharge = 5
    PendingDischarge = 6

class UPowerConnectionError(Exception):
    pass

class UPowerProxy(GObject.GObject):
    __gsignals__ = {
        'ready': (GObject.SignalFlags.RUN_LAST, None, ()),
        'power-state-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(UPowerProxy, self).__init__()

        self.proxy = None

        self.loaded = False
        self.have_battery = False
        self.plugged_in = False

        self.relevant_devices = []

        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                      c.UPOWER_SERVICE, c.UPOWER_PATH, c.UPOWER_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except GLib.Error as e:
            print("Could not acquire UPower system proxy", e)
            raise UPowerConnectionError

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
        trackers.con_tracker_get().connect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

        trackers.con_tracker_get().connect(self.proxy,
                                           "g-properties-changed",
                                           self.on_properties_changed)

        self.rescan_devices()

    def on_signal(self, proxy, sender, signal, params):
        if signal == "DeviceRemoved":
            removed_path = params[0]
            for path, obj in self.relevant_devices:
                if removed_path == path:
                    trackers.con_tracker_get().disconnect(obj,
                                                          "g-properties-changed",
                                                          self.on_device_properties_changed)
            
        self.rescan_devices()

    def on_properties_changed(self, proxy, changed, invalid):
        self.rescan_devices()

    def rescan_devices(self):
        self.proxy.call("EnumerateDevices",
                        GLib.Variant("()", ()),
                        Gio.DBusCallFlags.NONE, -1, None,
                        self.enumerate_devices_callback, None)

    def enumerate_devices_callback(self, proxy, res, data=None):
        results = proxy.call_finish(res)[0]
        bus = dbus.SystemBus()

        self.relevant_devices = []

        for path in results:
            dev = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                                 c.UPOWER_SERVICE, path, c.UPOWER_DEVICE_INTERFACE,
                                                 None)

            if self.get_device_type(dev) in (DeviceType.Battery, DeviceType.LinePower):
                self.relevant_devices.append((path, dev))
                trackers.con_tracker_get().connect(dev,
                                                   "g-properties-changed",
                                                   self.on_device_properties_changed)

        if len(self.get_batteries()) == 0:
            self.have_battery = False
            return;

        self.have_battery = True

        self.check_current_devices()

        if not self.loaded:
            self.loaded = True
            self.emit("ready")

    def on_device_properties_changed(self, proxy, changed, invalid):
        keys_changed = changed.keys()

        if "Online" in keys_changed or "IconName" in keys_changed or "State" in keys_changed:
            self.check_current_devices()
            self.emit("power-state-changed")

    def check_current_devices(self):
        for path, dev in self.relevant_devices:
            if self.get_device_type(dev) == DeviceType.LinePower:
                self.plugged_in = self.get_device_property(dev, "Online")

    def get_battery_icon_name(self, path):
        for dev_path, dev in self.relevant_devices:
            if path == dev_path:
                return self.get_device_icon_name(dev)

        print("Battery not found")
        return None

    def get_batteries(self):
        if len(self.relevant_devices) == 0:
            return None

        ret = []

        for path, dev in self.relevant_devices:
            if self.get_device_type(dev) == DeviceType.Battery:
                ret.append((path, dev))

        return ret

    def get_device_state(self, dev):
        return self.get_device_property(dev, "State")

    def get_device_type(self, dev):
        return self.get_device_property(dev, "Type")

    def get_device_online(self, dev):
        return self.get_device_property(dev, "Online")

    def get_device_icon_name(self, dev):
        return self.get_device_property(dev, "IconName")

    def get_device_property(self, dev_proxy, prop_name):
        result = dev_proxy.get_connection().call_sync(c.UPOWER_SERVICE,
                                                      dev_proxy.get_object_path(),
                                                      c.DBUS_PROP_INTERFACE,
                                                      "Get",
                                                      GLib.Variant("(ss)",
                                                                   (c.UPOWER_DEVICE_INTERFACE, prop_name)),
                                                      None,
                                                      Gio.DBusCallFlags.NONE,
                                                      -1,
                                                      None)

        return result

    def full_and_on_ac_or_no_batteries(self):
        batteries = self.get_batteries()

        if batteries == None:
            return True

        all_batteries_full = True

        for battery in batteries:
            if self.get_device_state(battery) not in (DeviceState.FullyCharged, DeviceState.Unknown):
                all_batteries_full = False
                break

        return self.plugged_in and all_batteries_full

