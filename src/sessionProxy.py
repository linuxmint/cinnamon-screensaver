#! /usr/bin/python3

from gi.repository import Gio, GObject
import dbus

import constants as c
import trackers

class SessionProxy(GObject.GObject):
    __gsignals__ = {
        'idle-changed': (GObject.SignalFlags.RUN_LAST, None, (bool, )),
        'idle-notice-changed': (GObject.SignalFlags.RUN_LAST, None, (bool, ))
    }

    def __init__(self):
        super(SessionProxy, self).__init__()

        self.proxy = None
        self.alive = False
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

        self.alive = False
        self.proxy = None

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
        trackers.con_tracker_get().connect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

        self.alive = True

    def on_signal(self, proxy, sender, signal, params):
        if signal == "StatusChanged":
            self.set_status(params[0])
    
    def set_status(self, status):
        is_idle = status == 3
        if is_idle:
            self.set_session_idle_notice(True)

            trackers.timer_tracker_get().start("session-idle-countdown",
                                               10 * 1000,
                                               self.on_idle_timeout)
        else:
            trackers.timer_tracker_get().cancel("session-idle-countdown")
            self.set_session_idle(False)
            self.set_session_idle_notice(False)

    def on_idle_timeout(self):
        self.set_session_idle(True)
        self.set_session_idle_notice(False)

        trackers.timer_tracker_get().cancel("session-idle-countdown")

        return False

    def set_session_idle_notice(self, in_effect):
        if in_effect != self.idle_notice:
            self.idle_notice = in_effect
            self.emit("idle-notice-changed", self.idle_notice)

    def set_session_idle(self, is_idle):
        if is_idle != self.idle:
            self.idle = is_idle
            self.emit("idle-changed", self.idle)
