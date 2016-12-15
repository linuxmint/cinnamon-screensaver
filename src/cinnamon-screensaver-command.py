#!/usr/bin/python3

import gi
gi.require_version('CScreensaver', '1.0')

from gi.repository import GLib
import signal
import argparse
import gettext
from enum import IntEnum

from dbusdepot.screensaverClient import ScreenSaverClient
import config

signal.signal(signal.SIGINT, signal.SIG_DFL)
gettext.install("cinnamon-screensaver", "/usr/share/locale")

class Action(IntEnum):
    EXIT = 1
    QUERY = 2
    TIME = 3
    LOCK = 4
    ACTIVATE = 5
    DEACTIVATE = 6
    VERSION = 7

class ScreensaverCommand:
    """
    This is a standalone executable that provides a simple way
    of controlling the screensaver via its dbus interface.
    """
    def __init__(self, mainloop):
        self.mainloop = mainloop

        parser = argparse.ArgumentParser(description='Cinnamon Screensaver Command')
        parser.add_argument('--exit', '-e', dest="action_id", action='store_const', const=Action.EXIT,
                            help=_('Causes the screensaver to exit gracefully'))
        parser.add_argument('--query', '-q', dest="action_id", action='store_const', const=Action.QUERY,
                            help=_('Query the state of the screensaver'))
        parser.add_argument('--time', '-t', dest="action_id", action='store_const', const=Action.TIME,
                            help=_('Query the length of time the screensaver has been active'))
        parser.add_argument('--lock', '-l', dest="action_id", action='store_const', const=Action.LOCK,
                            help=_('Tells the running screensaver process to lock the screen immediately'))
        parser.add_argument('--activate', '-a', dest="action_id", action='store_const', const=Action.ACTIVATE,
                            help=_('Turn the screensaver on (blank the screen)'))
        parser.add_argument('--deactivate', '-d', dest="action_id", action='store_const', const=Action.DEACTIVATE,
                            help=_('If the screensaver is active then deactivate it (un-blank the screen)'))
        parser.add_argument('--version', '-V', dest="action_id", action='store_const', const=Action.VERSION,
                            help=_('Version of this application'))
        parser.add_argument('--away-message', '-m', dest="message", action='store', default="",
                            help=_('Message to be displayed in lock screen'))
        args = parser.parse_args()

        if not args.action_id:
            parser.print_help()
            quit()

        if args.action_id == Action.VERSION:
            print("cinnamon-screensaver %s" % (config.VERSION))
            quit()

        self.action_id = args.action_id
        self.message = args.message

        self.client = ScreenSaverClient()
        self.client.connect("client-ready", self.on_client_ready)

    def on_client_ready(self, client, success):
        if not success or client.proxy == None:
            print("Can't connect to screensaver!")
            self.mainloop.quit()
        else:
            self.perform_action()

    def perform_action(self):
        if self.action_id == Action.EXIT:
            self.client.proxy.call_quit_sync()
        elif self.action_id == Action.QUERY:
            if self.client.proxy.call_get_active_sync():
                print(_("The screensaver is active\n"))
            else:
                print(_("The screensaver is inactive\n"))
        elif self.action_id == Action.TIME:
            time = self.client.proxy.call_get_active_time_sync()
            if time == 0:
                print(_("The screensaver is not currently active.\n"))
            else:
                print(gettext.ngettext ("The screensaver has been active for %d second.\n", "The screensaver has been active for %d seconds.\n", time) % time)
        elif self.action_id == Action.LOCK:
            self.client.proxy.call_lock_sync(self.message)
        elif self.action_id == Action.ACTIVATE:
            self.client.proxy.call_set_active_sync(True)
        elif self.action_id == Action.DEACTIVATE:
            self.client.proxy.call_set_active_sync(False)

        self.mainloop.quit()

if __name__ == "__main__":

    ml = GLib.MainLoop.new(None, True)
    main = ScreensaverCommand(ml)

    ml.run()
