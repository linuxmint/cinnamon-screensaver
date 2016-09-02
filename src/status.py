#! /usr/bin/python3

Active = False
Locked = False
Awake = False

focusChain = []

# This helps the Stage decide whether to show the clock widget or not while not Awake.
# You get all sorts of artifacts trying to draw widgets over the x plugins
PluginRunning = False
