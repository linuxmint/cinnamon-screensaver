#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib
import dbus
import os

import constants as c
import trackers

class LogindConnectionError(Exception):
    pass

class LogindProxy(GObject.GObject):
    __gsignals__ = {
        'lock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'unlock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'active': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(LogindProxy, self).__init__()

        self.proxy = None

        # First, get our session path:
        try:
            pid = os.getpid()

            logind_manager_proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                                                  c.LOGIND_SERVICE, c.LOGIND_PATH, c.LOGIND_INTERFACE,
                                                                  None)

            # GetSessionByPID returns something like "/org/freedesktop/login1/session/c1" 
            self.session_id = logind_manager_proxy.GetSessionByPID("(u)", pid)
        except dbus.exceptions.DBusException:
            print("Could not acquire logind Manager proxy", e)
            raise LogindConnectionError

        # Now, make a proxy for our logind session, so we can listen to lock/unlock signals
        # and Active property changes.  Note, the Active property refers to the *session*, *not*
        # cinnamon-screensaver
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                      c.LOGIND_SERVICE, self.session_id, c.LOGIND_SESSION_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print("Could not acquire logind Session proxy", e)
            raise LogindConnectionError

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
        trackers.con_tracker_get().connect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

        trackers.con_tracker_get().connect(self.proxy,
                                           "g-properties-changed",
                                           self.on_properties_changed)

    def on_signal(self, proxy, sender, signal, params):
        if signal == "Unlock":
            self.emit("unlock")
        elif signal == "Lock":
            self.emit("lock")

    def on_properties_changed(self, proxy, changed, invalid):
        active_var = changed.lookup_value("Active", GLib.VariantType("b"))

        if active_var and active_var.get_boolean():
            self.emit("active")

