#! /usr/bin/python3

from gi.repository import Gio, CScreensaver

from dbusdepot.baseClient import BaseClient

class KeybindingHandlerClient(BaseClient):
    """
    Connects to the media key interface of cinnamon-settings-daemon.
    This calls the keybinding handler for shortcuts received by the
    Keybindings object.
    """
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

    def on_failure(self, *args):
        print("Failed to connect to the keybinding handler - media key shortcuts will not work.")