#!/usr/bin/python3

from gi.repository import Gio, GObject, CScreensaver

from dbusdepot.baseClient import BaseClient
from util.utils import DEBUG

class SessionClient(BaseClient):
    """
    This client is for connecting to the session manager's Presence
    interface - it is responsible for triggering activation of the
    screensaver when the session goes into an idle state.
    """
    __gsignals__ = {
        'idle-changed': (GObject.SignalFlags.RUN_LAST, None, (bool, )),
    }

    GSM_SERVICE       = "org.gnome.SessionManager"
    GSM_PRESENCE_PATH = "/org/gnome/SessionManager/Presence"

    def __init__(self):
        super(SessionClient, self).__init__(Gio.BusType.SESSION,
                                            CScreensaver.SessionPresenceProxy,
                                            self.GSM_SERVICE,
                                            self.GSM_PRESENCE_PATH)

        self.idle = False

    def on_client_setup_complete(self):
        self.proxy.connect("status-changed", self.on_status_changed)

    def on_status_changed(self, proxy, status):
        new_idle = status == 3
        if new_idle != self.idle:
            DEBUG("SessionClient: status changed: %d to %d (Session manager code %d)" % (self.idle, new_idle, status))
            self.idle = new_idle
            self.emit("idle-changed", self.idle)

    def on_failure(self, *args):
        DEBUG("Failed to connect to session manager - idle detection will not work.")
