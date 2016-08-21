#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib

import constants as c
import trackers

class ConsoleKitConnectionError(Exception):
    pass

class ConsoleKitProxy(GObject.GObject):
    __gsignals__ = {
        'lock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'unlock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'active': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(ConsoleKitProxy, self).__init__()

        self.proxy = None

        # First, get our session path:
        try:
            ck_manager_proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                                                  c.CK_SERVICE, c.CK_MANAGER_PATH, c.CK_MANAGER_INTERFACE,
                                                                  None)

            # GetCurrentSession returns something like "/org/freedesktop/ConsoleKit/Session1" 
            self.session_id = ck_manager_proxy.GetCurrentSession()
        except GLib.Error as e:
            print("Could not acquire ConsoleKit Manager proxy:", e)
            raise ConsoleKitConnectionError

        # Now, make a proxy for our CK session, so we can listen to Lock/Unlock/ActiveChanged signals
        # Note, active here refers to the *session*, *not* cinnamon-screensaver
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                      c.CK_SERVICE, self.session_id, c.CK_SESSION_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except GLib.Error as e:
            print("Could not acquire ConsoleKit Session proxy:", e)
            raise ConsoleKitConnectionError

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
        trackers.con_tracker_get().connect(self.proxy,
                                           "g-signal",
                                           self.on_signal)

    def on_signal(self, proxy, sender, signal, params):
        if signal == "Unlock":
            self.emit("unlock")
        elif signal == "Lock":
            self.emit("lock")
        elif signal == "ActiveChanged":
            (active, ) = params
            if active:
                self.emit("active")
