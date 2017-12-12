#!/usr/bin/python3

import gi
gi.require_version('CDesktopEnums', '3.0')
from gi.repository import Gtk, GObject, Gdk, Gio, CinnamonDesktop
from gi.repository.CDesktopEnums import MediaKeyType as MK

import status
import singletons
from util import settings

ALLOWED_ACTIONS = [MK.MUTE,
                   MK.VOLUME_UP,
                   MK.VOLUME_UP_QUIET,
                   MK.VOLUME_DOWN,
                   MK.VOLUME_DOWN_QUIET,
                   MK.MIC_MUTE,
                   MK.EJECT,
                   MK.PLAY,
                   MK.PAUSE,
                   MK.STOP,
                   MK.PREVIOUS,
                   MK.NEXT,
                   MK.REWIND,
                   MK.FORWARD,
                   MK.REPEAT,
                   MK.RANDOM,
                   MK.TOUCHPAD,
                   MK.TOUCHPAD_ON,
                   MK.TOUCHPAD_OFF,
                   MK.SHUTDOWN,
                   MK.SUSPEND,
                   MK.HIBERNATE,
                   MK.SCREEN_BRIGHTNESS_UP,
                   MK.SCREEN_BRIGHTNESS_DOWN,
                   MK.ROTATE_VIDEO,
                   MK.KEYBOARD_BRIGHTNESS_UP,
                   MK.KEYBOARD_BRIGHTNESS_DOWN,
                   MK.KEYBOARD_BRIGHTNESS_TOGGLE]

class ShortcutAction(GObject.GObject):
    """
    A class representing a group of keybindings for a specific
    media key action.
    """
    def __init__(self, action, bindings):
        super(ShortcutAction, self).__init__()

        self.action = action
        self.bindings = bindings

        self.parsed = []

        for binding in self.bindings:
            key, codes, mods = Gtk.accelerator_parse_with_keycode(binding)

            self.parsed.append((key, codes, mods))

    def activate(self, key, keycode, mods):
        for binding in self.parsed:
            if (key == binding[0] or keycode in binding[1]) and mods == binding[2]:
                return self.action

        return -1

class KeyBindings(GObject.GObject):
    """
    Receives keystrokes from the EventHandler - it checks for media key
    activation, as well as special keys like Escape or Tab, and performs the
    appropriate actions.
    """
    def __init__(self, manager):
        super(KeyBindings, self).__init__()

        self.manager = manager

        self.client = singletons.KeybindingHandlerClient

        self.keymap = Gdk.Keymap.get_default()

        self.media_key_settings = Gio.Settings(schema_id="org.cinnamon.desktop.keybindings.media-keys")
        self.shortcut_actions = []

        self.load_bindings()

    def load_bindings(self):
        self.shortcut_actions = []

        for action_id in ALLOWED_ACTIONS:
            bindings = self.media_key_settings.get_strv(CinnamonDesktop.desktop_get_media_key_string(action_id))

            action = ShortcutAction(action_id, bindings)

            self.shortcut_actions.append(action)

    def maybe_handle_event(self, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return False

        filtered_state = Gdk.ModifierType(event.state & ~(Gdk.ModifierType.MOD2_MASK | Gdk.ModifierType.LOCK_MASK))

        if filtered_state == 0 and event.keyval == Gdk.KEY_Escape:
            if status.Awake:
                self.manager.cancel_unlock_widget()
                return True

        if event.keyval == Gdk.KEY_Menu:
            return True

        if status.Awake:
            if (event.keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab)):
                if event.keyval == Gdk.KEY_ISO_Left_Tab:
                    self.manager.propagate_tab_event(True)
                else:
                    self.manager.propagate_tab_event(False)
                return True
            elif event.keyval == Gdk.KEY_space and isinstance(self.manager.get_focused_widget(), Gtk.Button):
                self.manager.propagate_activation()
                return True

        if settings.get_allow_shortcuts():
            for entry in self.shortcut_actions:
                res = entry.activate(event.keyval, event.hardware_keycode, filtered_state)

                if res == -1:
                    continue
                else:
                    self.client.handle_keybinding(res)
                    return True

        return False
