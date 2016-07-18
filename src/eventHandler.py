#! /usr/bin/python3

from gi.repository import Gdk
from keybindings import KeyBindings
import manager

class EventHandler:
    __singleton = None

    def get():
        if EventHandler.__singleton == None:
            EventHandler()
        return EventHandler.__singleton

    def __init__(self):
        EventHandler.__singleton = self

        self.manager = manager.ScreensaverManager.get()
        self.keybindings_handler = KeyBindings(self.manager)

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

        if not self.manager.unlock_raised and event.string != "":
            self.manager.unlock_dialog.queue_key_event(event)

        if self.manager.unlock_raised:
            self.on_user_activity()
            return self.manager.unlock_dialog.auth_prompt_entry.event(event)

        self.on_user_activity()

        return Gdk.EVENT_STOP
