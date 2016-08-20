#! /usr/bin/python3

from gi.repository import Gtk, Gdk
import cairo

import trackers

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
        self.set_size_request(170, -1)

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

        x = padding.left
        y = padding.top
        width = alloc.width - padding.left - padding.right
        height = alloc.height - padding.top - padding.bottom
        ratio = height / width
        value = round(self.get_value())
        floor = y + height
        current_val = 8
        bar_width = 6

        if self.muted:
            fill_color = ctx.get_background_color(Gtk.StateFlags.INSENSITIVE)
            border_color = ctx.get_border_color(Gtk.StateFlags.INSENSITIVE)
        else:
            fill_color = ctx.get_background_color(Gtk.StateFlags.NORMAL)
            border_color = ctx.get_border_color(Gtk.StateFlags.NORMAL)

        cr.set_line_width(1)
        cr.set_antialias(cairo.ANTIALIAS_GRAY)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        cr.save()

        while current_val <= value * 1.6:
            cr.save()
            cr.new_sub_path()
            cr.move_to(current_val, floor)
            short_corner_y = (current_val / 160) * height
            cr.line_to(current_val, floor - short_corner_y)
            cr.line_to(current_val + bar_width, floor - (short_corner_y + (bar_width * ratio)))
            cr.line_to(current_val + bar_width, floor)
            cr.line_to(current_val, floor)
            Gdk.cairo_set_source_rgba(cr, fill_color)
            cr.fill_preserve()
            Gdk.cairo_set_source_rgba(cr, border_color)
            cr.stroke()
            current_val += 8
            cr.restore()

        while current_val <= 160:
            cr.save()
            cr.new_sub_path()
            cr.move_to(current_val, floor)
            short_corner_y = (current_val / 160) * height
            cr.line_to(current_val, floor - short_corner_y)
            cr.line_to(current_val + bar_width, floor - (short_corner_y + (bar_width * ratio)))
            cr.line_to(current_val + bar_width, floor)
            cr.line_to(current_val, floor)
            cr.set_source_rgba(1, 1, 1, .1)
            cr.fill_preserve()
            Gdk.cairo_set_source_rgba(cr, border_color)
            cr.stroke()
            current_val += 8
            cr.restore()

        cr.restore()

        return True

