#! /usr/bin/python3

UNLOCK_TIMEOUT = 30


# /* DBus */
DBUS_SERVICE                    = "org.freedesktop.DBus"
DBUS_PATH                       = "/org/freedesktop/DBus"
DBUS_INTERFACE                  = "org.freedesktop.DBus"

# /* Cinnamon Screensaver */
SS_SERVICE                      = "org.cinnamon.ScreenSaver"
SS_PATH                         = "/org/cinnamon/ScreenSaver"
SS_INTERFACE                    = "org.cinnamon.ScreenSaver"

# PAM Helper service
PAM_SERVICE                      = "org.cinnamon.ScreenSaver.PAMHelper"
PAM_PATH                         = "/org/cinnamon/ScreenSaver/PAMHelper"
PAM_INTERFACE                    = "org.cinnamon.ScreenSaver.PAMHelper"

# /* Gnome Session Manager */
GSM_SERVICE                     = "org.gnome.SessionManager"
GSM_PATH                        = "/org/gnome/SessionManager"
GSM_INTERFACE                   = "org.gnome.SessionManager"

GSM_PRESENCE_PATH               = GSM_PATH + "/Presence"
GSM_PRESENCE_INTERFACE          = GSM_INTERFACE + ".Presence"

CSD_MEDIAKEY_HANDLER_SERVICE    = "org.cinnamon.SettingsDaemon"
CSD_MEDIAKEY_HANDLER_PATH       = "/org/cinnamon/SettingsDaemon/KeybindingHandler"
CSD_MEDIAKEY_HANDLER_INTERFACE  = "org.cinnamon.SettingsDaemon.KeybindingHandler"
