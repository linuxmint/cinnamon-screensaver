#! /usr/bin/python3

from gi.repository import Gtk, Gdk
import cairo

from util import trackers

class VolumeSlider(Gtk.Scale):
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
        border = ctx.get_padding(Gtk.StateFlags.NORMAL)

        x = padding.left + border.left
        y = padding.top + border.top
        width = alloc.width - padding.left - padding.right - border.left - border.right
        height = alloc.height - padding.top - padding.bottom - border.top - border.bottom
        value = round(self.get_value())
        floor = y + height

        if self.muted:
            fill_color = ctx.get_background_color(Gtk.StateFlags.INSENSITIVE)
        else:
            fill_color = ctx.get_background_color(Gtk.StateFlags.NORMAL)

        cr.set_line_width(1)
        cr.set_antialias(cairo.ANTIALIAS_GRAY)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        cr.save()

        cr.new_sub_path()
        cr.move_to(x, floor)
        cr.line_to(x + width, floor)
        cr.line_to(x + width, y)
        cr.close_path()

        cr.set_source_rgba(1, 1, 1, .1)

        cr.fill()

        cr.new_sub_path()
        cr.move_to(x, floor)
        cr.line_to(x + ((value / 100) * width), floor)
        cr.line_to(x + ((value / 100) * width), floor - ((value / 100) * height))
        cr.close_path()

        Gdk.cairo_set_source_rgba(cr, fill_color)
        cr.fill()

        cr.restore()

        return True

