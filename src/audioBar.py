#! /usr/bin/python3

import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Gtk

import utils
from baseWindow import BaseWindow
from volumeWidget import VolumeWidget

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

        self.volume_widget = VolumeWidget()
        self.box.pack_start(self.volume_widget, False, False, 6)

        self.show_all()