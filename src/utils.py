#! /usr/bin/python2

from gi.repository import GLib, Gio, Gdk, Gtk
import subprocess

def get_user_display_name():
    name = GLib.get_real_name()

    if not name or name == "Unknown":
        name = GLib.get_user_name()

    utf8_name = None

    if name:
        utf8_name = GLib.locale_to_utf8(name, -1, 0, 0)

    return utf8_name

def get_user_name():
    name = GLib.get_user_name()

    utf8_name = None

    if name:
        utf8_name = GLib.locale_to_utf8(name, -1, 0, 0)

    return utf8_name

def get_host_name():
    name = GLib.get_host_name()

    utf8_name = None

    if name:
        utf8_name = GLib.locale_to_utf8(name, -1, 0, 0)

    return utf8_name

def process_is_running(name):
    res = subprocess.check_output(["pidof", name])

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

def do_logout():
    command = "%s %s" % ("cinnamon-session-quit", "--logout --no-prompt")
    ctx = Gdk.Display.get_default().get_app_launch_context()

    app = Gio.AppInfo.create_from_commandline(command, "cinnamon-session-quit", 0)
    if app:
        app.launch(None, ctx)

    do_quit()

def override_user_time(window):
    ev_time = Gtk.get_current_event_time()

    window.set_user_time(ev_time)

def debug_allocation(alloc):
    print("x:%d, y:%d, width:%d, height:%d" % (alloc.x, alloc.y, alloc.width, alloc.height))

def do_quit():
    Gtk.main_quit()



class Settings:
    def __init__(self):
        pass