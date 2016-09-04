#! /usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from dbus.exceptions import DBusException
import signal
import gettext
import argparse
import os

import config
try:
   from service import ScreensaverService
except (ImportError, ValueError):
   print("The screensaver service is not available.")

signal.signal(signal.SIGINT, signal.SIG_DFL)
gettext.install("cinnamon-screensaver", "/usr/share/locale")

class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Cinnamon Screensaver')
        parser.add_argument('--version', dest='version', action='store_true',
                            help='Display the current version')
        parser.add_argument('--no-daemon', dest='no_daemon', action='store_true',
                            help="Deprecated: left for compatibility only - we never become a daemon")
        args = parser.parse_args()

        if args.version:
            print("cinnamon-screensaver %s" % (config.VERSION))
            quit()
        try:
            ScreensaverService()
            self.init_style_overrides()
            Gtk.main()
        except (NameError, DBusException) as e:
            print(e)

    def init_style_overrides(self):
        path = os.path.join(config.pkgdatadir, "application.css")
        prov = Gtk.CssProvider()

        if prov.load_from_path(path):
            Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), prov, 600)

if __name__ == "__main__":
    main = Main()



