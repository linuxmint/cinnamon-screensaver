#! /usr/bin/python3

from gi.repository import GLib, GObject

import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import authenticator
import constants as c

class PAMHelperService(dbus.service.Object):
    def __init__(self, ml):
        self.terminate_id = 0
        self.ml = ml

        bus_name = dbus.service.BusName(c.PAM_SERVICE, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, c.PAM_PATH)

        self.queue_timeout()

    @dbus.service.method(c.PAM_SERVICE, in_signature='ss', out_signature='bs')
    def authenticate(self, user, password):
        success, msg = authenticator.real_check_password(user, password)

        self.queue_timeout()

        return (success, msg)

    def queue_timeout(self):
        if self.terminate_id > 0:
            GObject.source_remove(self.terminate_id)
            self.terminate_id = 0

        self.terminate_id = GObject.timeout_add_seconds(30, self.ml.quit)

if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)

    ml = GLib.MainLoop.new(None, True)
    main = PAMHelperService(ml)

    ml.run()
