#! /usr/bin/python3

UNLOCK_TIMEOUT = 30

STAGE_SPAWN_TRANSITION = 250
STAGE_DESPAWN_TRANSITION = 250

STAGE_IDLE_SPAWN_TRANSITION = 10 * 1000
STAGE_IDLE_CANCEL_SPAWN_TRANSITION = 125

GRAB_RELEASE_TIMEOUT = 1 * 1000

# Cinnamon Screensaver
SS_SERVICE                      = "org.cinnamon.ScreenSaver"
SS_PATH                         = "/org/cinnamon/ScreenSaver"
SS_INTERFACE                    = "org.cinnamon.ScreenSaver"
