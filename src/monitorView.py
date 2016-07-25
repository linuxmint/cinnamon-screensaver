#! /usr/bin/python3

from gi.repository import Gtk, Gio, GLib
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
        self.stack.set_transition_duration(250)
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
            self.proc = Gio.Subprocess.new((self.path, None),
                                           Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)

            pipe = self.proc.get_stdout_pipe()
            pipe.read_bytes_async(4096, GLib.PRIORITY_DEFAULT, None, self.on_bytes_read)

        except Exception as e:
            print(e)
            return

    def on_bytes_read(self, obj, res):
        bytes_read = obj.read_bytes_finish(res)

        if bytes_read:
            output = bytes_read.get_data().decode()

            if output:
                match = re.match('^\s*WINDOW ID=(\d+)\s*$', output)
                if match:
                    self.socket.add_id(int(match.group(1)))

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
