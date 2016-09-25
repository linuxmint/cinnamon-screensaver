#! /usr/bin/python3

# Idle time in seconds before the unlock dialog will disappear and we go back to sleep.
UNLOCK_TIMEOUT = 30

# Time in ms to fade the stage in and out initiated by user actions
STAGE_SPAWN_TRANSITION = 250
STAGE_DESPAWN_TRANSITION = 250

# Time in ms to fade the stage in when triggered by session idle
STAGE_IDLE_SPAWN_TRANSITION = 10 * 1000
# Time in ms to despawn the stage when it is interrupted during an
# idle fade in.
STAGE_IDLE_CANCEL_SPAWN_TRANSITION = 125

# Time in ms to wait before releasing the keyboard and mouse grabs
# after an idle-activation is canceled.
GRAB_RELEASE_TIMEOUT = 1 * 1000

# Cinnamon Screensaver
SS_SERVICE                      = "org.cinnamon.ScreenSaver"
SS_PATH                         = "/org/cinnamon/ScreenSaver"
SS_INTERFACE                    = "org.cinnamon.ScreenSaver"
