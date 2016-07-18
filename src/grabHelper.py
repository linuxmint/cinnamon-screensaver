#! /usr/bin/python3

from gi.repository import Gdk, Gtk

from eventHandler import EventHandler

class GrabHelper:
    def __init__(self):

        self.offscreen = OffscreenWindow()
        self.offscreen.show()

        self.screen = Gdk.Screen.get_default()

        self.mouse_grab_window = None
        self.keyboard_grab_window = None
        self.mouse_hide_cursor = False

    def grab_root(self, hide_cursor):
        root = self.screen.get_root_window()

        return self.grab_window(root, hide_cursor)

    def grab_offscreen(self, hide_cursor):
        window = self.offscreen.get_window()

        return self.grab_window(window, hide_cursor)

    def grab_window(self, window, hide_cursor):
        got_mouse = self.grab_mouse(window, hide_cursor)
        got_keyboard = self.grab_keyboard(window)

        if got_mouse != Gdk.GrabStatus.SUCCESS and got_keyboard != Gdk.GrabStatus.SUCCESS:
            self.release_keyboard()
            self.release_mouse()
            return False

        return True

    def release(self):
        self.release_mouse()
        self.release_keyboard()
        self.screen.get_display().sync()

    def reset_mouse(self):
        if self.mouse_grab_window is not None:
            self.mouse_grab_window = None
            self.mouse_hide_cursor = False

    def release_mouse(self):
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
            self.mouse_grab_window.weak_ref(self.on_window_finalize, "mouse")
            self.mouse_hide_cursor = hide_cursor
        else:
            print("couldn't grab mouse")

        return status

    def reset_keyboard(self):
        if self.keyboard_grab_window is not None:
            self.keyboard_grab_window = None

    def release_keyboard(self):
        Gdk.keyboard_ungrab(Gdk.CURRENT_TIME)
        self.reset_keyboard()

    def grab_keyboard(self, window):
        status = Gdk.keyboard_grab(window, False, Gdk.CURRENT_TIME)

        if status == Gdk.GrabStatus.SUCCESS:
            self.reset_keyboard()

            self.keyboard_grab_window = window
            self.keyboard_grab_window.weak_ref(self.on_window_finalize, "keyboard")
        else:
            print("couldn't grab keyboard")

        return status

    def on_window_finalize(self, grab_type):
        if grab_type == "mouse":
            self.mouse_grab_window = None
            self.mouse_hide_cursor = False
        else:
            self.keyboard_grab_window = None

class OffscreenWindow(Gtk.Invisible):
    def __init__(self):
        super(OffscreenWindow, self).__init__()

        self.eh = EventHandler.get()

    def do_key_press_event(self, event):
        # print("OffscreenWindow: do_key_press_event")
        return self.eh.on_key_press_event(event)
