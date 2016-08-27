#! /usr/bin/python3

from gi.repository import Gio, GObject, CScreensaver

from dbusdepot.baseClient import BaseClient
import constants as c

class ScreenSaverClient(BaseClient):
    __gsignals__ = {
        'client-ready': (GObject.SignalFlags.RUN_LAST, None, (bool,)),
    }

    def __init__(self):
        super(ScreenSaverClient, self).__init__(Gio.BusType.SESSION,
                                            CScreensaver.ScreenSaverProxy,
                                            c.SS_SERVICE,
                                            c.SS_PATH)

    def on_client_setup_complete(self):
        self.emit("client-ready", True)

    def on_failure(self, *args):
        self.emit("client-ready", False)

