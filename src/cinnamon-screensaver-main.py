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

        Gtk.icon_size_register("audio-button", 20, 20)

        Gtk.Settings.get_default().connect("notify::gtk-theme-name", self.on_theme_changed)
        self.do_style_overrides()

        ScreensaverService()
        Gtk.main()

    def on_theme_changed(self, settings, pspec, data=None):
        self.do_style_overrides()

    def do_style_overrides(self):
        theme_name = Gtk.Settings.get_default().get_property("gtk-theme-name")
        provider = Gtk.CssProvider.get_named(theme_name)

        css = provider.to_string()

        if ".csstage" not in css:
            print("Cinnamon Screensaver support not found in current theme - adding some...")

            if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
                path = os.path.join(config.pkgdatadir, "cinnamon-screensaver-gtk3.20.css")
            else:
                path = os.path.join(config.pkgdatadir, "cinnamon-screensaver-gtk3.18.css")

            f = open(path, 'r')
            fallback_css = f.read()
            f.close()

            if "@define-color theme_selected_bg_color" in css:
                pass
            elif "@define-color selected_bg_color" in css:
                print("replacing theme_selected_bg_color with selected_bg_color")
                fallback_css = fallback_css.replace("@theme_selected_bg_color", "@selected_bg_color")
            else:
                print("replacing theme_selected_bg_color with Adwaita blue")
                fallback_css = fallback_css.replace("@selected_bg_color", "#4a90d9")

            fallback_prov = Gtk.CssProvider()

            if fallback_prov.load_from_data(fallback_css.encode()):
                Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), fallback_prov, 600)
                Gtk.StyleContext.reset_widgets(Gdk.Screen.get_default())

if __name__ == "__main__":
    main = Main()



