#! /usr/bin/python3

from gi.repository import Gio, GLib, CScreensaver
import os

from dbusdepot.baseClient import BaseClient
from dbusdepot.loginInterface import LoginInterface

class LogindClient(LoginInterface, BaseClient):
    LOGIND_SERVICE      = "org.freedesktop.login1"
    LOGIND_PATH = "/org/freedesktop/login1"

    def __init__(self):
        super(LogindClient, self).__init__(Gio.BusType.SYSTEM,
                                           CScreensaver.LogindManagerProxy,
                                           self.LOGIND_SERVICE,
                                           self.LOGIND_PATH)

        self.pid = os.getpid()

        self.session_id = None
        self.session_proxy = None

    def on_client_setup_complete(self):
        try:
            self.session_id = self.proxy.call_get_session_by_pid_sync(self.pid)
        except GLib.Error:
            print("Not running under the session scope, trying XDG_SESSION_ID")
            id_suffix = os.getenv("XDG_SESSION_ID", "")
            if id_suffix != "":
                self.session_id = "/org/freedesktop/login1/session/%s" % (id_suffix,)
                print("found session: %s" % (id_suffix,))

        try:
            self.session_proxy = CScreensaver.LogindSessionProxy.new_for_bus(Gio.BusType.SYSTEM,
                                                                             Gio.DBusProxyFlags.NONE,
                                                                             self.LOGIND_SERVICE,
                                                                             self.session_id,
                                                                             None,
                                                                             self.on_session_ready,
                                                                             None)
        except GLib.Error:
            self.session_proxy = None
            self.on_failure()

    def on_session_ready(self, object, result, data=None):
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