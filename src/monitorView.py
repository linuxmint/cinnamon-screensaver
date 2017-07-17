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
    __gsignals__ = {
        'current-view-change-complete': (GObject.SignalFlags.RUN_LAST, None, ()),
    }
    def __init__(self, index):
        super(MonitorView, self).__init__()

        self.monitor_index = index

        self.proc = None

        self.update_geometry()

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(250)
        self.add(self.stack)

        self.wallpaper_stack = WallpaperStack()
        self.wallpaper_stack.show()
        self.wallpaper_stack.set_halign(Gtk.Align.FILL)
        self.wallpaper_stack.set_valign(Gtk.Align.FILL)

        self.stack.add_named(self.wallpaper_stack, "wallpaper")

        self.socket = Gtk.Socket()
        self.socket.show()
        self.socket.set_halign(Gtk.Align.FILL)
        self.socket.set_valign(Gtk.Align.FILL)

        # This prevents the socket from self-destructing when the plug process is killed
        trackers.con_tracker_get().connect(self.socket,
                                           "plug-removed",
                                           lambda socket: True)

        self.stack.add_named(self.socket, "plugin")

        self.show_all()

    def set_initial_wallpaper_image(self, image):
        self.wallpaper_stack.set_initial_image(image)

    def set_next_wallpaper_image(self, image):
        self.wallpaper_stack.transition_to_image(image)

    def kill_plugin(self):
        """
        Asks the active plug-in to exit gracefully.
        The plug-in script is set to run Gtk.main_quit()
        when it receives a SIGTERM.
        """
        if self.proc:
            self.proc.send_signal(signal.SIGTERM)
            self.proc = None

    def show_plugin(self):
        """
        Attempt to retreive the current plug-in info and spawn
        a script to instantiate it.
        """
        name = settings.get_screensaver_name()
        path = utils.lookup_plugin_path(name)
        if path is not None:
            self.spawn_plugin(path)
            trackers.con_tracker_get().connect(self.socket,
                                               "plug-added",
                                               self.on_plug_added)

    def on_plug_added(self, socket, data=None):
        """
        Callback for a plug-in being added to our GtkSocket.  This
        completes the operation and makes the plugin stack child the
        visible child for this MonitorView.
        """
        trackers.con_tracker_get().disconnect(self.socket,
                                              "plug-added",
                                              self.on_plug_added)

        status.PluginRunning = True

        if self.stack.get_visible_child_name() == "plugin":
            self.emit("current-view-change-complete")
            return

        self.stack.set_visible_child_name("plugin")
        trackers.con_tracker_get().connect(self.stack,
                                           "notify::transition-running",
                                           self.notify_transition_callback)

    def show_wallpaper(self):
        """
        Initiate showing the wallpaper child of MonitorView
        """
        status.PluginRunning = False

        if self.stack.get_visible_child_name() == "wallpaper":
            self.emit("current-view-change-complete")
            return

        self.stack.set_visible_child_name("wallpaper")
        trackers.con_tracker_get().connect(self.stack,
                                           "notify::transition-running",
                                           self.notify_transition_callback)

    def notify_transition_callback(self, stack, pspec, data=None):
        """
        GtkStacks don't have any signal for telling you 'we're done transitioning'
        the closest we can come to it is for every animation tick they call a notify
        on the 'transition-running' property.  We wait until it returns False
        to emit our own transition completed signal.  This only works because our
        stack here *does* use a duration and transition type that isn't "None".
        """
        if stack.get_transition_running():
            return
        else:
            trackers.con_tracker_get().disconnect(self.stack,
                                                  "notify::transition-running",
                                                  self.notify_transition_callback)
            self.emit("current-view-change-complete")

    def update_view(self, awake, low_power):
        """
        Syncs the current MonitorView state to whatever is appropriate, depending
        on whether we're awake and whether a plugin should be visible instead.
        """
        self.kill_plugin()

        if not awake and not low_power and settings.should_show_plugin():
            self.show_plugin()
        else:
            self.show_wallpaper()

    def spawn_plugin(self, path):
        """
        Spawns the plug-in script and watches its STDOUT for a window ID to use for
        our GtkSocket.  We hold a reference to it so that we can terminate it properly
        later.
        """
        try:
            self.proc = Gio.Subprocess.new((path, None),
                                           Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)

            pipe = self.proc.get_stdout_pipe()
            pipe.read_bytes_async(4096, GLib.PRIORITY_DEFAULT, None, self.on_bytes_read)

        except Exception as e:
            print(e)
            return

    def on_bytes_read(self, pipe, res):
        bytes_read = pipe.read_bytes_finish(res)
        pipe.close(None)

        if bytes_read:
            output = bytes_read.get_data().decode()

            if output:
                match = re.match('^\s*WINDOW ID=(\d+)\s*$', output)
                if match:
                    self.socket.add_id(int(match.group(1)))

