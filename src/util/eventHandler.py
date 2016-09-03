#! /usr/bin/python3

from gi.repository import Gdk

import status
from util.keybindings import KeyBindings

MOTION_THRESHOLD = 100

class EventHandler:
    def __init__(self, manager):
        self.manager = manager
        self.keybindings_handler = KeyBindings(manager)

        self.last_x = -1
        self.last_y = -1


    def on_user_activity(self):
        self.manager.simulate_user_activity()

    def on_motion_event(self, event):
        if status.Awake:
            self.on_user_activity()
            return Gdk.EVENT_STOP

        if self.last_x == -1 or self.last_y == -1:
            self.last_x = event.x
            self.last_y = event.y
            return Gdk.EVENT_STOP

        distance = max(abs(self.last_x - event.x), abs(self.last_y - event.y))

        if distance > MOTION_THRESHOLD:
            self.on_user_activity()

        return Gdk.EVENT_STOP

    def on_button_press_event(self, event):
        self.on_user_activity()

        return Gdk.EVENT_STOP

    def on_key_press_event(self, event):
        if self.keybindings_handler.maybe_handle_event(event):
            return Gdk.EVENT_STOP

        if status.Active:
            if status.Locked:
                self.manager.queue_dialog_key_event(event)

        self.on_user_activity()

        return Gdk.EVENT_STOP
