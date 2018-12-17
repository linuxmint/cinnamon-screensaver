#!/usr/bin/python3
# coding: utf-8

import gi
gi.require_version('Caribou', '1.0')

from gi.repository import Gtk, Gdk, GObject, Caribou, Gio, GLib

import status
from util import utils, trackers, settings
from widgets.transparentButton import TransparentButton
from baseWindow import BaseWindow

LARGEST_OSK_WIDTH = 1200
LARGEST_OSK_HEIGHT = 360
DEFAULT_PADDING = 2

class ExtendedKey(Gtk.Button):
    def __init__(self, label, xkey):
        super(ExtendedKey, self).__init__(label)
        self.get_style_context().add_class("osk-button")

        self._key = xkey

        self.connect("button-press-event", lambda widget, event: self._key.press())
        self.connect("button-release-event", lambda widget, event: self._key.release())

    def update_sizes(self, width, height):
        real_width = width * self._key.props.width

        self.set_size_request(real_width, height)

class Key(Gtk.Button):
    def __init__(self, key):
        super(Key, self).__init__()

        self.get_style_context().add_class("osk-button")

        self._key = key
        self.checked = False
        self._extended_keys = key.get_extended_keys()
        self._extended_keyboard = None
        self._grabbed = False
        self._eventCaptureId = 0

        self.set_label(self._key.props.label)

        self._popup = None
        self._popover_box = None

        if self._extended_keys:
            self._key.connect("notify::show-subkeys", self._on_show_subkeys_changed)
            self._popup = Gtk.Popover(relative_to=self)
            self._popup.get_style_context().add_class("osk-popover")
            self.get_extended_keys()

        self.connect("button-press-event", self.button_press_event)
        self.connect("button-release-event", self.button_release_event)

        if self._key.props.name in ("Control_L", "Alt_L"):
            self.model_press_handler = self._key.connect("key-pressed", self._model_key_pressed)
            self.model_release_handler = self._key.connect("key-released", self._model_key_released)

    def update_sizes(self, width, height):
        # The virtual key width is a multiplier based on the default key width.
        # Keys such as the spacebar use this to become proportionally wider than
        # other keys.
        real_width = width * self._key.props.width

        self.set_size_request(real_width, height)

        if self._popover_box:
            for child in self._popover_box.get_children():
                child.update_sizes(width, height)

    def _model_key_pressed(self, key, data=None):
        print("pressed model")

    def _model_key_released(self, key, data=None):
        print("released model")

    def button_press_event(self, widget, event, data=None):
        # Pressing buttons quickly can be recognized as a double- or triple-click, ignore
        # when that happens.  Extended keys should only appear on a click-hold.

        if event.type in (Gdk.EventType._2BUTTON_PRESS, Gdk.EventType._3BUTTON_PRESS):
            return Gdk.EVENT_PROPAGATE

        self._key.press()

        return Gdk.EVENT_PROPAGATE

    def button_release_event(self, widget, event, data=None):
        self._key.release()

        return Gdk.EVENT_PROPAGATE

    def get_uni_char(self, key):
        keyval = key.props.keyval
        unichar = Gdk.keyval_to_unicode(keyval)

        if unichar:
            return chr(unichar)
        else:
            return key.props.name

    def get_extended_keys(self):
        self._popover_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=6)

        for xkey in self._extended_keys:
            label = self.get_uni_char(xkey)

            key = ExtendedKey(label, xkey)
            self._popover_box.pack_start(key, False, False, 2)

            self._popover_box.show_all()

        self._popup.add(self._popover_box)

    def _on_show_subkeys_changed(self, key, pspec, data=None):
        if self._key.props.show_subkeys:
            self._popup.popup()
        else:
            self._popup.popdown()


class OnScreenKeyboard(BaseWindow):
    """
    An on-screen keyboard that can be used to input the password in the lockscreen.  If
    accessibility doesn't have the osk enabled, we don't construct the keyboard initially,
    to save footprint.  If needed, the keyboard button can be pressed to display the keyboard
    on demand, and it gets constructed then.
    """
    def __init__(self):
        super(OnScreenKeyboard, self).__init__()

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.END)

        self.props.margin = 30

        smallest_width, smallest_height = status.screen.get_smallest_monitor_sizes()

        self.max_width = min(smallest_width, LARGEST_OSK_WIDTH) - 60
        self.max_height = min(smallest_height / 3, LARGEST_OSK_HEIGHT) - 60 
        # print(self.max_width, self.max_height)

        self._group_stack = None

        self.base_stack = Gtk.Stack()
        self.add(self.base_stack)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      halign=Gtk.Align.CENTER,
                      valign=Gtk.Align.END)

        activate_button = TransparentButton("input-keyboard-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        activate_button.connect("clicked", self.on_activate_button_clicked)

        box.pack_start(activate_button, False, False, 0)
        box.show_all()

        self.base_stack.add_named(box, "disabled")
        self.base_stack.show_all()

        if settings.get_osk_a11y_active():
            self.build_and_show_keyboard()

    def on_activate_button_clicked(self, button, data=None):
        self.build_and_show_keyboard()

    def on_caribou_button_clicked(self, button, data=None):
        self.base_stack.set_visible_child_name("disabled")

    def build_and_show_keyboard(self):
        if not self._group_stack:
            self._keyboard = Caribou.KeyboardModel(keyboard_type=settings.get_osk_type())

            self._group_stack = Gtk.Stack(visible=True)

            self._groups = {}

            self._add_keys()
            self._group_stack.show_all()

            self.base_stack.add_named(self._group_stack, "enabled")

        self.base_stack.set_visible_child_name("enabled")

    def _add_keys(self):
        groups = self._keyboard.get_groups()

        size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        for group_name in groups:
            group = self._keyboard.get_group(group_name)

            group.connect("notify::active-level", self._on_level_changed)

            layers = {}
            levels = group.get_levels()

            for level_name in levels:
                level = group.get_level(level_name)

                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                size_group.add_widget(box)

                self._load_rows(level, box)

                layers[level_name] = box

                box.show_all()
                self._group_stack.add_named(box, "%s::%s" % (group_name, level_name))

            self._groups[group_name] = layers

        self.set_active_layer()

    def _on_level_changed(self, object, pspec, data=None):
        self.set_active_layer()

    def _load_rows(self, level, box):
        rows = level.get_rows()

        row_height = self.max_height / len(rows)

        for row in rows:
            self._add_rows(row.get_columns(), box, row_height)

    def _add_rows(self, keys, box, row_height):
        num_keys = 0
        row_children = []

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        for key in keys:
            right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            children = key.get_children()

            right_box_members = []

            for child in children:
                button = Key(child)

                num_keys += child.props.width
                row_children.append(button)

                if child.props.align == "right":
                    right_box_members.append(button)
                else:
                    left_box.pack_start(button, False, False, DEFAULT_PADDING)

            if right_box_members:
                right_box_members.reverse()

                for member in right_box_members:
                    right_box.pack_end(member, False, False, DEFAULT_PADDING)

                if child.props.name == "Caribou_Prefs":
                    button.connect("clicked", self.on_caribou_button_clicked)

            if left_box.get_children():
                row.pack_start(left_box, True, True, 0)

            if right_box.get_children():
                row.pack_end(right_box, True, True, 0)

        key_width = (self.max_width / (num_keys )) - (DEFAULT_PADDING * 2)
        key_height = row_height - (DEFAULT_PADDING * 2)

        for child in row_children:
            child.update_sizes(key_width, key_height)

        box.pack_start(row, False, False, DEFAULT_PADDING)

    def set_active_layer(self):
        active_group_name = self._keyboard.props.active_group

        active_group = self._keyboard.get_group(active_group_name)
        active_level = active_group.props.active_level

        layers = self._groups[active_group_name]
        self._group_stack.set_visible_child_name("%s::%s" % (active_group_name, active_level))
