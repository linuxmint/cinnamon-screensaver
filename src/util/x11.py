#! /usr/bin/python3

from Xlib import display, X
from gi.repository import GLib, GObject


def nuke_focus():
    """
    Used by GrabHelper (only if python3-xlib is available) to help
    break a grab.  Usually never reached.
    """
    print("screensaver - x11 - nuking focus")
    xdisplay = display.Display()
    ret = xdisplay.get_input_focus()

    xdisplay.set_input_focus(X.NONE, X.RevertToNone, X.CurrentTime, None)


class Mplayer:

    """
    used to checkif video is displaying to keep the lock-screen tranparent
    """
    def __init__(self, widget):

        MPLAYERS = ["Gnome-mpv", "mpv", "vlc", "Xplayer", "Bino", "MPlayer", "Gnome-mplayer", "Xviewer", "Xreader", "Soffice"]

        dpy = display.Display()
        scr = dpy.screen()
        window = dpy.get_input_focus().focus
        wmclass = window.get_wm_class()
        self.destroy=False

        if wmclass is None:
            window = window.query_tree().parent
            wmclass = window.get_wm_class()

        wmgeom = window.get_geometry()
        self.sw=scr.width_in_pixels 
        self.window = window
        self.wmclass = None
        if wmclass[1] in MPLAYERS:
            if wmgeom.width == scr.width_in_pixels and wmgeom.height == scr.height_in_pixels and wmgeom.x == 0 and wmgeom.y == 0:
                self.wmclass = wmclass[1]
                GObject.idle_add(self.mplayer_check, 200, widget.mplayer_cb)


    def mplayer_check(self, ms, callback = None):

        if self.destroy:
            return GLib.SOURCE_REMOVE
        try:
            wmgeom = self.window.get_geometry()
        except:
            wmgeom = None

        if wmgeom and wmgeom.width == self.sw:
            return GLib.SOURCE_CONTINUE

        callback()
        return GLib.SOURCE_REMOVE

