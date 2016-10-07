#! /usr/bin/python3
# coding: utf-8

import gi

gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, Gdk, GObject, CinnamonDesktop, GdkPixbuf
import cairo

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

        self.current_icon_name = None
        self.current_icon_pixbuf = None

        trackers.con_tracker_get().connect(self,
                                           "icon-press",
                                           self.on_icon_pressed)

        self.keyboard_controller = singletons.KeyboardLayoutController
        self.set_lockscreen_keyboard_layout()

        trackers.con_tracker_get().connect(self,
                                           "draw",
                                           self.on_draw)

        trackers.con_tracker_get().connect(self,
                                           "destroy",
                                           self.on_destroy)

    def on_draw(self, widget, cr, data=None):
        """
        GtkEntry always makes its icons menu-sized, no matter how much actual
        space is available for the image.  So, we use a transparent icon in
        update_layout_icon(), just so GtkEntry thinks there's an icon there,
        that way it allocates space for it, and responds to clicks in the area.
        """
        icon_rect = widget.get_icon_area(Gtk.EntryIconPosition.PRIMARY)
        x = icon_rect.x
        y = icon_rect.y
        width = (icon_rect.width // 2) * 2
        height = icon_rect.height

        if settings.get_show_flags():
            name = self.keyboard_controller.get_current_icon_name()

            if name != self.current_icon_name:
                self.current_icon_name = name
                theme = Gtk.IconTheme.get_default()
                pixbuf = theme.load_icon(name, 26, Gtk.IconLookupFlags.FORCE_SIZE)
                self.current_icon_pixbuf = pixbuf

            Gdk.cairo_set_source_pixbuf(cr,
                                        self.current_icon_pixbuf,
                                        (x + (width / 2) - (self.current_icon_pixbuf.get_width() / 2)),
                                        (y + (height / 2) - (self.current_icon_pixbuf.get_height() / 2)))
            cr.paint()
        else:
            if settings.get_show_upper_case_layout():
                name = self.keyboard_controller.get_short_name().upper()
            else:
                name = self.keyboard_controller.get_short_name().lower()

            self.current_icon_name = name

            ctx = widget.get_style_context()
            font_size = ctx.get_property("font-size", Gtk.StateFlags.BACKDROP)
            family = ctx.get_property("font-family", Gtk.StateFlags.BACKDROP)
            cr.select_font_face(family[0], cairo.FONT_WEIGHT_NORMAL, cairo.FONT_SLANT_NORMAL)
            cr.set_font_size(font_size)

            (xb, yb, w, h, xa, ya) = cr.text_extents(name)

            # Drop shadow for visibility - 1px, 1px
            cr.set_source_rgba(0, 0, 0, 0.8)
            cr.move_to((x + (width / 2) - (w / 2)) + 1,
                       (y + (height / 2) + (h / 2) + 1))

            cr.show_text(name)

            # Text

            text_color = widget.get_style_context().get_color(Gtk.StateFlags.BACKDROP)

            Gdk.cairo_set_source_rgba(cr, text_color)
            cr.move_to((x + (width / 2) - (w / 2)),
                       (y + (height / 2) + (h / 2)))

            cr.show_text(name)

        return False

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
        """
        Set an empty icon here so the widget responds to clicks and allocates space for it.
        We'll do the actual flag or whatever in the 'draw' callback.  Setting the icon here
        also ensures a redraw at the correct time to update the flag image.
        """
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "screensaver-blank")
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

