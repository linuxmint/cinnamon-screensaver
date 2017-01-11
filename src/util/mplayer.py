#! /usr/bin/python3

from Xlib import display
from gi.repository import GLib, GObject
from util import settings

class Mplayer:

    """
    used to checkif video is displaying to keep the lock-screen tranparent
    """
    def __init__(self, widget):

        self.destroy = False
        self.fs = False
        if not settings.get_allow_media_control():
            return

        MPLAYERS = ["Gnome-mpv", "mpv", "vlc", "Xplayer", "Bino", "MPlayer", "Gnome-mplayer", "Xviewer", "Xreader", "Soffice"]

        dpy = display.Display()
        scr = dpy.screen()
        window = dpy.get_input_focus().focus
        wmclass = window.get_wm_class()

        if wmclass is None:
            window = window.query_tree().parent
            wmclass = window.get_wm_class()

        wmgeom = window.get_geometry()
        self.sw=scr.width_in_pixels 
        self.window = window
        if wmclass[1] in MPLAYERS:
            if wmgeom.width == scr.width_in_pixels and wmgeom.height == scr.height_in_pixels and wmgeom.x == 0 and wmgeom.y == 0:
                self.fs = True
                GObject.timeout_add(100, self.mplayer_check, widget)


    def mplayer_check(self, widget):

        if self.destroy:
            return GLib.SOURCE_REMOVE
        try:
            wmgeom = self.window.get_geometry()
        except:
            wmgeom = None

        if wmgeom and wmgeom.width == self.sw:
            return GLib.SOURCE_CONTINUE

        self.fs = False
        widget.update_monitor_views()
        widget.set_opacity(1.0)
        widget.on_bg_changed(None)

        return GLib.SOURCE_REMOVE

