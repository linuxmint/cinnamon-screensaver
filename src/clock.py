#!/usr/bin/python3

from gi.repository import CinnamonDesktop, GLib, Gtk, Gio, Pango

from util import utils, trackers, settings
from baseWindow import BaseWindow
from floating import Floating

MAX_WIDTH = 320
MAX_WIDTH_LOW_RES = 200

class ClockWidget(Floating, BaseWindow):
    """
    ClockWidget displays the time and away message on the screen.

    It is a child of the Stage's GtkOverlay, and its placement is
    controlled by the overlay's child positioning function.

    When not Awake, it positions itself around all monitors
    using a timer which randomizes its halign and valign properties
    as well as its current monitor.
    """
    def __init__(self, away_message=None, initial_monitor=0, low_res=False):
        super(ClockWidget, self).__init__(initial_monitor)
        self.get_style_context().add_class("clock")
        self.set_halign(Gtk.Align.START)

        self.set_property("margin", 6)

        self.clock = None
        self.low_res = low_res

        if not settings.get_show_clock():
            return

        self.away_message = away_message

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        box.show()

        self.label = Gtk.Label()
        self.label.show()
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.5, 0.5)

        box.pack_start(self.label, True, False, 6)

        self.msg_label = Gtk.Label()
        self.msg_label.show()
        self.msg_label.set_line_wrap(True)
        self.msg_label.set_alignment(0.5, 0.5)

        if self.low_res:
            self.msg_label.set_max_width_chars(50)
        else:
            self.msg_label.set_max_width_chars(80)

        box.pack_start(self.msg_label, True, True, 6)

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

        time_font = Pango.FontDescription.from_string(settings.get_time_font())
        date_font = Pango.FontDescription.from_string(settings.get_date_font())

        if self.low_res:
            time_size = time_font.get_size() * .66
            date_size = date_font.get_size() * .66
            time_font.set_size(int(time_size))
            date_font.set_size(int(date_size))

        time_format = ('<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>\n' +             \
                       '<b><span font_desc=\"%s\" foreground=\"#FFFFFF\">%s</span></b>')                \
            % (time_font.to_string(), time_format, date_font.to_string(), date_format)

        self.clock.set_format_string(time_format)

    def on_clock_changed(self, clock, pspec):
        self.update_clock()

    def on_tz_changed(self, monitor, file, other, event):
        self.update_clock()

    def update_clock(self):
        default_message = GLib.markup_escape_text (settings.get_default_away_message(), -1)
        font_message = Pango.FontDescription.from_string(settings.get_message_font())

        if self.low_res:
            msg_size = font_message.get_size() * .66
            font_message.set_size(int(msg_size))

        if self.away_message and self.away_message != "":
            user_name = utils.get_user_display_name()
            markup = ('<b><span font_desc=\"Ubuntu 14\" foreground=\"#CCCCCC\">%s</span></b>' +\
                      '\n<b><span font_desc=\"Ubuntu 10\" foreground=\"#ACACAC\">  ~ %s</span></b>\n ') %\
                     (self.away_message, user_name)
        else:
            markup = '<b><span font_desc=\"%s\" foreground=\"#CCCCCC\">%s</span></b>\n ' %\
                     (font_message.to_string(), default_message)

        self.label.set_markup(self.clock.get_clock())
        self.msg_label.set_markup(markup)

    def set_message(self, msg=""):
        if not self.clock:
            return

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
