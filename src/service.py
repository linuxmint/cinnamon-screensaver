#!/usr/bin/python3

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

        """
        The stage constructs itself and fades in asynchronously, and most importantly,
        as an idle callback.  This can cause the screensaver to not be fully active when
        a call to suspend is made.  Cinnamon-session calls to lock the screensaver
        synchronously, and if we don't completely finish construction before returning
        the dbus call completion, there's a chance the idle callback won't run until
        after the computer is resumed.

        We get an active-changed signal whenever the screensaver becomes completely active
        or inactive, so we'll queue up running iface.complete_lock() until we receive that signal.

        This allows the screensaver to be fully activated prior to cinnamon-session allowing
        the suspend/hibernate/whatever process to continue.

        For reference, this is called in cinnamon-session's csm-manager.c "manager_perhaps_lock"
        method.
        """
        self.lock_queue = []

        self.interface.export(self.bus, c.SS_PATH)

# Interface handlers
    def handle_lock(self, iface, inv, msg):
        self.lock_queue.append(inv)

        self.manager.lock(msg)

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
        GObject.idle_add(self.on_active_changed_idle, state)

    def on_active_changed_idle(self, state):
        self.lock_queue.reverse()

        while len(self.lock_queue) > 0:
            invocation = self.lock_queue.pop()
            self.interface.complete_lock(invocation)

        self.lock_queue = []

        self.interface.emit_active_changed(state)
