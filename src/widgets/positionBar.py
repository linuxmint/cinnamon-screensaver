#! /usr/bin/python3

from gi.repository import Gtk, Gdk

from util import trackers

class PositionBar(Gtk.ProgressBar):
    """
    A custom GtkProgressBar for displaying the current track position.
    """
    def __init__(self):
        super(PositionBar, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.get_style_context().add_class("positionbar")

        self.set_can_focus(False)

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        trackers.con_tracker_get().connect(self,
                                           "draw",
                                           self.on_draw)

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
        value = self.get_fraction()
        value_width = value * width

        fill_color = ctx.get_color(Gtk.StateFlags.NORMAL)
        bg_color = ctx.get_background_color(Gtk.StateFlags.NORMAL)

        cr.save()

        cr.new_sub_path()
        cr.rectangle(x, y, end, floor)
        Gdk.cairo_set_source_rgba(cr, bg_color)
        cr.fill()

        cr.restore()
        cr.save()

        cr.new_sub_path()
        cr.rectangle(x, y, value_width, floor)
        Gdk.cairo_set_source_rgba(cr, fill_color)
        cr.fill()

        cr.restore()

        return True

