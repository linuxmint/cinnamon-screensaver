#! /usr/bin/python3

from gi.repository import GObject

class LoginInterface(GObject.Object):
    """
    A common signal interface for our Logind and ConsoleKit clients.
    """
    __gsignals__ = {
        'startup-status': (GObject.SignalFlags.RUN_LAST, None, (bool, )),
        'lock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'unlock': (GObject.SignalFlags.RUN_LAST, None, ()),
        'active': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, *args):
        super(LoginInterface, self).__init__(*args)
