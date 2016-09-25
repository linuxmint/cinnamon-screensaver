#! /usr/bin/python3

from gi.repository import Gio, GLib, CScreensaver

from dbusdepot.baseClient import BaseClient
from dbusdepot.loginInterface import LoginInterface


class ConsoleKitClient(LoginInterface, BaseClient):
    """
    Client for communicating with ConsoleKit - this is a backup
    to logind, if it's not available.
    """
    CK_SERVICE      = "org.freedesktop.ConsoleKit"
    CK_MANAGER_PATH = "/org/freedesktop/ConsoleKit/Manager"

    def __init__(self):
        """
        We first try to connect to the ConsoleKit manager.
        """
        super(ConsoleKitClient, self).__init__(Gio.BusType.SYSTEM,
                                               CScreensaver.ConsoleKitManagerProxy,
                                               self.CK_SERVICE,
                                               self.CK_MANAGER_PATH)

        self.session_proxy = None
        self.session_id = None

    def on_client_setup_complete(self):
        """
        If our manager connection succeeds, we ask it for the current session id and
        then attempt to connect to its session interface.
        """
        self.session_id = self.proxy.call_get_current_session_sync()

        try:
            self.session_proxy = CScreensaver.ConsoleKitSessionProxy.new_for_bus(Gio.BusType.SYSTEM,
                                                                                 Gio.DBusProxyFlags.NONE,
                                                                                 self.CK_SERVICE,
                                                                                 self.session_id,
                                                                                 None,
                                                                                 self.on_session_ready,
                                                                                 None)
        except GLib.Error:
            self.session_proxy = None
            self.on_failure()

    def on_session_ready(self, object, result, data=None):
        """
        Once we're connected to the session interface, we can respond to signals sent from
        it - used primarily when returning from suspend, hibernation or the login screen.
        """
        self.session_proxy = CScreensaver.ConsoleKitSessionProxy.new_for_bus_finish(result)

        self.session_proxy.connect("unlock", lambda proxy: self.emit("unlock"))
        self.session_proxy.connect("lock", lambda proxy: self.emit("lock"))
        self.session_proxy.connect("active-changed", self.on_active_changed)

        self.emit("startup-status", True)

    def on_active_changed(self, proxy, active, data=None):
        if active:
            self.emit("active")

    def on_failure(self, *args):
        self.emit("startup-status", False)