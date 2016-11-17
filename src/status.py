#! /usr/bin/python3

# Our global state vars
Active = False    # Screensaver visible or not - False when it's completely idle.
Locked = False    # Independent of Active, whether the unlock dialog will show when we become Awake.
Awake = False     # Whether the unlock dialog is visible or not.

# A list of focusable widgets that the user can tab between in the unlock screen.  See FocusNavigator.
focusWidgets = []

# This helps the Stage decide whether to show the clock widget or not while not Awake.
# You get all sorts of artifacts trying to draw widgets over the x plugins
PluginRunning = False

# Set at startup, assisted by cs_init_utils_initialize_locking()
# This is different than the preference that turns off locking - that only prevents idle locking.  The
# user can still lock explicitly.  The function checks for the existence of correct PAM files,
# as well as adjusting the UID if this process is started as root.
LockEnabled = True
