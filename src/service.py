#! /usr/bin/python3

from gi.repository import Gtk

import dbus, dbus.service, dbus.glib

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from manager import ScreensaverManager
from sessionProxy import SessionProxy

import trackers
import constants as c

class ScreensaverService(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName(c.SS_SERVICE, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, c.SS_PATH)

        self.screen_manager = ScreensaverManager.get()

        self.session_watcher = SessionProxy()
        trackers.con_tracker_get().connect(self.session_watcher,
                                           "idle-changed", 
                                           self.on_session_idle_changed)
        trackers.con_tracker_get().connect(self.session_watcher,
                                           "idle-notice-changed", 
                                           self.on_session_idle_notice_changed)

    @dbus.service.method(c.SS_SERVICE, in_signature='s', out_signature='')
    def Lock(self, msg):
        self.screen_manager.lock(msg)

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='')
    def Quit(self):
        self.screen_manager.unlock()
        Gtk.main_quit()

    @dbus.service.method(c.SS_SERVICE, in_signature='b', out_signature='')
    def SetActive(self, active):
        if active:
            self.screen_manager.lock()
        else:
            self.screen_manager.unlock()

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='b')
    def GetActive(self):
        return self.screen_manager.is_locked()

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='u')
    def GetActiveTime(self):
        return self.screen_manager.get_active_time()

    @dbus.service.method(c.SS_SERVICE, in_signature='', out_signature='')
    def SimulateUserActivity(self):
        if self.GetActive():
            self.screen_manager.simulate_user_activity()

    def on_session_idle_changed(self, proxy, idle):
        if idle:
            self.Lock("")
        else:
            pass

    def on_session_idle_notice_changed(self, proxy, idle):
        pass


