#!/usr/bin/python3

from gi.repository import Gtk, Gdk

from util import trackers

class VolumeSlider(Gtk.Scale):
    """
    Custom GtkScale widget for controlling the volume.
    """
    def __init__(self):
        super(VolumeSlider, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.set_can_focus(False)

        self.muted = False

        self.set_range(0, 100.0)
        self.set_increments(5.0, 5.0)
        self.get_style_context().remove_class("scale")
        self.get_style_context().add_class("volumeslider")
        self.set_round_digits(0)
        self.set_draw_value(False)
        self.set_size_request(130, -1)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        trackers.con_tracker_get().connect(self,
                                           "draw",
                                           self.on_draw)

    def set_muted(self, muted):
        if muted != self.muted:
            self.muted = muted
            self.queue_draw()

    def on_draw(self, widget, cr):
        ctx = widget.get_style_context()
        alloc = self.get_allocation()

        padding = ctx.get_padding(Gtk.StateFlags.NORMAL)
        border = ctx.get_border(Gtk.StateFlags.NORMAL)

        x = padding.left + border.left
        y = padding.top + border.top
        width = alloc.width - padding.left - padding.right - border.left - border.right
        height = alloc.height - padding.top - padding.bottom - border.top - border.bottom
        floor = y + height
        end = x + width
        value = round(self.get_value())
        value_x = x + ((value / 100) * width)
        value_y = floor - ((value / 100) * height)

        if self.muted:
            fill_color = ctx.get_color(Gtk.StateFlags.INSENSITIVE)
            bg_color = ctx.get_background_color(Gtk.StateFlags.INSENSITIVE)
        else:
            fill_color = ctx.get_color(Gtk.StateFlags.NORMAL)
            bg_color = ctx.get_background_color(Gtk.StateFlags.NORMAL)

        cr.save()

        cr.new_sub_path()
        cr.move_to(x, floor)
        cr.line_to(end, floor)
        cr.line_to(end, y)
        cr.close_path()

        Gdk.cairo_set_source_rgba(cr, bg_color)
        cr.fill()

        cr.restore()
        cr.save()

        cr.new_sub_path()
        cr.move_to(x, floor)
        cr.line_to(value_x, floor)
        cr.line_to(value_x, value_y)
        cr.close_path()

        Gdk.cairo_set_source_rgba(cr, fill_color)
        cr.fill()

        cr.restore()

        return True
