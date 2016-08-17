#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib
import dbus

import constants as c
import trackers

class CinnamonProxy(GObject.GObject):
    def __init__(self):
        super(CinnamonProxy, self).__init__()

        self.proxy = None

        Gio.bus_watch_name(Gio.BusType.SESSION, c.CINNAMON_SERVICE, Gio.BusNameWatcherFlags.NONE,
                           self.on_appeared, self.on_disappeared)

    def on_appeared(self, connection, name, owner):
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.CINNAMON_SERVICE, c.CINNAMON_PATH, c.DBUS_PROP_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None

    def on_disappeared(self, connection, name):
        self.proxy = None

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)

    def exit_expo_and_overview(self):
        if self.proxy == None:
            return

        self.proxy.Set("(ssv)", c.CINNAMON_INTERFACE, "OverviewActive", GLib.Variant.new_boolean(False),
                       reply_handler=None, error_handler=None)
        self.proxy.Set("(ssv)", c.CINNAMON_INTERFACE, "ExpoActive", GLib.Variant.new_boolean(False),
                       reply_handler=None, error_handler=None)
