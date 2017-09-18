#!/usr/bin/python3

import gi

from util import trackers, settings
import status

# Our dbus proxies are abstracted out one level more than really necessary - we have
# clients that the screensaver initializes, that can never fail.  The actual connection
# business to the various dbus address is performed asynchronously from within each client.
# The following clients can fail to establish with their respective dbus interfaces without
# competely breaking the program (or at least that's what we're after) - it just means that
# depending on what fails, you may end up without keyboard shortcut support, or a battery
# widget, etc...
from dbusdepot.cinnamonClient import CinnamonClient as _CinnamonClient
from dbusdepot.sessionClient import SessionClient as _SessionClient
from dbusdepot.uPowerClient import UPowerClient as _UPowerClient
from dbusdepot.keybindingHandlerClient import KeybindingHandlerClient as _KeybindingHandlerClient
from dbusdepot.mediaPlayerWatcher import MediaPlayerWatcher as _MediaPlayerWatcher
from dbusdepot.accountsServiceClient import AccountsServiceClient as _AccountsServiceClient

CinnamonClient = _CinnamonClient()
SessionClient = _SessionClient()
UPowerClient = _UPowerClient()
KeybindingHandlerClient = _KeybindingHandlerClient()
MediaPlayerWatcher = _MediaPlayerWatcher()
AccountsServiceClient = _AccountsServiceClient()

# The notification watcher is a C introspected class - some of the functions it uses
# don't work well via introspection.
from gi.repository import CScreensaver

NotificationWatcher = CScreensaver.NotificationWatcher.new(status.Debug)

# We only need one instance of CinnamonDesktop.BG - have it listen to bg gsettings changes
# and we just connect to "changed" on the Backgrounds object from our user (the Stage)
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import CinnamonDesktop

Backgrounds = CinnamonDesktop.BG()
Backgrounds.load_from_preferences(settings.bg_settings)
settings.bg_settings.connect("changed", lambda s,k: Backgrounds.load_from_preferences(s))

# We use XAppKbdLayoutController as a wrapper around libgnomekbd to supply the icon theme
# with icons, as well as providing correct group names.
gi.require_version('XApp', '1.0')
from gi.repository import XApp
KeyboardLayoutController = XApp.KbdLayoutController()

# The login client is a bit different - we can have either logind or ConsoleKit.
# So, we have to do a bit more work to determine which one we're going to use.
# This doesn't really need to impact the main startup business though - whichever
# one we end up using, all we're doing is connecting to signals from one or the
# other client.  Whichever we end up with is invisible/not relevant to the rest of
# the application.
from dbusdepot.consoleKitClient import ConsoleKitClient
from dbusdepot.logindClient import LogindClient

class LoginClientResolver:
    def __init__(self, manager):

        self.manager = manager
        self.login_client = None

        self.try_logind()

    def try_logind(self):
        print("Trying to connect to logind...")

        login_client = LogindClient()
        trackers.con_tracker_get().connect(login_client,
                                           "startup-status",
                                           self.on_logind_startup_result)

    def on_logind_startup_result(self, client, success):
        trackers.con_tracker_get().disconnect(client,
                                              "startup-status",
                                              self.on_logind_startup_result)

        if success:
            print("Successfully using logind")
            self.login_client = client
            self.setup_manager_connections()
        else:
            print("Failed to connect to logind, or it doesn't exist.")
            self.try_console_kit()

    def try_console_kit(self):
        print("Trying to connect to ConsoleKit...")

        login_client = ConsoleKitClient()
        trackers.con_tracker_get().connect(login_client,
                                           "startup-status",
                                           self.on_consolekit_startup_result)

    def on_consolekit_startup_result(self, client, success):
        trackers.con_tracker_get().disconnect(client,
                                              "startup-status",
                                              self.on_consolekit_startup_result)

        if success:
            print("Successfully using ConsoleKit")
            self.login_client = client
            self.setup_manager_connections()
        else:
            print("Failed to connect to ConsoleKit, or it doesn't exist.\n")

            print("Unable to connect to either logind or ConsoleKit.  Certain things will not work,")
            print("such as automatic unlocking when switching users from the desktop manager,")
            print("or locking in appropriate power/system-management events.")

    def setup_manager_connections(self):
        trackers.con_tracker_get().connect(self.login_client,
                                           "lock",
                                           self.on_session_manager_lock)
        trackers.con_tracker_get().connect(self.login_client,
                                           "unlock",
                                           self.on_session_manager_unlock)
        trackers.con_tracker_get().connect(self.login_client,
                                           "active",
                                           self.on_session_manager_active)

    def on_session_manager_lock(self, client):
        if status.Debug:
            print("Received Lock from session manager")

        self.manager.lock()

    def on_session_manager_unlock(self, client):
        if status.Debug:
            print("Received Unlock from session manager")

        self.manager.unlock()

    def on_session_manager_active(self, client):
        if status.Debug:
            print("Received Active changed from session manager")

        self.manager.update_stage()
        self.manager.simulate_user_activity()
