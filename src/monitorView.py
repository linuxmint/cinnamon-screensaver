#! /usr/bin/python3

from gi.repository import Gtk, Gio, GLib, GObject
import re

import settings
import utils
import trackers
from baseWindow import BaseWindow

class WallpaperStack(Gtk.Stack):
    def __init__(self):
        super(WallpaperStack, self).__init__()

        self.set_transition_type(Gtk.StackTransitionType.NONE)
        self.set_transition_duration(1000)

        self.current = None

    def set_initial_image(self, image):
        self.current = image
        self.current.set_visible(True)

        trackers.con_tracker_get().connect_after(image,
                                                 "draw",
                                                 self.shade_wallpaper)

        self.add(self.current)
        self.set_visible_child(self.current)

        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

    def transition_to_image(self, image):
        self.queued = image
        self.queued.set_visible(True)

        trackers.con_tracker_get().connect_after(image,
                                                 "draw",
                                                 self.shade_wallpaper)

        self.add(self.queued)
        self.set_visible_child(self.queued)

        tmp = self.current
        self.current = self.queued
        self.queued = None

        # No need to disconnect the draw handler, it'll be disco'd by the con_tracker's
        # weak_ref callback.

        GObject.idle_add(tmp.destroy)

    def shade_wallpaper(self, widget, cr):
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.paint()
        return False

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

        self.wallpaper_stack = WallpaperStack()
        self.wallpaper_stack.show()
        self.wallpaper_stack.set_halign(Gtk.Align.FILL)
        self.wallpaper_stack.set_valign(Gtk.Align.FILL)

        self.stack.add_named(self.wallpaper_stack, "wallpaper")

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

    def set_initial_wallpaper_image(self, image):
        self.wallpaper_stack.set_initial_image(image)

    def set_next_wallpaper_image(self, image):
        self.wallpaper_stack.transition_to_image(image)

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
