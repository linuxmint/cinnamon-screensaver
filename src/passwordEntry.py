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
        super(PasswordEntry, self).__init__(max_length=200)
        self.get_style_context().add_class("passwordentry")

        placeholder_text = _("Please enter your password...")
        self.set_width_chars(len(placeholder_text) + 1) # account for the flag
        self.set_has_frame(True)
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        self.set_property("caps-lock-warning", False)
        self.set_placeholder_text (placeholder_text)
        self.set_can_default(True)

        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "cinnamon-screensaver-view-reveal")
        trackers.con_tracker_get().connect(self, "icon-press", self.on_icon_pressed)

        self.placeholder_text = placeholder_text
        self.lockscreen_layout_source = None
        self.system_layout_source = None

        self.cinnamon = singletons.CinnamonClient
        self.cinnamon.connect("current-input-source-changed", self.on_current_layout_changed)
        self.cinnamon.connect("input-sources-changed", self.on_layout_sources_changed)
        self.on_layout_sources_changed(self.cinnamon)

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
        y = icon_rect.y + 2
        width = (icon_rect.width // 2) * 2
        height = icon_rect.height - 4

        handled = False
        if settings.get_show_flags():
            ui_scale = self.get_scale_factor()

            if self.lockscreen_layout_source.flag_name != "":
                filename = "/usr/share/iso-flag-png/%s.png" % self.lockscreen_layout_source.flag_name
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, -1, height * ui_scale)

                    logical_width = pixbuf.get_width() / ui_scale
                    logical_height = pixbuf.get_height() / ui_scale

                    render_x = (x + (width / 2) - (logical_width / 2))
                    render_y = (y + (height / 2) - (logical_height / 2))

                    if pixbuf:
                        surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf,
                                                                       ui_scale,
                                                                       self.get_window())

                    cr.set_source_surface(surface,
                                          render_x,
                                          render_y)

                    cr.paint()

                    if self.lockscreen_layout_source.dupe_id > 0:
                        x = render_x + logical_width / 2
                        y = render_y + logical_height / 2
                        width = logical_width / 2 + 2
                        height = logical_height / 2 + 2

                        cr.set_source_rgba(0, 0, 0, 0.5)
                        cr.rectangle(x, y, width, height)
                        cr.fill()

                        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
                        cr.rectangle(x + 1, y + 1, width - 2, height - 2)
                        cr.fill()

                        cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
                        cr.select_font_face("sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
                        cr.set_font_size(height - 2.0)

                        dupe_str = str(self.lockscreen_layout_source.dupe_id)

                        ext = cr.text_extents(dupe_str)
                        cr.move_to((x + (width / 2.0) - (ext.width / 2.0)),
                                   (y + (height / 2.0) + (ext.height / 2.0)))
                        cr.show_text(dupe_str)

                    handled = True
                except GLib.Error:
                    pass

        if not handled:
            name = self.lockscreen_layout_source.short_name
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

    def on_current_layout_changed(self, cinnamon):
        if not self.cinnamon.has_multiple_keyboard_layouts():
            return

        self.lockscreen_layout_source = self.cinnamon.get_current_layout_source()

        self.grab_focus()
        self.update_layout_icon()

    def on_layout_sources_changed(self, cinnamon):
        self.system_layout_source = self.cinnamon.get_current_layout_source()
        self.lockscreen_layout_source = self.system_layout_source

        if not self.cinnamon.has_multiple_keyboard_layouts():
            return

        self.set_lockscreen_keyboard_layout()

    def on_icon_pressed(self, entry, icon_pos, event):
        if icon_pos == Gtk.EntryIconPosition.PRIMARY:
            self.cinnamon.activate_next_layout()
        elif icon_pos == Gtk.EntryIconPosition.SECONDARY:
            if self.get_input_purpose() == Gtk.InputPurpose.FREE_FORM:
                self.set_visibility(False)
                self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
                self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "cinnamon-screensaver-view-reveal")
            else:
                self.set_visibility(True)
                self.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
                self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "cinnamon-screensaver-view-conceal")
            self.queue_draw()

    def update_layout_icon(self):
        """
        Set an empty icon here so the widget responds to clicks and allocates space for it.
        We'll do the actual flag or whatever in the 'draw' callback.  Setting the icon here
        also ensures a redraw at the correct time to update the flag image.
        """
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "screensaver-blank")
        self.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, self.lockscreen_layout_source.display_name)

    def on_destroy(self, widget, data=None):
        self.stop_progress()

        self.restore_original_layout()

    def set_lockscreen_keyboard_layout(self):
        # If there are multiple keyboard layouts, we want to store
        # the one the user ends up using in the unlock widget, as they'll
        # want to use the same one each time, at least until they change
        # their password.

        saved_index = settings.get_kb_group()
        new_index = 0

        if saved_index == -1:
            new_index = self.system_layout_source.index
            settings.set_kb_group(new_index)
        else:
            new_index = saved_index

        if new_index != self.system_layout_source.index:
            self.cinnamon.activate_layout_index(new_index)

        self.update_layout_icon()

        trackers.con_tracker_get().connect_after(self,
                                                 "draw",
                                                 self.on_draw)

    def restore_original_layout(self):
        """
        Called when the unlock dialog is destroyed, restores
        the group that was active before the screensaver was activated.
        """
        if settings.get_kb_group() != self.lockscreen_layout_source.index:
            settings.set_kb_group(self.lockscreen_layout_source.index)

        self.cinnamon.activate_layout_index(self.system_layout_source.index)

    def grab_focus(self):
        Gtk.Widget.grab_focus(self)

        length = self.get_buffer().get_length()
        self.select_region(length, -1)
