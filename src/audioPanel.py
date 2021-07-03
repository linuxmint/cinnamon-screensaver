#!/usr/bin/python3

from gi.repository import Gtk

from baseWindow import BaseWindow
from volumeControl import VolumeControl
from playerControl import PlayerControl
from util import utils, settings, trackers
import status

class AudioPanel(BaseWindow):
    def __init__(self):
        """
        Upper left panel - only shows when Awake.  Will always show the
        volume slider, and will only show the player controls if there is
        a controllable mpris player available.
        """
        super(AudioPanel, self).__init__()

        self.monitor_index = status.screen.get_primary_monitor()

        self.update_geometry()

        if not settings.get_allow_media_control():
            self.disabled = True
            return

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_halign(Gtk.Align.FILL)
        self.box.get_style_context().add_class("toppanel")
        self.box.get_style_context().add_class("audiopanel")

        self.add(self.box)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(hbox, True, True, 6)

        self.volume_widget = VolumeControl()
        hbox.pack_start(self.volume_widget, False, False, 0)

        self.player_widget = PlayerControl()
        hbox.pack_start(self.player_widget, False, False, 0)

        should_show = self.player_widget.should_show()

        trackers.con_tracker_get().connect(self.player_widget.watcher,
                                           "players-changed",
                                           self.update_visibility)

    def update_visibility(self, watcher):
        self.disabled = not self.player_widget.should_show()

    def show_panel(self):
        if not self.disabled:
            self.show_all()