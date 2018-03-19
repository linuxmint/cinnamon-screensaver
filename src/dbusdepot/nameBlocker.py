#!/usr/bin/python3

from gi.repository import Gio, GObject, GLib

import status

class NameBlocker(GObject.GObject):
    """
    Blocks names
    """
    def __init__(self):
        super(NameBlocker, self).__init__()

        self.owned_names = []

    def own(self, name):
        handle = Gio.bus_own_name(Gio.BusType.SESSION,
                                  name,
                                  Gio.BusNameOwnerFlags.REPLACE,
                                  None,
                                  self.on_acquired,
                                  self.on_lost)

        self.owned_names.append((handle, "name"))

    def release_all(self):
        for (handle, name) in self.owned_names:
            if status.Debug:
                print("Releasing dbus name: %s" % name)

            Gio.bus_unown_name(handle)

        self.owned_names = []

    def on_acquired(self, connection, name, data=None):
        if status.Debug:
            print("Acquired dbus name: %s" % name)

    def on_lost(self, connection, name, data=None):
        if status.Debug:
            print("Lost dbus name: %s" % name)

    def do_dispose(self):
        if status.Debug:
            print("nameBlocker do_dispose")

        self.release_all()

        super(NameBlocker, self).do_dispose()
