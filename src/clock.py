#!/usr/bin/python3

from gi.repository import CinnamonDesktop, GLib, Gtk, Gio

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

        self.clock = CinnamonDesktop.WallClock()
        self.set_clock_format()

        trackers.con_tracker_get().connect(self.clock,
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

    def set_clock_format(self):
        date_format = ""
        time_format = ""

        if settings.get_use_custom_format():
            date_format = settings.get_custom_date_format()
            time_format = settings.get_custom_time_format()
        else:
            date_format = self.clock.get_default_date_format()
            time_format = self.clock.get_default_time_format()

            # %l is 12-hr hours, but it adds a space to 0-9, which looks bad here.
            # The '-' modifier tells the GDateTime formatter not to pad the value.
            time_format = time_format.replace('%l', '%-l')

        time_format = ('<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>\n' +             \
                       '<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>')                \
            % (settings.get_time_font(), time_format, settings.get_date_font(), date_format)

        self.clock.set_format_string(time_format)

    def on_clock_changed(self, clock, pspec):
        self.update_clock()

    def on_tz_changed(self, monitor, file, other, event):
        self.update_clock()

    def update_clock(self):
        default_message = GLib.markup_escape_text (settings.get_default_away_message(), -1)
        font_message = settings.get_message_font()

        if self.away_message and self.away_message != "":
            user_name = utils.get_user_display_name()
            markup = ('%s\n\n<b><span font_desc=\"Ubuntu 14\" foreground=\"#CCCCCC\">%s</span></b>' +\
                      '\n<b><span font_desc=\"Ubuntu 10\" foreground=\"#ACACAC\">  ~ %s</span></b>') %\
                     (self.clock.get_clock(), self.away_message, user_name)
        else:
            markup = '%s\n\n<b><span font_desc=\"%s\" foreground=\"#CCCCCC\">%s</span></b>' %\
                     (self.clock.get_clock(), font_message, default_message)

        self.label.set_markup(markup)
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.5, 0.5)

    def set_message(self, msg=""):
        self.away_message = msg
        self.update_clock()

    def on_destroy(self, data=None):
        trackers.con_tracker_get().disconnect(self.clock,
                                              "notify::clock",
                                              self.on_clock_changed)

        trackers.con_tracker_get().disconnect(self.tz_monitor,
                                              "changed",
                                              self.on_tz_changed)

        trackers.con_tracker_get().disconnect(self,
                                              "destroy",
                                              self.on_destroy)

        self.clock = None
        self.tz_monitor = None
