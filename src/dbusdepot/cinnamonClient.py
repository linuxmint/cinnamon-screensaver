#! /usr/bin/python3

from gi.repository import Gio, CScreensaver

from dbusdepot.baseClient import BaseClient

class CinnamonClient(BaseClient):
    """
    Simple client to talk to Cinnamon's dbus interface.  Currently
    its only use is for attempting to force an exit from overview
    and expo mode (both of which do a fullscreen grab and would prevent
    the screensaver from acquiring one.)
    """
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
        if self.ensure_proxy_alive():
            self.proxy.set_property("overview-active", False)
            self.proxy.set_property("expo-active", False)

    def on_failure(self, *args):
        print("Failed to connect to Cinnamon - screensaver will not activate when expo or overview modes are active.")