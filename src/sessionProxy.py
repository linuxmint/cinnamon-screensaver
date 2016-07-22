#! /usr/bin/python3

from gi.repository import Gio, GObject
import dbus

import constants as c
import trackers

class SessionProxy(GObject.GObject):
    __gsignals__ = {
        'idle-changed': (GObject.SignalFlags.RUN_LAST, None, (bool, )),
    }

    def __init__(self):
        super(SessionProxy, self).__init__()

        self.proxy = None
        self.idle = False
        self.idle_notice = False

        Gio.bus_watch_name(Gio.BusType.SESSION, c.GSM_SERVICE, Gio.BusNameWatcherFlags.NONE,
                           self.on_appeared, self.on_disappeared)

    def on_appeared(self, connection, name, owner):
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.GSM_SERVICE, c.GSM_PRESENCE_PATH, c.GSM_PRESENCE_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None

    def on_disappeared(self, connection, name):
        trackers.con_tracker_get().disconnect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

        self.proxy = None

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
        trackers.con_tracker_get().connect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

    def on_signal(self, proxy, sender, signal, params):
        if signal == "StatusChanged":
            self.notify_status_changed(params[0])
    
    def notify_status_changed(self, status):
        is_idle = status == 3
        self.emit("idle-changed", is_idle)
