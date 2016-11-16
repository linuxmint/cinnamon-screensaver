#! /usr/bin/python3

import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Gtk
import datetime

from util import trackers, utils
from dbusdepot.mediaPlayerWatcher import PlaybackStatus
from widgets.blinkingLabel import BlinkingLabel
from widgets.marqueeLabel import MarqueeLabel
from widgets.transparentButton import TransparentButton
from widgets.positionBar import PositionBar
import singletons
import status

class PlayerControl(Gtk.Box):
    """
    Provides info and controls for any active music or other media player.  It is a
    a direct child of the AudioPanel, and is only shown if there is an active mpris
    interface we can connect to.
    """
    def __init__(self):
        super(PlayerControl, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.watcher = singletons.MediaPlayerWatcher
        self.player = self.watcher.get_best_player()

        if self.player:
            self.build_layout()

    def build_layout(self):
        size = Gtk.IconSize.from_name("audio-button")

        player_status = self.player.get_playback_status()

        # Player buttons

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_homogeneous(True)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(vbox, True, True, 2)
        vbox.pack_start(button_box, True, True, 0)
        vbox.set_valign(Gtk.Align.CENTER)

        self.previous_button = TransparentButton("media-skip-backward-symbolic", size)
        self.previous_button.show()
        trackers.con_tracker_get().connect(self.previous_button,
                                           "clicked",
                                           self.on_previous_clicked)

        button_box.pack_start(self.previous_button, True, True, 2)

        self.play_pause_button = TransparentButton(self.get_play_pause_icon_name(player_status), size)
        self.play_pause_button.show()
        trackers.con_tracker_get().connect(self.play_pause_button,
                                           "clicked",
                                           self.on_play_pause_clicked)
        button_box.pack_start(self.play_pause_button, True, True, 2)

        self.next_button = TransparentButton("media-skip-forward-symbolic", size)
        self.next_button.show()
        trackers.con_tracker_get().connect(self.next_button,
                                           "clicked",
                                           self.on_next_clicked)
        button_box.pack_start(self.next_button, True, True, 2)

        self.update_buttons(player_status)

        status.focusWidgets = status.focusWidgets + [self.previous_button,
                                                     self.play_pause_button,
                                                     self.next_button]

        # Position labels and bar

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(vbox, True, True, 4)

        vbox.set_valign(Gtk.Align.CENTER)

        position_length_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(position_length_box, True, True, 2)

        self.current_pos_label = BlinkingLabel("", 400)
        self.current_pos_label.get_style_context().add_class("positionlabel")
        position_length_box.pack_start(self.current_pos_label, False, False, 2)

        self.max_pos_label = BlinkingLabel("", 400)
        self.max_pos_label.get_style_context().add_class("positionlabel")
        position_length_box.pack_end(self.max_pos_label, False, False, 2)

        self.position_bar = PositionBar()
        vbox.pack_end(self.position_bar, True, True, 2)

        # Track info

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(vbox, True, True, 6)

        vbox.set_valign(Gtk.Align.CENTER)

        self.track_name_label = MarqueeLabel("")
        self.track_name_label.get_style_context().add_class("trackname")
        vbox.pack_start(self.track_name_label, True, True, 2)

        self.album_artist_label = MarqueeLabel("")
        self.album_artist_label.get_style_context().add_class("albumartist")
        vbox.pack_end(self.album_artist_label, True, True, 2)

        self.show_all()

        trackers.con_tracker_get().connect(self.player,
                                           "position-changed",
                                           self.on_position_changed)

        trackers.con_tracker_get().connect(self.player,
                                           "status-changed",
                                           self.on_playback_status_changed)

        trackers.con_tracker_get().connect(self.player,
                                           "metadata-changed",
                                           self.on_metadata_changed)

        self.on_playback_status_changed(self.player, player_status)
        self.on_metadata_changed(self.player)

        trackers.con_tracker_get().connect(self,
                                           "destroy",
                                           self.on_widget_destroy)

        self.update_position_timer(player_status)

    def on_previous_clicked(self, button, data=None):
        self.player.go_previous()

    def on_next_clicked(self, button, data=None):
        self.player.go_next()

    def on_play_pause_clicked(self, button, data=None):
        self.player.play_pause()

    def get_play_pause_icon_name(self, status):
        if status == PlaybackStatus.Playing:
            icon_name = "media-playback-pause-symbolic"
        else:
            icon_name = "media-playback-start-symbolic"

        return icon_name

    def position_to_time_string(self, position):
        """
        We receive track position and track length values in microseconds.
        This function formats this into readable HH:MM:SS format, and handles
        any invalid values.
        """
        delta = datetime.timedelta(microseconds=position)

        duration = datetime.datetime.utcfromtimestamp(delta.total_seconds())

        if duration.hour < 0:
            return _("--:--")

        if duration.hour < 1:
            return duration.strftime(_("%M:%S"))
        else:
            return duration.strftime(_("%H:%M:%S"))

    def on_playback_status_changed(self, player, status, data=None):
        self.update_buttons(status)
        self.update_position_timer(status)
        self.update_position_display()

        self.update_position_values_appearance(status)

    def update_position_values_appearance(self, status):
        """
        When the player is paused, we blink the position/length values.
        """
        if status == PlaybackStatus.Paused:
            self.max_pos_label.set_blinking(True)
            self.current_pos_label.set_blinking(True)
        else:
            self.max_pos_label.set_blinking(False)
            self.current_pos_label.set_blinking(False)

    def on_metadata_changed(self, player):
        """
        Update max position and labels when the player metadata changes
        """
        self.max_pos_label.set_text(self.position_to_time_string(self.player.get_max_position()))
        self.update_labels()

    def update_labels(self):
        """
        Construct the track and artist-album labels as well as possible.
        """
        self.track_name_label.set_text(self.player.get_track_name())

        artist_name = self.player.get_artist_name()
        album_name = self.player.get_album_name()

        if artist_name != "" and album_name != "":
            self.album_artist_label.set_text("%s - %s" % (self.player.get_artist_name(), self.player.get_album_name()))
        elif artist_name != "":
            self.album_artist_label.set_text(artist_name)
        elif album_name != "":
            self.album_artist_label.set_text(album_name)
        else:
            self.album_artist_label.set_text("")

    def update_buttons(self, status):
        """
        Updates the player buttons based on the current state
        """
        self.play_pause_button.set_sensitive(self.player.get_can_play_pause())
        self.next_button.set_sensitive(self.player.get_can_go_next())
        self.previous_button.set_sensitive(self.player.get_can_go_previous())

        icon_name = self.get_play_pause_icon_name(status)

        size = Gtk.IconSize.from_name("audio-button")

        image = Gtk.Image.new_from_icon_name(icon_name, size)
        self.play_pause_button.set_image(image)

    def update_position_display(self):
        """
        Updates the position values and bar to reflect the current state.
        """
        if self.player.get_position() < self.player.get_max_position():
            value = self.player.get_position() / self.player.get_max_position()
        else:
            value = 1.0
        value = utils.CLAMP(value, 0.0, 1.0)
        self.position_bar.set_fraction(value)

        self.current_pos_label.set_text(self.position_to_time_string(self.player.get_position()))

        return True

    def update_position_timer(self, status):
        """
        Starts or stops the position update timer - this is based upon the provided rate
        property of the player, which is defined as the recommended update frequency for position
        data.
        """
        if status == PlaybackStatus.Playing:
            trackers.timer_tracker_get().start("position-timer", self.player.get_rate() * 1000, self.update_position_display)
        else:
            trackers.timer_tracker_get().cancel("position-timer")

    def on_position_changed(self, player, position, data=None):
        """
        Callback for an explicit position change from the player.
        """
        self.update_position_display()

    def on_widget_destroy(self, widget, data=None):
        trackers.con_tracker_get().disconnect(self.player,
                                              "position-changed",
                                              self.on_position_changed)

        trackers.con_tracker_get().disconnect(self.player,
                                              "status-changed",
                                              self.on_playback_status_changed)

        trackers.con_tracker_get().disconnect(self,
                                              "destroy",
                                              self.on_widget_destroy)

        trackers.timer_tracker_get().cancel("position-timer")

    def should_show(self):
        """
        Checked by the AudioPanel, whether or not this widget should be displayed.
        """
        return self.player != None