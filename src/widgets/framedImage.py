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

class FramedImage(Gtk.Image):
    """
    Widget to hold the user face image.  It can be sized using CSS color.red value
    (up to 255px) in Gtk 3.18, and using the min-height style property in gtk 3.20+.
    """
    def __init__(self):
        super(FramedImage, self).__init__()
        self.get_style_context().add_class("framedimage")

        self.path = None
        self.min_height = 50

        trackers.con_tracker_get().connect(self, "realize", self.on_realized)

    def on_realized(self, widget):
        self.generate_image()

    def generate_image(self):
        ctx = self.get_style_context()

        if utils.have_gtk_3_20():
            self.min_height = ctx.get_property("min-height", Gtk.StateFlags.NORMAL)
        else:
            self.min_height = ctx.get_color(Gtk.StateFlags.NORMAL).red * 255

        self.set_size_request(-1, self.min_height)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.path, -1, self.min_height, True)
        self.set_from_pixbuf(pixbuf)

    def set_from_file(self, path):
        self.path = path

        if self.get_realized():
            self.generate_image()

