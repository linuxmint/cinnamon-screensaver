#! /usr/bin/python3

from gi.repository import Gdk

import status
from util.keybindings import KeyBindings

MOTION_THRESHOLD = 100

class EventHandler:
    """
    The EventHandler receives all user key, button and motion events
    for the application.  At various points it can be receiving them
    from the Stage window, an offscreen window, or the root GdkWindow.

    All events are stopped from passing beyond this point, to prevent
    any unintended events from propagating to Cinnamon or Muffin.
    """
    def __init__(self, manager):
        self.manager = manager
        self.keybindings_handler = KeyBindings(manager)

        self.last_x = -1
        self.last_y = -1


    def on_user_activity(self):
        """
        Any user event is a 'wake' event, and is propagated to the stage
        in order to reset our unlock cancellation timer.
        """
        self.manager.simulate_user_activity()

    def on_motion_event(self, event):
        """
        Any mouse movement is sent here - there is a threshold to reach when
        asleep, so that inadvertant motion doesn't wake the system unintentionally.
        """
        if status.Awake:
            self.on_user_activity()
            return Gdk.EVENT_PROPAGATE

        if self.last_x == -1 or self.last_y == -1:
            self.last_x = event.x
            self.last_y = event.y
            return Gdk.EVENT_PROPAGATE

        distance = max(abs(self.last_x - event.x), abs(self.last_y - event.y))

        if distance > MOTION_THRESHOLD:
            self.on_user_activity()

        return Gdk.EVENT_PROPAGATE

    def on_button_press_event(self, event):
        """
        Any button presses are swallowed after interacting
        with their receiving widgets (in the case of buttons, entry, etc...)
        """
        self.on_user_activity()

        return Gdk.EVENT_STOP

    def on_key_press_event(self, event):
        """
        Any key events are checked with the KeybindingHandler in case
        a media shortcut is being used, or it's a special keystroke such
        as Escape or tab.

        Any other presses are sent to the password entry or swallowed.
        """
        if self.keybindings_handler.maybe_handle_event(event):
            return Gdk.EVENT_STOP

        if status.Active:
            if status.Locked:
                self.manager.queue_dialog_key_event(event)

        self.on_user_activity()

        return Gdk.EVENT_STOP
