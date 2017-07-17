#!/usr/bin/python3

from gi.repository import Gtk
import random
import status

from util import trackers
from util import settings

POSITIONING_TIMEOUT = 30
ALIGNMENTS = [int(Gtk.Align.START), int(Gtk.Align.END), int(Gtk.Align.CENTER)]

class Floating:
    def __init__(self, initial_monitor=0):
        super(Floating, self).__init__()
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.current_monitor = initial_monitor

    def start_positioning(self):
        self.reveal()
        if settings.get_allow_floating():
            trackers.timer_tracker_get().cancel(str(self) + "positioning")
            trackers.timer_tracker_get().start_seconds(str(self) + "positioning",
                                                       POSITIONING_TIMEOUT,
                                                       self.positioning_callback)

    def stop_positioning(self):
        if settings.get_allow_floating():
            trackers.timer_tracker_get().cancel(str(self) + "positioning")
            trackers.timer_tracker_get().cancel(str(self) + "align-timeout")

    def positioning_callback(self):
        self.unreveal()
        self.queue_resize()

        trackers.timer_tracker_get().start(str(self) + "align-timeout",
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

        if status.screen.get_n_monitors() > 1:
            new_monitor = self.current_monitor
            n = status.screen.get_n_monitors()

            while new_monitor == self.current_monitor:
                new_monitor = random.randint(0, n - 1)

            self.current_monitor = new_monitor

        self.queue_resize()

        self.reveal()

        trackers.timer_tracker_get().cancel(str(self) + "align-timeout")

        return False


