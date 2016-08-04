#! /usr/bin/python3

UNLOCK_TIMEOUT = 30

OVERLAY_SPAWN_TRANSITION = 250
OVERLAY_DESPAWN_TRANSITION = 250

OVERLAY_IDLE_SPAWN_TRANSITION = 10 * 1000
OVERLAY_IDLE_CANCEL_SPAWN_TRANSITION = 125

GRAB_RELEASE_TIMEOUT = 1 * 1000

# logind
LOGIND_SERVICE                  = "org.freedesktop.login1"
LOGIND_PATH                     = "/org/freedesktop/login1"
LOGIND_INTERFACE                = "org.freedesktop.login1.Manager"

LOGIND_SESSION_INTERFACE        = "org.freedesktop.login1.Session"
LOGIND_SESSION_PATH             = "/org/freedesktop/login1/session"

# ConsoleKit
CK_SERVICE                      = "org.freedesktop.ConsoleKit"
CK_PATH                         = "/org/freedesktop/ConsoleKit"
CK_INTERFACE                    = "org.freedesktop.ConsoleKit"

CK_MANAGER_PATH                 = CK_PATH + "/Manager"
CK_MANAGER_INTERFACE            = CK_INTERFACE + ".Manager"

CK_SESSION_PATH                 = CK_PATH + "/Session"
CK_SESSION_INTERFACE            = CK_INTERFACE + ".Session"

# DBus
DBUS_SERVICE                    = "org.freedesktop.DBus"
DBUS_PATH                       = "/org/freedesktop/DBus"
DBUS_INTERFACE                  = "org.freedesktop.DBus"

# Cinnamon Screensaver
SS_SERVICE                      = "org.cinnamon.ScreenSaver"
SS_PATH                         = "/org/cinnamon/ScreenSaver"
SS_INTERFACE                    = "org.cinnamon.ScreenSaver"

# /* Gnome Session Manager */
GSM_SERVICE                     = "org.gnome.SessionManager"
GSM_PATH                        = "/org/gnome/SessionManager"
GSM_INTERFACE                   = "org.gnome.SessionManager"

GSM_PRESENCE_PATH               = GSM_PATH + "/Presence"
GSM_PRESENCE_INTERFACE          = GSM_INTERFACE + ".Presence"

CSD_MEDIAKEY_HANDLER_SERVICE    = "org.cinnamon.SettingsDaemon"
CSD_MEDIAKEY_HANDLER_PATH       = "/org/cinnamon/SettingsDaemon/KeybindingHandler"
CSD_MEDIAKEY_HANDLER_INTERFACE  = "org.cinnamon.SettingsDaemon.KeybindingHandler"
