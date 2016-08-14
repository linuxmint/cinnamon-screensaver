#! /usr/bin/python3

from gi.repository import Gtk
import dbus, dbus.service, dbus.glib
import signal

import constants as c
from manager import ScreensaverManager

signal.signal(signal.SIGINT, signal.SIG_DFL)


class ScreensaverService(dbus.service.Object):
    def __init__(self):
        sessionBus = dbus.SessionBus ()
        request = sessionBus.request_name(c.SS_SERVICE, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)

        if request == dbus.bus.REQUEST_NAME_REPLY_EXISTS:
            print("cinnamon-screensaver already running!  Exiting...")
            quit()

        bus_name = dbus.service.BusName(c.SS_SERVICE, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, c.SS_PATH)

        self.screen_manager = ScreensaverManager(self.on_manager_message)

    @dbus.service.method(c.SS_SERVICE, in_signature='s', out_signature='')
    def Lock(self, msg):
        self.screen_manager.lock(msg)

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='')
    def Quit(self):
        self.screen_manager.unlock()
        Gtk.main_quit()

    @dbus.service.method(c.SS_SERVICE, in_signature='b', out_signature='')
    def SetActive(self, active):
        self.screen_manager.set_active(active)

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='b')
    def GetActive(self):
        return self.screen_manager.get_active()

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='u')
    def GetActiveTime(self):
        return self.screen_manager.get_active_time()

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='')
    def SimulateUserActivity(self):
        if self.screen_manager.is_locked():
            self.screen_manager.simulate_user_activity()

    @dbus.service.signal(c.SS_SERVICE, signature='b')
    def ActiveChanged(self, state):
        print("Emitting ActiveChanged", state)

    def on_manager_message(self, name, data):
        if name == "ActiveChanged":
            self.ActiveChanged(data)

