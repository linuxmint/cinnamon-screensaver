#! /usr/bin/python3

from gi.repository import CinnamonDesktop, GLib, Gtk, Gio
import random

from util import utils, trackers, settings
from baseWindow import BaseWindow

CLOCK_POSITIONING_TIMEOUT = 5
ALIGNMENTS = [int(Gtk.Align.START), int(Gtk.Align.END), int(Gtk.Align.CENTER)]

class ClockWidget(BaseWindow):
    def __init__(self, screen, away_message=None, initial_monitor=0):
        super(ClockWidget, self).__init__()
        self.screen = screen
        # self.set_name("clock")
        self.get_style_context().add_class("clock")

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        self.current_monitor = initial_monitor

        self.away_message = away_message

        self.label = Gtk.Label()
        self.label.show()
        self.add(self.label)

        self.clock_tracker = CinnamonDesktop.WallClock()

        trackers.con_tracker_get().connect(self.clock_tracker,
                                           "notify::clock",
                                           self.on_clock_changed)

        tz = Gio.File.new_for_path(path="/etc/localtime")
        self.tz_monitor = tz.monitor_file(0, None)

        trackers.con_tracker_get().connect(self.tz_monitor,
                                           "changed",
                                           self.on_tz_changed)

        self.update_clock()

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

    def start_positioning(self):
        trackers.timer_tracker_get().cancel("clock-positioning")
        trackers.timer_tracker_get().start_seconds("clock-positioning",
                                                   CLOCK_POSITIONING_TIMEOUT,
                                                   self.positioning_callback)

    def stop_positioning(self):
        trackers.timer_tracker_get().cancel("clock-positioning")

    def positioning_callback(self):
        self.unreveal()
        self.queue_resize()

        trackers.timer_tracker_get().start("align-clock-timeout",
                                           self.REVEALER_DURATION + 10,
                                           self.align_clock)

        return True

    def align_clock(self):
        current_halign = int(self.get_halign())
        horizontal = current_halign

        current_valign = int(self.get_valign())
        vertical = current_valign

        while horizontal == current_halign:
            horizontal = ALIGNMENTS[random.randint(0, 2)]
        while vertical == current_valign:
            vertical = ALIGNMENTS[random.randint(0, 2)]

        self.set_halign(Gtk.Align(horizontal))
        self.set_valign(Gtk.Align(vertical))

        if self.screen.get_n_monitors() > 1:
            new_monitor = self.current_monitor
            n = self.screen.get_n_monitors()

            while new_monitor == self.current_monitor:
                new_monitor = random.randint(0, n - 1)

            self.current_monitor = new_monitor

        self.queue_resize()

        self.reveal()

        trackers.timer_tracker_get().cancel("align-clock-timeout")

        return False

    def set_message(self, msg=""):
        self.away_message = msg
        self.update_clock()



