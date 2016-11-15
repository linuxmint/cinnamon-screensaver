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
