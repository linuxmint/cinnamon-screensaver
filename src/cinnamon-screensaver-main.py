#! /usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import dbus
from dbus.mainloop.glib import DBusGMainLoop

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import gettext
import os
import sys
import argparse

import config
from service import ScreensaverService

gettext.install("cinnamon-screensaver", "/usr/share/locale")

class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Cinnamon Screensaver')
        parser.add_argument('--version', dest='version', action='store_true',
                            help='Display the current version')
        parser.add_argument('--no-daemon', dest='no_daemon', action='store_true',
                            help="Don't become a daemon")
        args = parser.parse_args()

        if args.version:
            print("cinnamon-screensaver %s" % (config.VERSION))
            quit()

        if args.no_daemon:
            print("FIX ME no daemon")
            quit()

        service = ScreensaverService()
        Gtk.main()


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)

    main = Main()



