#!/usr/bin/python3

from gi.repository import Gio, GLib, CScreensaver
import os
import subprocess

import status
from dbusdepot.baseClient import BaseClient
from dbusdepot.loginInterface import LoginInterface
from util.utils import DEBUG

class LogindClient(LoginInterface, BaseClient):
    """
    A client for communicating with logind.  At startup we check
    for its availability, falling back to ConsoleKit if it's not
    available.
    """
    LOGIND_SERVICE      = "org.freedesktop.login1"
    LOGIND_PATH = "/org/freedesktop/login1"

    def __init__(self):
        """
        We first try to connect to the logind manager.
        """
        super(LogindClient, self).__init__(Gio.BusType.SYSTEM,
                                           CScreensaver.LogindManagerProxy,
                                           self.LOGIND_SERVICE,
                                           self.LOGIND_PATH)

        self.pid = os.getpid()

        self.session_path = None
        self.session_proxy = None

    def on_client_setup_complete(self):
        """
        If our manager connection succeeds, we get the current session path and attempt
        to connect to its interface.
        """
        try:
            current_user = GLib.get_user_name()

            cmd = "loginctl show-user %s -pDisplay --value" % current_user
            current_session_id = subprocess.check_output(cmd, shell=True).decode().replace("\n", "")

            self.session_path = self.proxy.call_get_session_sync(current_session_id, None)
            DEBUG("login client: found session path for user '%s' (session_id: %s): %s" % (current_user, current_session_id, self.session_path))
        except GLib.Error as e:
            print("login client: could not get session path: %s" % e, flush=True)
            self.on_failure()
            return

        CScreensaver.LogindSessionProxy.new_for_bus(Gio.BusType.SYSTEM,
                                                    Gio.DBusProxyFlags.NONE,
                                                    self.LOGIND_SERVICE,
                                                    self.session_path,
                                                    None,
                                                    self.on_session_ready,
                                                    None)

    def on_session_ready(self, object, result, data=None):
        """
        Once we're connected to the session interface, we can respond to signals sent from
        it - used primarily when returning from suspend, hibernation or the login screen.
        """
        self.session_proxy = CScreensaver.LogindSessionProxy.new_for_bus_finish(result)

        self.session_proxy.connect("unlock", lambda proxy: self.emit("unlock"))
        self.session_proxy.connect("lock", lambda proxy: self.emit("lock"))
        self.session_proxy.connect("notify::active", self.on_active_changed)

        self.emit("startup-status", True)

    def on_active_changed(self, proxy, pspec, data=None):
        if self.session_proxy.get_property("active"):
            self.emit("active")

    def on_failure(self, *args):
        self.emit("startup-status", False)
