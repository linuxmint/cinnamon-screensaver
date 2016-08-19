#! /usr/bin/python3

import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Gtk, Gio, GLib, GObject, Cvc
import re
import cairo

import status
import settings
import utils
import trackers
from baseWindow import BaseWindow

class StatusBar(BaseWindow):
    def __init__(self, screen):
        super(StatusBar, self).__init__()
        # self.get_style_context().add_class("statusbar")
        self.set_name("statusbar")
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        self.screen = screen
        self.monitor_index = utils.get_primary_monitor()

        self.update_geometry()

        self.sound_widget = SoundWidget()

        self.add(self.sound_widget)

        self.show_all()

class SoundWidget(Gtk.Box):
    def __init__(self):
        super(SoundWidget, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.controller = None
        self.output = None

        self.volume_icon = Gtk.Button.new_from_icon_name(self.volume_to_icon_name(0, False),
                                                         Gtk.IconSize.LARGE_TOOLBAR)
        self.pack_start(self.volume_icon, False, False, 4)
        self.volume_icon.get_style_context().add_class("transparentbutton")


        self.initialize_sound_controller()

    def initialize_sound_controller(self):
        self.controller = Cvc.MixerControl(name="cinnamon-screensaver")
        trackers.con_tracker_get().connect(self.controller,
                                           "state-changed",
                                           self.on_state_changed)
        # self.controller.connect("output-added", self.on_device_added, "output")
        # self.controller.connect("input-added", self.on_device_added, "input")
        # self.controller.connect("output-removed", self.on_device_removed, "output")
        # self.controller.connect("input-removed", self.on_device_removed, "input")
        # self.controller.connect("active-output-update", self.on_active_output_update)
        # self.controller.connect("active-input-update", self.on_active_input_update)
        self.controller.connect("default-sink-changed", self.on_state_changed)
        # self.controller.connect("default-source-changed", self.on_default_source_changed)
        # self.controller.connect("stream-added", self.on_stream_added)
        # self.controller.connect("stream-removed", self.on_stream_removed)
        self.controller.open()
        self.on_state_changed()

    def on_state_changed(self, controller=None, state=None):
        if controller and controller != self.controller:
            old = self.controller
            self.controller = controller
            del old
        if self.controller.get_state() == Cvc.MixerControlState.READY:
            new = self.controller.get_default_sink()
            if self.output and self.output != new:
                old = self.output
                self.output = new
                del old
            else:
                self.output = new
            trackers.con_tracker_get().connect(self.output,
                                               "notify::is-muted",
                                               self.on_volume_changed)
            trackers.con_tracker_get().connect(self.output,
                                               "notify::volume",
                                               self.on_volume_changed)

            self.on_volume_changed(None, None)

    def on_volume_changed(self, output, pspec):
        vol = self.output.get_volume()
        muted = self.output.get_is_muted()
        max_vol = self.controller.get_vol_max_norm()

        normalized_volume = int(min((vol / max_vol * 100), 100))

        new_icon_name = self.volume_to_icon_name(normalized_volume, muted)

        image = self.volume_icon.get_image()
        old_icon_name, size = image.get_icon_name()

        if old_icon_name == new_icon_name:
            return

        image.set_from_icon_name(new_icon_name, Gtk.IconSize.LARGE_TOOLBAR)

    def volume_to_icon_name(self, volume, muted):
        if muted:
            return "audio-volume-muted-symbolic"
        if volume == 0:
            return "audio-volume-off"
        if volume < 33:
            return "audio-volume-low-symbolic"
        if volume < 66:
            return "audio-volume-medium-symbolic"

        return "audio-volume-high-symbolic"