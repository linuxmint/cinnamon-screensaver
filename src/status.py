#!/usr/bin/python3

# Our global state vars
Active = False    # Screensaver visible or not - False when it's completely idle.
Locked = False    # Independent of Active, whether the unlock dialog will show when we become Awake.
Awake = False     # Whether the unlock dialog is visible or not.

# A list of focusable widgets that the user can tab between in the unlock screen.  See FocusNavigator.
focusWidgets = []

# This is different than the preference that turns off locking - that only prevents idle locking.  The
# user can still lock explicitly.  The function checks for the existence of correct PAM files,
# as well as adjusting the UID if this process is started as root.
LockEnabled = True

# Enables extra PAM/authentication/notification debugging
# TODO: We do a *lot* of logging now, we should just use a debug() function that checks
# for debug mode internally, instead of 'if status.Debug' everywhere.
Debug = False

# Forces the Stage to only cover a single monitor and launch a GtkInspector window.
InteractiveDebug = False

# If the wallpaper aspect is 'spanned' we will only create one MonitorView and manage it slightly
# differently.  This is an easy place to keep track of that.  This is set in singletons.py.
Spanned = False

screen = None
