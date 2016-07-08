#! /usr/bin/python3

from gi.repository import GLib, GObject

import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import authenticator
import constants as c

class PAMHelperService(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName(c.PAM_SERVICE, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, c.PAM_PATH)

    @dbus.service.method(c.PAM_SERVICE, in_signature='ss', out_signature='bs')
    def authenticate(self, user, password):
        success, msg = authenticator.real_check_password(user, password)

        if success:
            GObject.timeout_add_seconds(10, ml.quit)

        return (success, msg)

if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)

    main = PAMHelperService()

    ml = GLib.MainLoop.new(None, True)
    ml.run()
