#! /usr/bin/python3

from gi.repository import GLib, Gio, Gdk, Gtk
import os
import grp
import subprocess

import config

# Various utility functions that are used in multiple places.

def nofail_locale_to_utf8(string):
    try:
        ret = GLib.locale_to_utf8(string, -1, 0, 0)
    except:
        try:
            ret, br, bw = GLib.locale_to_utf8(string, -1)
        except:
            ret = string

    return ret

def get_user_display_name():
    name = GLib.get_real_name()

    if not name or name == "Unknown":
        name = GLib.get_user_name()

    utf8_name = None

    if name:
        utf8_name = nofail_locale_to_utf8(name)

    return utf8_name

def get_user_name():
    name = GLib.get_user_name()

    utf8_name = None

    if name:
        utf8_name = nofail_locale_to_utf8(name)

    return utf8_name

def get_host_name():
    name = GLib.get_host_name()

    utf8_name = None

    if name:
        utf8_name = nofail_locale_to_utf8(name)

    return utf8_name

def user_can_lock():
    name = GLib.get_user_name()

    # KeyError is generated if group doesn't exist, ignore it and allow lock
    try:
        group = grp.getgrnam("nopasswdlogin")
        if name in group.gr_mem:
            return False
    except KeyError:
        pass

    return True

def process_is_running(name):
    res = ""

    try:
        res = subprocess.check_output(["pidof", name])
    except subprocess.CalledProcessError:
        pass

    return res != ""

def do_user_switch():
    if process_is_running("mdm"):
        command = "%s %s" % ("mdmflexiserver", "--startnew Standard")
        ctx = Gdk.Display.get_default().get_app_launch_context()

        app = Gio.AppInfo.create_from_commandline(command, "mdmflexiserver", 0)
        if app:
            app.launch(None, ctx)
    elif process_is_running("gdm"):
        command = "%s %s" % ("gdmflexiserver", "--startnew Standard")
        ctx = Gdk.Display.get_default().get_app_launch_context()

        app = Gio.AppInfo.create_from_commandline(command, "gdmflexiserver", 0)
        if app:
            app.launch(None, ctx)
    elif os.getenv("XDG_SEAT_PATH") is not None:
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            bus.call_sync("org.freedesktop.DisplayManager",
                          os.getenv("XDG_SEAT_PATH"),
                          "org.freedesktop.DisplayManager.Seat",
                          "SwitchToGreeter",
                          None,
                          None,
                          Gio.DBusCallFlags.NONE,
                          -1,
                          None)

        except GLib.Error as err:
            print("Switch user failed: " + err.message)

def session_is_cinnamon():
    if "cinnamon" in GLib.getenv("DESKTOP_SESSION"):
        if GLib.find_program_in_path("cinnamon-session-quit"):
            return True

    return False

def override_user_time(window):
    ev_time = Gtk.get_current_event_time()

    window.set_user_time(ev_time)

def debug_allocation(alloc):
    print("x:%d, y:%d, width:%d, height:%d" % (alloc.x, alloc.y, alloc.width, alloc.height))

def get_mouse_monitor():
    manager = Gdk.Display.get_default().get_device_manager()
    pointer = manager.get_client_pointer()

    screen, x, y = pointer.get_position()

    return Gdk.Screen.get_default().get_monitor_at_point(x, y)

def get_primary_monitor():
    return Gdk.Screen.get_default().get_primary_monitor()

def lookup_plugin_path(name):
    if name == "":
        return None

    try_path = os.path.join(config.pkgdatadir,
                                "screensavers",
                                name,
                                "main")

    if not os.path.exists(try_path):
        try_path = os.path.join(GLib.get_user_data_dir(),
                                "cinnamon-screensaver",
                                "screensavers",
                                name,
                                "main")
        if not os.path.exists(try_path):
            return None

    return try_path

def CLAMP(value, low, high):
        return max(low, min(value, high))

def have_gtk_version(version_string):
    [major, minor, micro] = version_string.split(".", 3)

    return Gtk.get_major_version() >= eval(major) and \
           Gtk.get_minor_version() >= eval(minor) and \
           Gtk.get_micro_version() >= eval(micro)

def do_quit():
    Gtk.main_quit()
