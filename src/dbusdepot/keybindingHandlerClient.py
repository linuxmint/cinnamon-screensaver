#! /usr/bin/python3

from gi.repository import Gio, CScreensaver

from dbusdepot.baseClient import BaseClient

class KeybindingHandlerClient(BaseClient):
    KEYBINDING_HANDLER_SERVICE = "org.cinnamon.SettingsDaemon"
    KEYBINDING_HANDLER_PATH     = "/org/cinnamon/SettingsDaemon/KeybindingHandler"

    def __init__(self):
        super(KeybindingHandlerClient, self).__init__(Gio.BusType.SESSION,
                                                      CScreensaver.KeybindingHandlerProxy,
                                                      self.KEYBINDING_HANDLER_SERVICE,
                                                      self.KEYBINDING_HANDLER_PATH)

    def on_client_setup_complete(self):
        pass

    def handle_keybinding(self, mk_type):
        if self.proxy:
            self.proxy.call_handle_keybinding(mk_type, None, None)

