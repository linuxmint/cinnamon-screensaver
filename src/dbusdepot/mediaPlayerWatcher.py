#!/usr/bin/python3

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
    """
    Represents a media player with an mpris dbus interface.

    There can be as many of these as there are players active in the session,
    but we only control the first active one in our list.

    These are instantiated by our MediaPlayerWatcher.
    """
    __gsignals__ = {
        "status-changed": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "metadata-changed": (GObject.SignalFlags.RUN_LAST, None, ())
    }
    def __init__(self, name, path):
        super(MprisClient, self).__init__(Gio.BusType.SESSION,
                                          CScreensaver.MediaPlayerProxy,
                                          name,
                                          path)

        self.metadata = None
        self.album_name = ""
        self.track_name = ""
        self.artist_name = ""
        self.albumart_url = ""

    def on_client_setup_complete(self):
        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::playback-status",
                                           self.on_playback_status_changed)

        trackers.con_tracker_get().connect(self.proxy,
                                           "notify::metadata",
                                           self.on_metadata_changed)

        self.ensure_metadata()

    def get_playback_status(self):
        status = PlaybackStatus.Unknown

        if self.ensure_proxy_alive():
            str_prop = self.proxy.get_property("playback-status")

            try:
                status = PlaybackStatus(eval("PlaybackStatus." + str_prop))
            except (ValueError, TypeError, SyntaxError):
                pass

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
            self.proxy.call_play_pause()

    def get_can_go_next(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-go-next")

        return False

    def go_next(self):
        if self.ensure_proxy_alive():
            self.proxy.call_next()

    def get_can_go_previous(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_property("can-go-previous")

        return False

    def go_previous(self):
        if self.ensure_proxy_alive():
            self.proxy.call_previous()

    def get_name(self):
        if self.ensure_proxy_alive():
            return self.proxy.get_name()

        return ""

    def get_track_name(self):
        self.ensure_metadata()

        return self.track_name

    def get_artist_name(self):
        self.ensure_metadata()

        return self.artist_name

    def get_album_name(self):
        self.ensure_metadata()

        return self.album_name

    def get_albumart_url(self):
        self.ensure_metadata()

        return self.albumart_url

    def on_failure(self, *args):
        pass

    def return_best_string(self, item):
        if type(item) == list:
            return ", ".join(item)
        elif type(item) == str:
            return item
        else:
            return ""

    def ensure_metadata(self):
        if not self.metadata:
            self.metadata = self.proxy.get_property("metadata")
            if self.metadata:
                try:
                    self.track_name = self.return_best_string(self.metadata["xesam:title"])
                except KeyError:
                    self.track_name = ""
                try:
                    self.album_name = self.return_best_string(self.metadata["xesam:album"])
                except KeyError:
                    self.album_name = ""
                try:
                    self.artist_name = self.return_best_string(self.metadata["xesam:albumArtist"])
                except KeyError:
                    try:
                        self.artist_name = self.return_best_string(self.metadata["xesam:artist"])
                    except:
                        self.artist_name = ""
                try:
                    self.albumart_url = self.return_best_string(self.metadata["mpris:artUrl"])
                except KeyError:
                    self.albumart_url = ""

    def on_playback_status_changed(self, proxy, pspec, data=None):
        self.emit("status-changed", self.get_playback_status())

    def on_metadata_changed(self, proxy, pspec, data=None):
        self.metadata = None
        self.ensure_metadata()
        self.emit("metadata-changed")

class MediaPlayerWatcher(GObject.Object):
    """
    Media player interfaces are different from our other interfaces.
    There is no common owned name, players export their own unique interface,
    within the org.mpris.MediaPlayer2.* namespace.  This allows multiple
    players to exist on the bus at one time.  It requires us to list all
    interfaces and filter out all but the ones in that namespace.  We then
    create separate Player clients for each one.
    """
    MPRIS_PATH = "/org/mpris/MediaPlayer2"

    def __init__(self):
        """
        Connect to the bus and retrieve a list of interfaces.
        """
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
        """
        NameOwnerChanged is called both when a name appears on the bus, as
        well as when it disappears.  The filled parameters tell us whether we've
        gained or lost the player.
        """
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
        """
        Create an mpris client for any discovered interfaces.
        """
        if name.startswith("org.mpris.MediaPlayer2."):
            self.player_clients.append(MprisClient(name, self.MPRIS_PATH))

    def on_name_lost(self, name):
        """
        Remove any clients that disappear off the bus.
        """
        item = None
        for client in self.player_clients:
            if client.get_name() == name:
                item = client
                break

        if item:
            self.player_clients.remove(item)

    def get_best_player(self):
        """
        Find the first player in our list that is either playing, or
        *can* be played.  Players that are simply loaded but don't have
        any playlist queued up should not pass these tests - we have only
        limited control from the lockscreen.
        """
        for client in self.player_clients:
            if client.get_playback_status() == PlaybackStatus.Playing:
                return client

            if client.get_can_play_pause() and client.get_can_control():
                return client

        return None

    def get_all_player_names(self):
        """
        Return a list of all player simple names - this is used by our
        notification code to ignore notifications sent from media players,
        which are usually unimportant, but not marked as transient (which
        would normally cause them to be ignored in the CsNotificationWatcher.)
        """
        ret = []

        for client in self.player_clients:
            fullname = client.get_name()
            split = fullname.split(".")
            ret.append(split[len(split) - 1].lower())

        return ret
