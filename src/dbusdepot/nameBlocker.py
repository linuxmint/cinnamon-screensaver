#!/usr/bin/python3

from gi.repository import Gio, GObject, GLib

import status

class NameBlocker(GObject.GObject):
    """
    Terminates other screensavers.  Ideally we'd just take ownership of their
    dbus names, but due to how DE detection works in xdg-screensaver, that script
    incorrectly assumes we're a gnome or mate session if their names are owned.
    """
    def __init__(self):
        super(NameBlocker, self).__init__()

        self.owned_names = []

        self.watch("org.gnome.ScreenSaver")
        self.watch("org.mate.ScreenSaver")

    def watch(self, name):
        handle = Gio.bus_watch_name(Gio.BusType.SESSION,
                                    name,
                                    Gio.BusNameWatcherFlags.NONE,
                                    self.on_name_appeared,
                                    self.on_name_lost)

        self.owned_names.append((handle, "name"))

    def unwatch_all(self):
        for (handle, name) in self.owned_names:
            if status.Debug:
                print("Releasing dbus name: %s" % name)

            Gio.bus_unown_name(handle)

        self.owned_names = []

    def on_name_appeared(self, connection, name, name_owner, data=None):
        if status.Debug:
            print("%s appeared on the session bus, killing it" % name)

        connection.call(name_owner,
                        "/" + name.replace(".", "/"),
                        name,
                        "Quit",
                        None,
                        None,
                        Gio.DBusCallFlags.NONE,
                        -1,
                        None)

    def on_name_lost(self, connection, name, data=None):
        if status.Debug:
            print("%s is gone from the session bus" % name)

    def do_dispose(self):
        if status.Debug:
            print("nameBlocker do_dispose")

        self.unwatch_all()

        super(NameBlocker, self).do_dispose()
