#!/usr/bin/python3

from gi.repository import Gio, CScreensaver, GObject

from dbusdepot.baseClient import BaseClient
from util import trackers

# see cinnamon/files/usr/share/cinnamon/cinnamon-settings/bin/InputSources.py
class CurrentInputSource:
    def __init__(self, source):
        self.type, self.id, self.index,         \
            self.display_name, self.short_name, \
            self.flag_name, self.xkbid,         \
            self.xkb_layout, self.xkb_variant,  \
            self.preferences,                   \
            self.dupe_id, self.active           \
                 = source

class CinnamonClient(BaseClient):
    """
    Client to talk to Cinnamon's dbus interface.

    Used to deactivate special modal cinnamon states and deal with
    keyboard layout info.
    """
    CINNAMON_SERVICE = "org.Cinnamon"
    CINNAMON_PATH    = "/org/Cinnamon"
    __gsignals__ = {
        'current-input-source-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
        'input-sources-changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }
    def __init__(self):
        super(CinnamonClient, self).__init__(Gio.BusType.SESSION,
                                             CScreensaver.CinnamonProxy,
                                             self.CINNAMON_SERVICE,
                                             self.CINNAMON_PATH)
        self.sources = []

    def on_client_setup_complete(self):
        trackers.con_tracker_get().connect(self.proxy, "g-signal", self.on_cinnamon_signal)
        self.update_layout_sources()

    def on_cinnamon_signal(self, proxy, sender, signal, params, data=None):
        if signal == "CurrentInputSourceChanged":
            self.update_current_layout(params[0])
        elif signal == "InputSourcesChanged":
            self.update_layout_sources()

    def update_layout_sources(self):
        self.proxy.GetInputSources(result_handler=self.get_input_sources_callback,
                                   error_handler=self.get_input_sources_error)

    def get_input_sources_callback(self, proxy, sources, data=None):
        self.sources = []

        for source in sources:
            input_source = CurrentInputSource(source)
            if input_source.type == "xkb":
                self.sources.append(input_source)
        self.emit("input-sources-changed")

    def get_input_sources_error(self, proxy, error, data=None):
        print("Failed to get keyboard layouts from Cinnamon - multiple layouts will not be available: %s" % error.message)

    def has_multiple_keyboard_layouts(self):
        return len(self.sources) > 1

    def update_current_layout(self, layout):
        for source in self.sources:
            source.active = source.id == layout
        self.emit("current-input-source-changed")

    def get_current_layout_source(self):
        for source in self.sources:
            if source.active:
                return source
        return None

    def activate_next_layout(self):
        current = 0

        for i in range(0, len(self.sources)):
            source = self.sources[i]
            if source.active:
                current = i
                break

        new = current + 1
        if new > len(self.sources) - 1:
            new = 0

        self.activate_layout_index(self.sources[new].index)

    def activate_layout_index(self, index):
        """
        Activate a keyboard layout without blocking our main loop.

        Cinnamon services this call on its single JS main loop, and the work it
        does there is not cheap - an xkb reconfiguration plus an IBus
        round-trip.  When Cinnamon is busy (for instance reconfiguring monitors
        while resuming on a docking station) a synchronous call parks us for the
        full 25s default GDBus timeout.  During that time the unlock dialog is
        frozen: keystrokes are never delivered and the PAM conversation fails,
        so the user cannot log back in.  Fire and forget instead.
        """
        if not self.ensure_proxy_alive():
            return

        # NOTE: PyGI selects the async path on the *presence* of the
        # result_handler key, so it has to be a real callable - passing None
        # makes it raise TypeError from the reply handler instead.
        self.proxy.ActivateInputSourceIndex("(i)", index,
                                            result_handler=self.activate_layout_finished,
                                            error_handler=self.activate_layout_error)

    def activate_layout_finished(self, proxy, result, data=None):
        pass

    def activate_layout_error(self, proxy, error, data=None):
        print("Failed to activate keyboard layout: %s" % error.message, flush=True)

    def exit_expo_and_overview(self):
        if self.ensure_proxy_alive():
            self.proxy.set_property("overview-active", False)
            self.proxy.set_property("expo-active", False)

    def on_failure(self, *args):
        print("Failed to connect to Cinnamon - screensaver will not activate when expo or overview modes are active.", flush=True)
