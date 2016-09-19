#! /usr/bin/python3

from gi.repository import Gtk

from baseWindow import BaseWindow
from volumeControl import VolumeControl
from playerControl import PlayerControl
from util import utils

class AudioBar(BaseWindow):
    def __init__(self, screen):
        super(AudioBar, self).__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        self.screen = screen
        self.monitor_index = utils.get_primary_monitor()

        self.update_geometry()

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_halign(Gtk.Align.FILL)
        self.box.get_style_context().add_class("topbar")
        self.box.get_style_context().add_class("audiobar")

        self.add(self.box)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(hbox, True, True, 6)

        self.volume_widget = VolumeControl()
        hbox.pack_start(self.volume_widget, False, False, 0)

        self.player_widget = PlayerControl()
        hbox.pack_start(self.player_widget, False, False, 0)
        self.player_widget.set_no_show_all(True)

        self.player_widget.set_visible(self.player_widget.should_show())

        self.show_all()