#! /usr/bin/python3

import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Gtk

import utils
from baseWindow import BaseWindow
from soundWidget import SoundWidget

class StatusBar(BaseWindow):
    def __init__(self, screen):
        super(StatusBar, self).__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        self.screen = screen
        self.monitor_index = utils.get_primary_monitor()

        self.update_geometry()

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_halign(Gtk.Align.FILL)

        self.box.get_style_context().add_class("statusbar")

        self.add(self.box)

        self.sound_widget = SoundWidget()
        self.box.pack_start(self.sound_widget, False, False, 6)

        self.show_all()
