#!/usr/bin/python3

from gi.repository import GLib, Gio, GObject, CScreensaver

import status

# TODO
# self.monitors, etc.. replace or at least prefer this over CsScreen, as it will be more accurate.
# Nothing currently listens to muffin-config-changed. This class is only used to initialize the event filters.

class MuffinClient(GObject.Object):
    MUFFIN_SERVICE = "org.cinnamon.Muffin.DisplayConfig"
    MUFFIN_PATH    = "/org/cinnamon/Muffin/DisplayConfig"

    __gsignals__ = {
        'muffin-config-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        GObject.Object.__init__(self)

        self.proxy = None
        self.using_fractional_scaling = False

        try:
            self.proxy = CScreensaver.MuffinDisplayConfigProxy.new_for_bus_sync(Gio.BusType.SESSION,
                                                                                Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES |
                                                                                  Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                                                                                self.MUFFIN_SERVICE,
                                                                                self.MUFFIN_PATH,
                                                                                None)
            self.proxy.connect("monitors-changed", self.on_monitors_changed)
            # cinnamon restart (monitors-changed isn't emitted at muffin startup)
            self.proxy.connect("notify::g-name-owner", self.on_name_owner_changed)
            self.update()
        except GLib.Error as e:
            print("Could not connect to Muffin's DisplayConfig service", flush=True)

    def on_monitors_changed(self, proxy):
        self.update()

    def on_name_owner_changed(self, proxy, pspec):
        if proxy.get_name_owner() is not None:
            self.update()

    def update(self):
        if self.read_current_state():
            self.emit("muffin-config-changed")

    def read_current_state(self, *args):
        old_scaling = self.using_fractional_scaling

        if self.proxy.get_name_owner() is None:
            print("Muffin not running, skipping fractinal scaling check.")
            return False

        try:
            serial, monitors, logical_monitors, properties = self.proxy.call_get_current_state_sync(None)
        except GLib.Error as e:
            print("Could not read current state from Muffin: %s" % e.message, flush=True)
            print(e, e.code)
            self.using_fractional_scaling = False
            return self.using_fractional_scaling != old_scaling

        fractional = False
        previous_scale = -1

        for monitor in logical_monitors.unpack():
            x, y, scale, transform, primary, monitors, properties = monitor

            # one or more monitors using some non-integer scale.
            if int(scale) != scale:
                fractional = True
                break

            # multiple monitors with non-identical scales
            if previous_scale > 0 and scale != previous_scale:
                fractional = True
                break

            previous_scale = scale

        self.using_fractional_scaling = fractional
        print("Fractional scaling active: %r" % self.using_fractional_scaling, flush=True)
        return self.using_fractional_scaling != old_scaling

    def get_using_fractional_scaling(self):
        return self.using_fractional_scaling
