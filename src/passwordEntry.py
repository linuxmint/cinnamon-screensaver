#! /usr/bin/python3
# coding: utf-8

import gi

gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, Gdk, GObject, CinnamonDesktop, GdkPixbuf

from util import utils, trackers, settings
import status
import singletons
from baseWindow import BaseWindow
from widgets.transparentButton import TransparentButton

class PasswordEntry(Gtk.Entry):
    """
    The GtkEntry where the user types their password.  It also
    implements a clickable imagine showing the currently chosen
    keyboard layout, and allowing switching of the layout.
    """
    def __init__(self):
        super(PasswordEntry, self).__init__()
        self.get_style_context().add_class("passwordentry")

        self.set_halign(Gtk.Align.FILL)
        self.set_has_frame(True)
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        self.set_property("caps-lock-warning", False)
        self.set_placeholder_text (_("Enter password..."))
        self.set_can_default(True)

        trackers.con_tracker_get().connect(self,
                                           "icon-press",
                                           self.on_icon_pressed)

        self.keyboard_controller = singletons.KeyboardLayoutController
        self.set_lockscreen_keyboard_layout()

        trackers.con_tracker_get().connect(self,
                                           "destroy",
                                           self.on_destroy)

    def start_progress(self):
        self.set_progress_pulse_step(0.2)
        trackers.timer_tracker_get().start("auth-progress",
                                           100,
                                           self.pulse)

    def stop_progress(self):
        trackers.timer_tracker_get().cancel("auth-progress")
        self.set_progress_fraction(0.0)

    def pulse(self):
        """
        Periodic callback for the progress bar.
        """
        self.progress_pulse()
        return True

    def on_layout_changed(self, controller, layout):
        self.grab_focus_without_selecting()
        self.update_layout_icon()

    def on_icon_pressed(self, entry, icon_pos, event):
        if icon_pos == Gtk.EntryIconPosition.PRIMARY:
            self.keyboard_controller.next_group()

    def update_layout_icon(self):
        name = self.keyboard_controller.get_current_icon_name()
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, name)
        self.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, self.keyboard_controller.get_current_name())

        self.update_saved_group(self.keyboard_controller.get_current_group())

    def grab_focus(self):
        """
        Overrides the standard GtkWidget's grab_focus().
        """
        Gtk.Entry.grab_focus_without_selecting(self)

    def on_destroy(self, widget, data=None):
        self.restore_original_layout()

    def set_lockscreen_keyboard_layout(self):
        if not self.keyboard_controller.get_enabled():
            return

        # If there are multiple keyboard layouts, we want to store
        # the one the user ends up using in the unlock widget, as they'll
        # want to use the same one each time, at least until they change
        # their password.

        saved_group = settings.get_kb_group()
        self.original_group = self.keyboard_controller.get_current_group()

        new_group = 0

        if saved_group == -1:
            new_group = self.original_group
        else:
            new_group = saved_group

        self.keyboard_controller.set_current_group(new_group)
        self.update_saved_group(new_group)
        self.update_layout_icon()

        trackers.con_tracker_get().connect(self.keyboard_controller,
                                           "layout-changed",
                                           self.on_layout_changed)

    def update_saved_group(self, group):
        settings.set_kb_group(group)

    def restore_original_layout(self):
        """
        Called when the unlock dialog is destroyed, restores
        the group that was active before the screensaver was activated.
        """
        trackers.con_tracker_get().disconnect(self.keyboard_controller,
                                              "layout-changed",
                                              self.on_layout_changed)

        self.keyboard_controller.set_current_group(self.original_group)

