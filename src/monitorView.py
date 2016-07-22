#! /usr/bin/python3

from gi.repository import Gtk
import subprocess
import re

import settings
import utils
import trackers
from baseWindow import BaseWindow

class MonitorView(BaseWindow):
    def __init__(self, screen, index):
        super(MonitorView, self).__init__()

        self.screen = screen
        self.monitor_index = index

        self.update_geometry()

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(500)
        self.add(self.stack)

        self.wallpaper = Gtk.Image()
        self.wallpaper.show()
        self.wallpaper.set_halign(Gtk.Align.FILL)
        self.wallpaper.set_valign(Gtk.Align.FILL)

        self.stack.add_named(self.wallpaper, "wallpaper")

        trackers.con_tracker_get().connect_after(self.wallpaper,
                                                 "draw",
                                                 self.on_wallpaper_drawn)

        name = settings.get_screensaver_name()
        path = utils.lookup_plugin_path(name)
        if path is not None:
            self.path = path
            self.socket = Gtk.Socket()
            self.socket.show()
            self.socket.set_halign(Gtk.Align.FILL)
            self.socket.set_valign(Gtk.Align.FILL)

            self.stack.add_named(self.socket, "plugin")

            trackers.con_tracker_get().connect(self.socket,
                                               "realize",
                                               self.on_socket_realized)
        else:
            self.socket = None

        self.show_all()

    def on_wallpaper_drawn(self, widget, cr):
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.paint()
        return False

    def on_socket_realized(self, widget):
        self.spawn_plugin()

    def spawn_plugin(self):
        try:
            self.proc = subprocess.Popen(self.path, stdout=subprocess.PIPE)
        except Exception as e:
            print(e)
            return

        line = self.proc.stdout.readline()

        while line:
            match = re.match('^\s*WINDOW ID=(\d+)\s*$', line.decode())
            if match:
                self.socket.add_id(int(match.group(1)))
                break
            line = self.proc.stdout.readline()

    def show_plugin(self):
        if self.socket:
            self.stack.set_visible_child_name("plugin")

    def show_wallpaper(self):
        self.stack.set_visible_child_name("wallpaper")

    def show_starting_view(self):
        if self.socket:
            self.show_plugin()
        else:
            self.show_wallpaper()
