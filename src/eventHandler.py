#! /usr/bin/python3

from gi.repository import Gdk
from keybindings import KeyBindings

import status
from status import Status

class EventHandler:
    def __init__(self, manager):
        self.manager = manager
        self.keybindings_handler = KeyBindings(manager)

    def on_user_activity(self):
        self.manager.simulate_user_activity()

    def on_motion_event(self, event):
        self.on_user_activity()

        return Gdk.EVENT_STOP

    def on_button_press_event(self, event):
        self.on_user_activity()

        return Gdk.EVENT_STOP

    def on_key_press_event(self, event):
        if self.keybindings_handler.maybe_handle_event(event):
            return Gdk.EVENT_STOP

        if status.ScreensaverStatus == Status.LOCKED_IDLE and event.string != "":
            self.manager.unlock_dialog.queue_key_event(event)
        elif status.ScreensaverStatus == Status.LOCKED_AWAKE:
            self.on_user_activity()
            return self.manager.unlock_dialog.auth_prompt_entry.event(event)

        self.on_user_activity()
        return Gdk.EVENT_STOP
