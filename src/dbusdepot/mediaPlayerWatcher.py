#! /usr/bin/python3

from gi.repository import Gio, GLib, CScreensaver, GObject
from enum import IntEnum

from dbusdepot.baseClient import BaseClient
from util import trackers

class PlaybackStatus(IntEnum):
    Unknown = 0
    Playing = 1
    Paused = 2
    Stopped = 3

class MprisClient(BaseClient):
    __gsignals__ = {
        "position-changed": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "status-changed": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "metadata-changed": (GObject.SignalFlags.RUN_LAST, None, ())
    }
    def __init__(self, name, path):
        super(MprisClient, self).__init__(Gio.BusType.SESSION,
                                          CScreensaver.MediaPlayerProxy,
                                          name,
                                          path)

        self.metadata = None
        self.rate = 0
        self.max_position = 0
        self.album_name = ""
        self.track_name = ""
        self.artist_name = ""

    def on_client_setup_complete(self):
        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::playback-status",
                                           self.on_playback_status_changed)

        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::metadata",
                                           self.on_metadata_changed)

        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::rate",
                                           self.on_rate_changed)

        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::position",
                                           self.on_position_changed)

        self.rate = self.proxy.get_property("rate")

        self.ensure_metadata()

    def ensure_proxy_alive(self):
        return self.proxy and self.proxy.get_name_owner() != None

    def get_playback_status(self):
        status = PlaybackStatus.Unknown

        if self.ensure_proxy_alive():
            str_prop = self.proxy.get_property("playback-status")

            try:
                status = PlaybackStatus(eval("PlaybackStatus." + str_prop))
            except ValueError as e:
                print(e)

        return status

    def get_can_play_pause(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-play") or self.proxy.get_property("can-pause")

        return False

    def get_can_control(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-control")

        return False

    def play_pause(self):
        if self.ensure_proxy_alive():
            self.proxy.call_play_pause_sync()

    def get_can_go_next(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-go-next")

        return False

    def go_next(self):
        if self.ensure_proxy_alive():
            self.proxy.call_next_sync()

    def get_can_go_previous(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-go-previous")

        return False

    def go_previous(self):
        if self.ensure_proxy_alive():
            self.proxy.call_previous_sync()

    def get_name(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_name()

        return ""

    def get_position(self):
        if self.ensure_proxy_alive():
            # To get the position *reliably*, we must make a round-trip, because
            # the proxy's cached property may not get updated

            bus = self.proxy.get_connection()

            pos = bus.call_sync(self.proxy.get_name(),
                                self.proxy.get_object_path(),
                                "org.freedesktop.DBus.Properties",
                                "Get",
                                GLib.Variant("(ss)", (self.proxy.get_interface_name(), "Position")),
                                None,
                                Gio.DBusCallFlags.NONE,
                                -1,
                                None)

            return pos[0]

        return 0.0

    def get_max_position(self):
        self.ensure_metadata()

        return self.max_position

    def get_rate(self):
        return self.rate

    def get_track_name(self):
        self.ensure_metadata()

        return self.track_name

    def get_artist_name(self):
        self.ensure_metadata()

        return self.artist_name

    def get_album_name(self):
        self.ensure_metadata()

        return self.album_name

    def on_failure(self, *args):
        pass

    def ensure_metadata(self):
        if not self.metadata:
            self.metadata = self.proxy.get_property("metadata")
            if self.metadata:
                try:
                    self.max_position = self.metadata["mpris:length"]
                except KeyError:
                    self.max_position = 0
                try:
                    self.track_name = self.metadata["xesam:title"]
                except KeyError:
                    self.track_name = _("Unknown title")
                try:
                    self.album_name = self.metadata["xesam:album"]
                except KeyError:
                    self.album_name = ""
                try:
                    self.artist_name = self.metadata["xesam:albumArtist"][0]
                except KeyError:
                    try:
                        self.artist_name = self.metadata["xesam:artist"][0]
                    except:
                        self.artist_name = ""

    def on_playback_status_changed(self, proxy, pspec, data=None):
        self.emit("status-changed", self.get_playback_status())

    def on_position_changed(self, proxy, pspec, data=None):
        position = proxy.get_property("position")

        self.emit("position-changed", position)

    def on_rate_changed(self, proxy, pspec, data=None):
        self.rate = proxy.get_property("rate")

    def on_metadata_changed(self, proxy, pspec, data=None):
        self.metadata = None
        self.ensure_metadata()
        self.emit("metadata-changed")

class MediaPlayerWatcher(GObject.Object):
    MPRIS_PATH = "/org/mpris/MediaPlayer2"

    def __init__(self):
        super(MediaPlayerWatcher, self).__init__()

        self.player_clients = []

        try:
            self.dbus_proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION,
                                                             Gio.DBusProxyFlags.NONE,
                                                             None,
                                                             "org.freedesktop.DBus",
                                                             "/org/freedesktop/DBus",
                                                             "org.freedesktop.DBus",
                                                             None)

            trackers.con_tracker_get().connect(self.dbus_proxy,
                                               "g-signal",
                                               self.on_dbus_proxy_signal)

            self.find_initial_players()
        except GLib.Error:
            self.dbus_proxy = None
            print("Cannot acquire session org.freedesktop.DBus client to watch for media players")

    def on_dbus_proxy_signal(self, proxy, sender, signal, parameters, data=None):
        if signal == "NameOwnerChanged":
            if parameters[2] != "":
                self.on_name_acquired(parameters[0])
            else:
                self.on_name_lost(parameters[0])

    def find_initial_players(self):
        self.dbus_proxy.call("ListNames",
                             None,
                             Gio.DBusCallFlags.NONE,
                             -1,
                             None,
                             self.on_names_listed)

    def on_names_listed(self, bus, result, data=None):
        names = bus.call_finish(result)[0]

        for name in names:
            self.on_name_acquired(name)

    def on_name_acquired(self, name):
        if name.startswith("org.mpris.MediaPlayer2."):
            self.player_clients.append(MprisClient(name, self.MPRIS_PATH))

    def on_name_lost(self, name):
        item = None
        for client in self.player_clients:
            if client.get_name() == name:
                item = client
                break

        if item:
            self.player_clients.remove(item)

    def get_best_player(self):
        for client in self.player_clients:
            if client.get_playback_status() == PlaybackStatus.Playing:
                return client

            if client.get_can_play_pause() and client.get_can_control():
                return client

        return None

    def get_all_player_names(self):
        ret = []

        for client in self.player_clients:
            fullname = client.get_name()
            split = fullname.split(".")
            ret.append(split[len(split) - 1].lower())

        return ret