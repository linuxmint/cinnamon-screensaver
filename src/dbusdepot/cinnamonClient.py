#! /usr/bin/python3

from gi.repository import Gio, CScreensaver, GLib

from dbusdepot.baseClient import BaseClient

class CinnamonClient(BaseClient):
    CINNAMON_SERVICE = "org.Cinnamon"
    CINNAMON_PATH    = "/org/Cinnamon"

    def __init__(self):
        super(CinnamonClient, self).__init__(Gio.BusType.SESSION,
                                             CScreensaver.CinnamonProxy,
                                             self.CINNAMON_SERVICE,
                                             self.CINNAMON_PATH)

    def on_client_setup_complete(self):
        pass

    def exit_expo_and_overview(self):
        if self.proxy == None:
            return

        self.proxy.set_property("overview-active", False)
        self.proxy.set_property("expo-active", False)
