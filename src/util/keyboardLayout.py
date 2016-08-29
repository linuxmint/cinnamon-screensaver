#! /usr/bin/python3

import gi
gi.require_version('Gkbd', '3.0')

from gi.repository import Gkbd, Gdk, GdkPixbuf, Gtk, GObject
import cairo
import os

from util import trackers, settings
import config

class KeyboardLayout(GObject.Object):
    __gsignals__ = {
        'group-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }
    def __init__(self):
        super(KeyboardLayout, self).__init__()

        self.config = Gkbd.Configuration()
        self.enabled = len(self.config.get_group_names()) > 1
        self.original_group = 0

    def set_lockscreen_group(self):
        if not self.enabled:
            return

        # If there are multiple keyboard layouts, we want to store
        # the one the user ends up using in the unlock widget, as they'll
        # want to use the same one each time, at least until they change
        # their password.

        saved_group = settings.get_kb_group()
        self.original_group = self.config.get_current_group()

        new_group = 0

        if saved_group == -1:
            new_group = self.original_group
        else:
            new_group = saved_group

        self.config.lock_group(new_group)
        self.update_saved_group(new_group)

        trackers.con_tracker_get().connect(self.config,
                                           "group-changed",
                                           self.on_group_changed)

        self.config.start_listen()

    def restore_original_group(self):
        trackers.con_tracker_get().disconnect(self.config,
                                              "group-changed",
                                              self.on_group_changed)

        self.config.lock_group(self.original_group)

    def next_group(self):
        self.config.lock_next_group()
        self.update_saved_group(self.config.get_current_group())

    def update_saved_group(self, group):
        settings.set_kb_group(group)

    def on_group_changed(self, config, group):
        self.update_saved_group(group)
        self.emit("group-changed")

    def get_image_pixbuf(self, widget):
        pixbuf = None

        if self.enabled:
            group = self.config.get_current_group()
            name = self.config.get_group_name(group)

            if settings.get_show_flags():
                path = os.path.join(config.datadir, "cinnamon", "flags", "%s.png" % name)
                if os.path.exists(path):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

            if pixbuf == None:
                pixbuf = self.get_text_pixbuf(name, widget)

        return pixbuf

    def get_text_pixbuf(self, text, widget):
        v, w, h = Gtk.icon_size_lookup(Gtk.IconSize.MENU)

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)

        cr.set_source_rgba(0, 0, 0, 0)
        cr.fill()

        font_size = 10.0

        cr.move_to(0, h - ((h - font_size) / 2))

        rgba = widget.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        Gdk.cairo_set_source_rgba(cr, rgba)

        cr.show_text(text.upper()[:2])

        final_surf = cr.get_target()
        pixbuf = Gdk.pixbuf_get_from_surface(final_surf, 0, 0, w, h)

        return pixbuf
