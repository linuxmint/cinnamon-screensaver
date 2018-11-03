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

        self.current = None

    def set_initial_image(self, image):
        """
        Creates and sets the initial background image to use in
        the WallpaperStack.
        """
        self.current = image
        self.current.set_visible(True)

        trackers.con_tracker_get().connect_after(image,
                                                 "draw",
                                                 self.shade_wallpaper)

        self.add(self.current)
        self.set_visible_child(self.current)

        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

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
        self.set_visible_child(self.queued)

        tmp = self.current
        self.current = self.queued
        self.queued = None

        # No need to disconnect the draw handler, it'll be disco'd by the con_tracker's
        # weak_ref callback.

        GObject.idle_add(tmp.destroy)

    def shade_wallpaper(self, widget, cr):
        """
        This draw callback adds a shade mask over the current
        image.  It is uniform when not Awake, and acquires a
        significant gradient vertically framing the unlock dialog
        when Awake.
        """
        if not status.Awake:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
            cr.paint()
            return False

        r = widget.get_allocation()

        pattern = cairo.LinearGradient(0, 0, 0, r.height)
        pattern.add_color_stop_rgba (0, 0, 0, 0, .75);
        pattern.add_color_stop_rgba (.35, 0, 0, 0, .9);
        pattern.add_color_stop_rgba (.65, 0, 0, 0, .9);
        pattern.add_color_stop_rgba (1, 0, 0, 0, .75);
        cr.set_source(pattern)
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

    def set_initial_wallpaper_image(self, image):
        self.wallpaper_stack.set_initial_image(image)

    def set_next_wallpaper_image(self, image):
        self.wallpaper_stack.transition_to_image(image)
