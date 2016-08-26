#! /usr/bin/python3

from dbusdepot.cinnamonClient import CinnamonClient as _CinnamonClient
from dbusdepot.consoleKitClient import ConsoleKitClient as _ConsoleKitClient
from dbusdepot.logindClient import LogindClient as _LogindClient
from dbusdepot.notificationClient import NotificationClient as _NotificationClient
from dbusdepot.sessionClient import SessionClient as _SessionClient
from dbusdepot.uPowerClient import UPowerClient as _UPowerClient
from dbusdepot.keybindingHandlerClient import KeybindingHandlerClient as _KeybindingHandlerClient

CinnamonClient = _CinnamonClient()
ConsoleKitClient = _ConsoleKitClient()
LogindClient = _LogindClient()
NotificationClient = _NotificationClient()
SessionClient = _SessionClient()
UPowerClient = _UPowerClient()
KeybindingHandlerClient = _KeybindingHandlerClient()