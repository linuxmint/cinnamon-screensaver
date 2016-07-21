#! /usr/bin/python3

from gi.repository import Gtk, GLib
from baseWindow import BaseWindow

class PluginWindow(BaseWindow):
    def __init__(self, screen, index, path):
        super(PluginWindow, self).__init__()

        self.path = path

        self.screen = screen
        self.monitor_index = index

        self.update_geometry()

        self.socket = Gtk.Socket()
        self.socket.show()

        self.socket.set_halign(Gtk.Align.FILL)
        self.socket.set_valign(Gtk.Align.FILL)

        self.add(self.socket)

        self.show_all()

        self.spawn_plugin()

    def spawn_plugin(self):
        GLib.spawn_command_line_async(self.path)

    def set_plug_id(self, plug_id):
        self.socket.add_id(plug_id)

    def has_plug(self):
        return self.socket.get_plug_window() != None
