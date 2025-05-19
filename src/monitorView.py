#!/usr/bin/python3

from gi.repository import Gtk, Gio, GLib, GObject
import re
import cairo
import signal

import status
from baseWindow import BaseWindow
from util import settings, utils, trackers

class WallpaperStack(Gtk.Stack):
    """
    WallpaperStack implements a crossfade when changing backgrounds.

    An initial image is made and added to the GtkStack.  When a new
    image is requested, it is created and added to the stack, then
    a crossfade transition is made to the new child.  The former
    visible stack child is then destroyed.  And this repeats.
    """
    def __init__(self):
        super(WallpaperStack, self).__init__()

        self.set_transition_type(Gtk.StackTransitionType.NONE)
        self.set_transition_duration(1000)

        self.initialized = False
        self.current = None
        self.queued = None

    def transition_to_image(self, image):
        """
        Queues a new image in the stack, and begins the transition to it.
        """
        self.queued = image
        self.queued.set_visible(True)

        trackers.con_tracker_get().connect_after(image,
                                                 "draw",
                                                 self.shade_wallpaper)

        self.add(self.queued)

        if not self.initialized:
            self.visible_image_changed()
            self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.initialized = True
            return

        self.set_visible_child(self.queued)
        GObject.timeout_add(2000, self.visible_image_changed)

    def visible_image_changed(self, data=None):
        if self.current is not None:
            tmp = self.current

            self.remove(tmp)
            tmp.destroy()

        self.current = self.queued
        self.queued = None

        return False

    def shade_wallpaper(self, widget, cr):
        """
        This draw callback adds a shade mask over the current
        image.  It is uniform when not Awake, and acquires a
        significant gradient vertically framing the unlock dialog
        when Awake.
        """
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.paint()
        return False

class MonitorView(BaseWindow):
    """
    A monitor-sized child of the stage that is responsible for displaying
    the currently-selected wallpaper or appropriate plug-in.
    """
    def __init__(self, index):
        super(MonitorView, self).__init__()

        self.monitor_index = index

        self.update_geometry()

        self.wallpaper_stack = WallpaperStack()
        self.wallpaper_stack.show()
        self.wallpaper_stack.set_halign(Gtk.Align.FILL)
        self.wallpaper_stack.set_valign(Gtk.Align.FILL)
        self.add(self.wallpaper_stack)

        self.show_all()

    def set_next_wallpaper_image(self, image):
        self.wallpaper_stack.transition_to_image(image)
