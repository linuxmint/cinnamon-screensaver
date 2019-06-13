#!/usr/bin/python3

# Idle time in seconds before the unlock dialog will disappear and we go back to sleep.
UNLOCK_TIMEOUT = 30

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
