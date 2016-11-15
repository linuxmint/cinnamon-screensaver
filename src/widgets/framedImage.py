#! /usr/bin/python3
# coding: utf-8

import gi

gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio, GLib, GObject

from util import utils, trackers

class FramedImage(Gtk.Image):
    """
    Widget to hold the user face image.  It can be sized using CSS color.red value
    (up to 255px) in Gtk 3.18, and using the min-height style property in gtk 3.20+.
    """
    __gsignals__ = {
        "pixbuf-changed": (GObject.SignalFlags.RUN_LAST, None, (object,))
    }
    def __init__(self):
        super(FramedImage, self).__init__()
        self.get_style_context().add_class("framedimage")

        self.cancellable = None

        self.file = None
        self.path = None
        self.loader = None

        self.current_pixbuf = None
        self.next_pixbuf = None

        self.min_height = 50

        trackers.con_tracker_get().connect(self, "realize", self.on_realized)

    def get_theme_height(self):
        ctx = self.get_style_context()

        if utils.have_gtk_version("3.20.0"):
            return ctx.get_property("min-height", Gtk.StateFlags.NORMAL)
        else:
            color = ctx.get_color(Gtk.StateFlags.NORMAL)
            return (color.red * 255) + (color.green * 255) + (color.blue * 255)

    def on_realized(self, widget):
        self.generate_image()

    def clear_image(self):
        self.set_from_pixbuf(None)
        self.emit("pixbuf-changed", None)

    def set_from_path(self, path):
        self.path = path
        self.file = None

        if self.get_realized():
            self.generate_image()

    def set_from_file(self, file):
        self.file = file
        self.path = None

        if self.get_realized():
            self.generate_image()

    def generate_image(self):
        self.set_size_request(-1, self.get_theme_height())

        if self.path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.path, -1, self.get_theme_height(), True)
            self.set_from_pixbuf(pixbuf)
            self.emit("pixbuf-changed", pixbuf)

        elif self.file:
            if self.cancellable != None:
                self.cancellable.cancel()
                self.cancellable = None

            self.cancellable = Gio.Cancellable()
            self.file.load_contents_async(self.cancellable, self.load_contents_async_callback)

    def load_contents_async_callback(self, file, result, data=None):
        try:
            success, contents, etag_out = file.load_contents_finish(result)
        except GLib.Error:
            self.clear_image()
            return

        if contents:
            cache_name = GLib.build_filenamev([GLib.get_user_cache_dir(), "cinnamon-screensaver-albumart-temp"])
            cache_file = Gio.File.new_for_path(cache_name)

            cache_file.replace_contents_async(contents,
                                              None,
                                              False,
                                              Gio.FileCreateFlags.REPLACE_DESTINATION,
                                              self.cancellable,
                                              self.on_file_written)

    def on_file_written(self, file, result, data=None):
        try:
            if file.replace_contents_finish(result):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(file.get_path(), -1, self.get_theme_height(), True)
                self.set_from_pixbuf(pixbuf)
                self.emit("pixbuf-changed", pixbuf)
        except GLib.Error:
            pass