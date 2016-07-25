#! /usr/bin/python3

from gi.repository import Gdk, Gtk, GdkX11
import time

import x11
from eventHandler import EventHandler

class GrabHelper:
    def __init__(self, manager = None):

        if manager:
            self.offscreen = OffscreenWindow(manager)
            self.offscreen.show()
        else:
            self.offscreen = None

        self.screen = Gdk.Screen.get_default()

        self.mouse_grab_window = None
        self.keyboard_grab_window = None
        self.mouse_hide_cursor = False

    def grab_root(self, hide_cursor):
        root = self.screen.get_root_window()

        return self.grab_window(root, hide_cursor)

    def grab_offscreen(self, hide_cursor):
        if self.offscreen == None:
            print("can't grab offscreen without an offscreen widget")
            return False

        window = self.offscreen.get_window()

        return self.grab_window(window, hide_cursor)

    def grab_window(self, window, hide_cursor):
        got_keyboard = False
        got_mouse = False

        def try_grab(grab_func, *args):
            retries = 0
            while retries < 4:
                got = grab_func(*args)
                if got:
                    return True

                retries = retries + 1
                time.sleep(1)
            return False

        got_keyboard = try_grab(self.grab_keyboard, window)

        if not got_keyboard:
            x11.nuke_focus()
            got_keyboard = try_grab(self.grab_keyboard, window)

        got_mouse = try_grab(self.grab_mouse, window, hide_cursor)

        if not got_mouse or not got_keyboard:
            if got_keyboard:
                self.release_keyboard()
            if got_mouse:
                self.release_mouse()
            return False

        return True

    def move_to_window(self, window, hide_cursor):
        result = False
        while not result:
            result = self.move_keyboard(window)
            Gdk.flush()

        result = False
        while not result:
            result = self.move_mouse(window, hide_cursor)
            Gdk.flush()

    def release(self):
        self.release_mouse()
        self.release_keyboard()
        self.screen.get_display().sync()

    def reset_mouse(self):
        if self.mouse_grab_window is not None:
            self.mouse_grab_window = None
            self.mouse_hide_cursor = False

    def release_mouse(self):
        if self.mouse_grab_window is not None:
            Gdk.pointer_ungrab(Gdk.CURRENT_TIME)
            self.reset_mouse()

    def grab_mouse(self, window, hide_cursor = False):
        if hide_cursor:
            cursor = Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR)
        else:
            cursor = None

        status = Gdk.pointer_grab(window, True, 0, None, cursor, Gdk.CURRENT_TIME)

        if status == Gdk.GrabStatus.SUCCESS:
            self.reset_mouse()
            self.mouse_grab_window = window
            self.mouse_hide_cursor = hide_cursor
        else:
            print("couldn't grab mouse")

        return status == Gdk.GrabStatus.SUCCESS

    def move_mouse(self, window, hide_cursor):
        GdkX11.x11_grab_server()

        old_window = self.mouse_grab_window

        if old_window:
            self.release_mouse()

        res = self.grab_mouse(window, hide_cursor)
        if not res:
            time.sleep(1)
            res = self.grab_mouse(window, hide_cursor)

        if not res and old_window:
            self.grab_mouse(old_window)

        GdkX11.x11_ungrab_server()

        return res

    def reset_keyboard(self):
        if self.keyboard_grab_window is not None:
            self.keyboard_grab_window = None

    def release_keyboard(self):
        if self.keyboard_grab_window is not None:
            Gdk.keyboard_ungrab(Gdk.CURRENT_TIME)
            self.reset_keyboard()

    def grab_keyboard(self, window):
        status = Gdk.keyboard_grab(window, False, Gdk.CURRENT_TIME)

        if status == Gdk.GrabStatus.SUCCESS:
            self.reset_keyboard()
            self.keyboard_grab_window = window
        else:
            print("couldn't grab keyboard")

        return status == Gdk.GrabStatus.SUCCESS

    def move_keyboard(self, window):
        GdkX11.x11_grab_server()

        old_window = self.keyboard_grab_window

        if old_window:
            self.release_keyboard()

        res = self.grab_keyboard(window)
        if not res:
            time.sleep(1)
            res = self.grab_keyboard(window)

        if not res and old_window:
            self.grab_keyboard(old_window)

        GdkX11.x11_ungrab_server()

        return res

class OffscreenWindow(Gtk.Invisible):
    def __init__(self, manager):
        super(OffscreenWindow, self).__init__()
        self.event_handler = EventHandler(manager)

    def do_key_press_event(self, event):
        return self.event_handler.on_key_press_event(event)
