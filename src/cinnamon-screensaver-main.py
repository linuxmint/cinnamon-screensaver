#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('CScreensaver', '1.0')

from gi.repository import Gtk, Gdk, CScreensaver, Gio

import signal
import gettext
import argparse
import os
import setproctitle
import sys

import config
import status
from util import utils, settings
from service import ScreensaverService

signal.signal(signal.SIGINT, signal.SIG_DFL)
gettext.install("cinnamon-screensaver", "/usr/share/locale")

class Main(Gtk.Application):
    """
    This is the main entry point to the program, and it shows up
    in the process list.  We do any theme preparation here as well.

    We start the ScreensaverService from here.
    """
    def __init__(self):
        super(Main, self).__init__(application_id="org.cinnamon.ScreenSaver",
                                   inactivity_timeout=30000,
                                   flags=Gio.ApplicationFlags.IS_SERVICE)

        # Our service must be set up before we register with the session manager.
        ScreensaverService()

    def do_activate(self):
        pass

    def do_startup(self):
        print("Starting screensaver...", flush=True)
        Gtk.Application.do_startup(self)

        parser = argparse.ArgumentParser(description='Cinnamon Screensaver')
        parser.add_argument('--debug', dest='debug', action='store_true',
                            help='Print out some extra debugging info')
        parser.add_argument('--interactive-debug', dest='interactive', action='store_true',
                            help='If multiple monitors are in use, only cover one monitor, and launch GtkInspector')
        parser.add_argument('--disable-locking', dest='lock_disabled', action='store_true',
                            help='Disable the lock screen')
        parser.add_argument('--version', dest='version', action='store_true',
                            help='Display the current version')
        parser.add_argument('--hold', dest='hold', action='store_true',
                            help="Keep the process running." \
                                 "Normally cinnamon-screensaver will exit after being idle for 30 seconds.")
        parser.add_argument('--no-fallback', dest='no_fallback', action='store_true',
                            help="Don't spawn a fallback window when locking the screen.")
        args = parser.parse_args()

        if settings.get_custom_screensaver() != '':
            print("custom screensaver selected, exiting cinnamon-screensaver.", flush=True)
            quit()

        if args.version:
            print("cinnamon-screensaver %s" % config.VERSION)
            quit()

        status.LockEnabled = not args.lock_disabled
        status.Debug = args.debug
        status.InteractiveDebug = args.interactive
        status.UseFallback = not args.no_fallback
        # The inactivity-timeout will be ignored until there's been an initial hold. Simply
        # starting the app and letting it idle will end up with it exiting after 10s no matter
        # what the timeout.
        self.hold()

        if not args.hold:
            self.release()

        if status.Debug:
            print("Debug mode active", flush=True)

        if args.lock_disabled:
            print("Locking disabled", flush=True)

        # This is here mainly to allow the notification watcher to have a valid status.Debug value
        import singletons
        Gtk.Settings.get_default().connect("notify::gtk-theme-name", self.on_theme_changed)
        self.do_style_overrides()

    def on_theme_changed(self, settings, pspec, data=None):
        self.do_style_overrides()

    def do_style_overrides(self):
        """
        Here we try to check for theme support in the current system's gtk theme.

        We do this by retrieving a string of the current theme's final style sheet,
        then searching for the .csstage style class.  If it's found, we return, otherwise
        we add our own application-priority provider as a fallback.  While we have the
        theme string, we check for a variable name we can use for the fallback experience,
        and adjust it in our application stylesheet if necessary before adding it as a
        provider.
        """
        theme_name = Gtk.Settings.get_default().get_property("gtk-theme-name")
        provider = Gtk.CssProvider.get_named(theme_name)

        css = provider.to_string()

        if ".csstage" not in css:
            print("Cinnamon Screensaver support not found in current theme - adding some...", flush=True)

            path = os.path.join(config.pkgdatadir, "cinnamon-screensaver.css")

            f = open(path, 'r')
            fallback_css = f.read()
            f.close()

            if "@define-color theme_selected_bg_color" in css:
                pass
            elif "@define-color selected_bg_color" in css:
                print("replacing theme_selected_bg_color with selected_bg_color", flush=True)
                fallback_css = fallback_css.replace("@theme_selected_bg_color", "@selected_bg_color")
            else:
                print("replacing theme_selected_bg_color with Adwaita blue", flush=True)
                fallback_css = fallback_css.replace("@selected_bg_color", "#4a90d9")

            fallback_prov = Gtk.CssProvider()

            try:
                fallback_prov.load_from_data(fallback_css.encode())
                Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), fallback_prov, 600)
                Gtk.StyleContext.reset_widgets(Gdk.Screen.get_default())
            except Exception as e:
                print("Could not parse fallback css: %s" % str(e))

if __name__ == "__main__":
    setproctitle.setproctitle('cinnamon-screensaver')

    main = Main()
    main.run()
