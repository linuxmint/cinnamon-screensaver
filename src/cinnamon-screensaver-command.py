#! /usr/bin/python3

from gi.repository import Gio, GLib
import dbus
import signal
import argparse
import gettext
from enum import IntEnum

import constants as c
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

    def __init__(self, mainloop):
        self.proxy = None
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

        Gio.bus_watch_name(Gio.BusType.SESSION, c.SS_SERVICE, Gio.BusNameWatcherFlags.NONE,
                           self.on_appeared, self.on_disappeared)

    def on_appeared(self, connection, name, owner):
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.SS_SERVICE, c.SS_PATH, c.SS_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None
            print("Can't connect to screensaver!")
            self.mainloop.quit()

    def on_disappeared(self, connection, name):
        self.proxy = None
        print("Can't connect to screensaver!")
        self.mainloop.quit()

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)

        self.perform_action()

    def perform_action(self):
        if self.action_id == Action.EXIT:
            self.proxy.Quit()
        elif self.action_id == Action.QUERY:
            if self.proxy.GetActive():
                print(_("The screensaver is active\n"))
            else:
                print(_("The screensaver is inactive\n"))
        elif self.action_id == Action.TIME:
            time = self.proxy.GetActiveTime()
            if time == 0:
                print(_("The screensaver is not currently active.\n"))
            else:
                print(gettext.ngettext ("The screensaver has been active for %d second.\n", "The screensaver has been active for %d seconds.\n", time) % time)
        elif self.action_id == Action.LOCK:
            self.proxy.Lock("(s)", self.message)
        elif self.action_id == Action.ACTIVATE:
            self.proxy.SetActive("(b)", True)
        elif self.action_id == Action.DEACTIVATE:
            self.proxy.SetActive("(b)", False)

        self.mainloop.quit()

if __name__ == "__main__":

    ml = GLib.MainLoop.new(None, True)
    main = ScreensaverCommand(ml)

    ml.run()
