#!/usr/bin/python3

from gi.repository import CinnamonDesktop, CDesktopEnums, GLib, Gtk, Gio

from util import utils, trackers, settings
from baseWindow import BaseWindow
from floating import Floating

class ClockWidget(Floating, BaseWindow):
    """
    ClockWidget displays the time and away message on the screen.

    It is a child of the Stage's GtkOverlay, and its placement is
    controlled by the overlay's child positioning function.

    When not Awake, it positions itself around all monitors
    using a timer which randomizes its halign and valign properties
    as well as its current monitor.
    """
    def __init__(self, away_message=None, initial_monitor=0):
        super(ClockWidget, self).__init__(initial_monitor)
        self.get_style_context().add_class("clock")
        self.set_halign(Gtk.Align.START)

        if not settings.get_show_clock():
            return

        self.away_message = away_message

        self.label = Gtk.Label()
        self.label.show()
        self.add(self.label)

        self.clock_tracker = CinnamonDesktop.WallClock()
        self.set_clock_interval()

        trackers.con_tracker_get().connect(self.clock_tracker,
                                           "notify::clock",
                                           self.on_clock_changed)

        tz = Gio.File.new_for_path(path="/etc/localtime")
        self.tz_monitor = tz.monitor_file(0, None)

        trackers.con_tracker_get().connect(self.tz_monitor,
                                           "changed",
                                           self.on_tz_changed)

        trackers.con_tracker_get().connect(self,
                                           "destroy",
                                           self.on_destroy)

        self.update_clock()

    def set_clock_interval(self):
        interval = CDesktopEnums.ClockInterval.SETTING

        if settings.get_use_custom_format():
            date_format = settings.get_custom_date_format()
            time_format = settings.get_custom_time_format()

            use_seconds = False

            for token in ("%S", "%c", "%T", "%X"):
                if token in date_format or token in time_format:
                    use_seconds = True
                    break

            if use_seconds:
                interval = CDesktopEnums.ClockInterval.SECOND
            else:
                interval = CDesktopEnums.ClockInterval.MINUTE

        self.clock_tracker.set_update_interval(interval)

    def on_clock_changed(self, clock, pspec):
        self.update_clock()

    def on_tz_changed(self, monitor, file, other, event):
        self.update_clock()

    def get_clock_string(self):
        date_value = ""
        time_value = ""

        now = GLib.DateTime.new_now_local()

        if not settings.get_use_custom_format():
            if settings.get_clock_should_show_date():
                date_value = now.format(_("%A, %B %e"))
            else:
                date_value = ""

            if settings.get_clock_should_use_24h():
                time_value = now.format("%H:%M").lstrip()
            else:
                time_value = now.format("%l:%M %p").lstrip()
        else:
            date_value = now.format(settings.get_custom_date_format())
            time_value = now.format(settings.get_custom_time_format())

        clock_string = ('<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>\n' +\
                       '<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>')\
                        % (settings.get_time_font(), time_value, settings.get_date_font(), date_value)

        return clock_string

    def update_clock(self):
        default_message = GLib.markup_escape_text (settings.get_default_away_message(), -1)
        font_message = settings.get_message_font()

        if self.away_message and self.away_message != "":
            user_name = utils.get_user_display_name()
            markup = ('%s\n\n<b><span font_desc=\"Ubuntu 14\" foreground=\"#CCCCCC\">%s</span></b>' +\
                      '\n<b><span font_desc=\"Ubuntu 10\" foreground=\"#ACACAC\">  ~ %s</span></b>') %\
                     (self.get_clock_string(), self.away_message, user_name)
        else:
            markup = '%s\n\n<b><span font_desc=\"%s\" foreground=\"#CCCCCC\">%s</span></b>' %\
                     (self.get_clock_string(), font_message, default_message)

        self.label.set_markup(markup)
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.5, 0.5)

    def set_message(self, msg=""):
        self.away_message = msg
        self.update_clock()

    def on_destroy(self, data=None):
        trackers.con_tracker_get().disconnect(self.clock_tracker,
                                              "notify::clock",
                                              self.on_clock_changed)

        trackers.con_tracker_get().disconnect(self.tz_monitor,
                                              "changed",
                                              self.on_tz_changed)

        trackers.con_tracker_get().disconnect(self,
                                              "destroy",
                                              self.on_destroy)

        self.clock_tracker = None
        self.tz_monitor = None

