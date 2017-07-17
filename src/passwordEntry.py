#!/usr/bin/python3
# coding: utf-8

import gi

gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import cairo

from util import trackers, settings
import singletons

class PasswordEntry(Gtk.Entry):
    """
    The GtkEntry where the user types their password.  It also
    implements a clickable imagine showing the currently chosen
    keyboard layout, and allowing switching of the layout.
    """
    def __init__(self):
        super(PasswordEntry, self).__init__()
        self.get_style_context().add_class("passwordentry")

        placeholder_text = _("Please enter your password...")
        self.set_width_chars(len(placeholder_text) + 1) # account for the flag
        self.set_has_frame(True)
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        self.set_property("caps-lock-warning", False)
        self.set_placeholder_text (placeholder_text)

        self.placeholder_text = placeholder_text
        self.current_icon_name = None
        self.current_flag_id = 0
        self.original_group = 0

        self.keyboard_controller = singletons.KeyboardLayoutController
        trackers.con_tracker_get().connect(self.keyboard_controller,
                                           "config-changed",
                                           self.on_config_changed)

        trackers.con_tracker_get().connect(self.keyboard_controller,
                                           "layout-changed",
                                           self.on_layout_changed)

        self.set_lockscreen_keyboard_layout()

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
        if not self.keyboard_controller.get_enabled():
            return False

        icon_rect = widget.get_icon_area(Gtk.EntryIconPosition.PRIMARY)
        x = icon_rect.x
        y = icon_rect.y + 2
        width = (icon_rect.width // 2) * 2
        height = icon_rect.height - 4

        handled = False

        if settings.get_show_flags():
            name = self.keyboard_controller.get_current_icon_name()

            if name:
                filename = "/usr/share/iso-flag-png/%s.png" % name

                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, -1, height)

                    render_x = (x + (width / 2) - (pixbuf.get_width() / 2))
                    render_y = (y + (height / 2) - (pixbuf.get_height() / 2))

                    Gdk.cairo_set_source_pixbuf(cr,
                                                pixbuf,
                                                render_x,
                                                render_y)

                    cr.paint()

                    self.keyboard_controller.render_cairo_subscript(cr,
                                                                    render_x + (pixbuf.get_width() / 2),
                                                                    render_y + (pixbuf.get_height() / 2),
                                                                    pixbuf.get_width() / 2,
                                                                    pixbuf.get_height() / 2,
                                                                    self.keyboard_controller.get_current_flag_id())

                    handled = True
                except GLib.Error:
                    pass

        if not handled:
            if settings.get_use_layout_variant_names():
                name = self.keyboard_controller.get_current_variant_label()
            else:
                name = self.keyboard_controller.get_current_short_group_label()

            if settings.get_show_upper_case_layout():
                name = name.upper()

            ctx = widget.get_style_context()
            ctx.save()

            ctx.set_state(Gtk.StateFlags.BACKDROP)
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

            ctx.restore()

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
        self.grab_focus()
        self.update_layout_icon()

    def on_config_changed(self, controller):
        self.set_lockscreen_keyboard_layout()

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

    def on_destroy(self, widget, data=None):
        self.stop_progress()

        trackers.con_tracker_get().disconnect(self.keyboard_controller,
                                              "config-changed",
                                              self.on_config_changed)

        trackers.con_tracker_get().disconnect(self.keyboard_controller,
                                              "layout-changed",
                                              self.on_layout_changed)

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

        trackers.con_tracker_get().connect(self,
                                           "icon-press",
                                           self.on_icon_pressed)

        trackers.con_tracker_get().connect(self,
                                           "draw",
                                           self.on_draw)

    def update_saved_group(self, group):
        settings.set_kb_group(group)

    def restore_original_layout(self):
        """
        Called when the unlock dialog is destroyed, restores
        the group that was active before the screensaver was activated.
        """
        if not self.keyboard_controller.get_enabled():
            return

        self.keyboard_controller.set_current_group(self.original_group)

    def grab_focus(self):
        Gtk.Widget.grab_focus(self)

        length = self.get_buffer().get_length()
        self.select_region(length, -1)
