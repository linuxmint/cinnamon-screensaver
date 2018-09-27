#!/usr/bin/python3

# Idle time in seconds before the unlock dialog will disappear and we go back to sleep.
UNLOCK_TIMEOUT = 30

# Time in ms to fade the stage in and out initiated by user actions
STAGE_SPAWN_TRANSITION = 250
STAGE_DESPAWN_TRANSITION = 250

# Time in ms to fade the stage in when triggered by session idle
# Set to 0, see https://github.com/linuxmint/cinnamon-screensaver/issues/219#issuecomment-342679518
STAGE_IDLE_SPAWN_TRANSITION = 0
# Time in ms to despawn the stage when it is interrupted during an idle fade in.
# Set to 0, see https://github.com/linuxmint/cinnamon-screensaver/issues/219#issuecomment-342679518
STAGE_IDLE_CANCEL_SPAWN_TRANSITION = 0

# Time in ms to wait before releasing the keyboard and mouse grabs
# after an idle-activation is canceled.
GRAB_RELEASE_TIMEOUT = 1 * 1000

# Used by powerWidget - the level a battery must be below before the battery icon widget in the infopanel
# will show even when asleep (active but not awake.)
BATTERY_CRITICAL_PERCENT = 20

# Cinnamon Screensaver
SS_SERVICE                      = "org.cinnamon.ScreenSaver"
SS_PATH                         = "/org/cinnamon/ScreenSaver"
SS_INTERFACE                    = "org.cinnamon.ScreenSaver"
