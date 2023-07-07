#!/usr/bin/python3

import gi
from gi.repository import GObject, CScreensaver, Gio, GLib
import os
import time

from util import utils, trackers

class AccountsServiceClient(GObject.Object):
    """
    Singleton for working with the AccountsService, which we use
    to retrieve the user's face image and their real name.
    """
    ACCOUNTS_SERVICE = "org.freedesktop.Accounts"
    ACCOUNTS_PATH    = "/org/freedesktop/Accounts"

    __gsignals__ = {
        'accounts-ready': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super(AccountsServiceClient, self).__init__()

        self.accounts = None
        self.user = None

        print("Loading AccountsService")

        CScreensaver.AccountsServiceProxy.new_for_bus(Gio.BusType.SYSTEM,
                                                      Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                                                      self.ACCOUNTS_SERVICE,
                                                      self.ACCOUNTS_PATH,
                                                      None,
                                                      self.on_accounts_connected)

    def on_accounts_connected(self, source, res):
        try:
            self.accounts = CScreensaver.AccountsServiceProxy.new_for_bus_finish(res)
        except GLib.Error as e:
            print(f"Could not connect to AccountsService: {e}", flush=True)
            return

        self.accounts.call_find_user_by_name(utils.get_user_name(), None, self.got_user_proxy)

    def got_user_proxy(self, source, res):
        try:
            proxy_path = self.accounts.call_find_user_by_name_finish(res)
        except GLib.Error as e:
            print(f"Could not get AccountsService User object path: {e}", flush=True)
            return

        CScreensaver.AccountsUserProxy.new_for_bus(Gio.BusType.SYSTEM,
                                                   Gio.DBusProxyFlags.NONE,
                                                   self.ACCOUNTS_SERVICE,
                                                   proxy_path,
                                                   None,
                                                   self.on_user_loaded)

    def on_user_loaded(self, source, res):
        try:
            self.user = CScreensaver.AccountsUserProxy.new_for_bus_finish(res)
        except GLib.Error as e:
            print(f"Could not create AccountsService.User: {e}", flush=True)

        print("AccountsService ready")
        self.emit("accounts-ready")

    def get_real_name(self):
        if self.user is not None:
            return self.user.get_property("real-name")

        return None

    def get_face_path(self):
        face = os.path.join(GLib.get_home_dir(), ".face")
        if os.path.exists(face):
            return face

        if self.user is not None:
            accounts_path = self.user.get_property("icon-file")
            if os.path.exists(accounts_path):
                    return accounts_path

        return None
