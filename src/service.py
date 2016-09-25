#! /usr/bin/python3

import gi
gi.require_version('CScreensaver', '1.0')

from gi.repository import Gtk, CScreensaver, Gio, GObject

import constants as c
from manager import ScreensaverManager

class ScreensaverService(GObject.Object):
    """
    This is the dbus service we run ourselves.  It is the owner
    of our ScreensaverManager, and implements the org.cinnamon.Screensaver
    dbus interface.  It is through this service that the screensaver
    is controlled.
    """
    def __init__(self):
        """
        Immediately attempt to own org.cinnamon.Screensaver.

        Failure to do so will result in simply quitting the program,
        as we can't run more than one instance at a time.

        Upon success we export our interface to the session bus.
        """
        super(ScreensaverService, self).__init__()

        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION)

        Gio.bus_own_name(Gio.BusType.SESSION,
                         c.SS_SERVICE,
                         Gio.BusNameOwnerFlags.NONE,
                         self.on_bus_acquired,
                         self.on_name_acquired,
                         self.on_name_lost)

    def on_name_lost(self, connection, name, data=None):
        """
        Failed to acquire our name - just exit.
        """
        print("A screensaver is already running!  Exiting...")
        Gtk.main_quit()

    def on_name_acquired(self, connection, name, data=None):
        """
        Acquired our name - pass... The real work will begin
        on our bus_acquired callback.
        """
        print("Starting screensaver...")

    def on_bus_acquired(self, connection, name, data=None):
        """
        Export our interface to the session bus.  Creates the
        ScreensaverManager.  We are now ready to respond to requests
        by cinnamon-session and cinnamon-screensaver-command.
        """
        self.bus = connection

        self.interface = CScreensaver.ScreenSaverSkeleton.new()

        self.interface.connect("handle-lock", self.handle_lock)
        self.interface.connect("handle-quit", self.handle_quit)
        self.interface.connect("handle-set-active", self.handle_set_active)
        self.interface.connect("handle-get-active", self.handle_get_active)
        self.interface.connect("handle-get-active-time", self.handle_get_active_time)
        self.interface.connect("handle-simulate-user-activity", self.handle_simulate_user_activity)

        self.manager = ScreensaverManager()
        self.manager.connect("active-changed", self.on_active_changed)

        self.interface.export(self.bus, c.SS_PATH)

# Interface handlers
    def handle_lock(self, iface, inv, msg):
        self.manager.lock(msg)

        iface.complete_lock(inv)

        return True

    def handle_quit(self, iface, inv):
        self.manager.unlock()

        iface.complete_quit(inv)

        Gtk.main_quit()

        return True

    def handle_set_active(self, iface, inv, active):
        self.manager.set_active(active)

        iface.complete_set_active(inv)

        return True

    def handle_get_active(self, iface, inv):
        active = self.manager.get_active()

        iface.complete_get_active(inv, active)

        return True

    def handle_get_active_time(self, iface, inv):
        atime = self.manager.get_active_time()

        iface.complete_get_active_time(inv, atime)

        return True

    def handle_simulate_user_activity(self, iface, inv):
        if self.manager.is_locked():
            self.manager.simulate_user_activity()

        iface.complete_simulate_user_activity(inv)

        return True

    def on_active_changed(self, manager, state, data=None):
        self.interface.emit_active_changed(state)
