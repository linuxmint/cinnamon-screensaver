#!/usr/bin/python3
# coding: utf-8

import gi

gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio, GLib, GObject, Gdk

from util import utils, trackers

MAX_IMAGE_SIZE = 320
MAX_IMAGE_SIZE_LOW_RES = 200

class FramedImage(Gtk.Image):
    """
    Widget to hold the user face image.  It attempts to display an image at
    its native size, up to a max sane size.
    """
    __gsignals__ = {
        "surface-changed": (GObject.SignalFlags.RUN_LAST, None, (object,))
    }
    def __init__(self, low_res=False, scale_up=False):
        super(FramedImage, self).__init__()
        self.get_style_context().add_class("framedimage")

        self.cancellable = None

        self.file = None
        self.path = None
        self.scale_up = scale_up

        if low_res:
            self.max_size = MAX_IMAGE_SIZE_LOW_RES
        else:
            self.max_size = MAX_IMAGE_SIZE

        trackers.con_tracker_get().connect(self, "realize", self.on_realized)

    def on_realized(self, widget):
        self.generate_image()

    def clear_image(self):
        self.set_from_surface(None)
        self.emit("surface-changed", None)

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

    def set_image_internal(self, path):
        pixbuf = None
        scaled_max_size = self.max_size * self.get_scale_factor()

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        except GLib.Error as e:
            message = "Could not load pixbuf from '%s' for FramedImage: %s" % (path, e.message)
            error = True

        if pixbuf != None:
            if (pixbuf.get_height() > scaled_max_size or pixbuf.get_width() > scaled_max_size) or \
               (self.scale_up and (pixbuf.get_height() < scaled_max_size / 2 or pixbuf.get_width() < scaled_max_size / 2)):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(path, scaled_max_size, scaled_max_size)
                except GLib.Error as e:
                    message = "Could not scale pixbuf from '%s' for FramedImage: %s" % (path, e.message)
                    error = True

        if pixbuf:
            surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf,
                                                           self.get_scale_factor(),
                                                           self.get_window())
            self.set_from_surface(surface)
            self.emit("surface-changed", surface)
        else:
            print(message)
            self.clear_image()

    def generate_image(self):
        if self.path:
            self.set_image_internal(self.path)
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
                self.set_image_internal(file.get_path())
        except GLib.Error:
            pass
