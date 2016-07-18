#! /usr/bin/python3

import gi
gi.require_version('CDesktopEnums', '3.0')
from gi.repository import Gtk, GObject, Gdk, Gio, CinnamonDesktop
import dbus

from gi.repository.CDesktopEnums import MediaKeyType as MK

import constants as c

class ShortcutAction(GObject.GObject):
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
    def __init__(self, manager):
        super(KeyBindings, self).__init__()

        self.proxy = None
        self.keymap = Gdk.Keymap.get_default()

        Gio.bus_watch_name(Gio.BusType.SESSION, c.CSD_MEDIAKEY_HANDLER_SERVICE,
                           Gio.BusNameWatcherFlags.NONE,
                           self.on_csd_appeared, self.on_csd_disappeared)

        self.manager = manager

        self.media_key_settings = Gio.Settings(schema_id="org.cinnamon.desktop.keybindings.media-keys")
        self.shortcut_actions = []

        self.load_bindings()

    def on_csd_appeared(self, connection, name, owner):
        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.CSD_MEDIAKEY_HANDLER_SERVICE, 
                                      c.CSD_MEDIAKEY_HANDLER_PATH,
                                      c.CSD_MEDIAKEY_HANDLER_INTERFACE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None

    def on_csd_disappeared(self, connection, name):
        self.proxy = None

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)

    def load_bindings(self):
        self.shortcut_actions = []

        i = 0

        for i in range(0, MK.SEPARATOR):
            bindings = self.media_key_settings.get_strv(CinnamonDesktop.desktop_get_media_key_string(i))

            action = ShortcutAction(MK(i), bindings)

            self.shortcut_actions.append(action)

    def maybe_handle_event(self, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return False

        filtered_state = Gdk.ModifierType(event.state & ~(Gdk.ModifierType.MOD2_MASK | Gdk.ModifierType.LOCK_MASK))

        if filtered_state == 0 and event.keyval == Gdk.KEY_Escape:
            if self.manager.unlock_raised:
                self.manager.cancel_lock_widget()
                return True

        for entry in self.shortcut_actions:
            res = entry.activate(event.keyval, event.hardware_keycode, filtered_state)

            if res == -1:
                continue
            else:
                self.on_media_key_pressed(res)
                return True

        return False

    def on_media_key_pressed(self, action):
        self.proxy.HandleKeybinding('(u)', action)

