#! /usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
import signal
import gettext
import argparse
import os

import config
from service import ScreensaverService

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

        self.init_style_overrides()

        ScreensaverService()
        Gtk.main()

    def init_style_overrides(self):
        path = os.path.join(config.pkgdatadir, "application.css")
        prov = Gtk.CssProvider()

        Gtk.icon_size_register("audio-button", 20, 20)

        if prov.load_from_path(path):
            Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), prov, 600)

if __name__ == "__main__":
    main = Main()



