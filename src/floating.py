#!/usr/bin/python3

from gi.repository import Gtk
import random
import status

from util import trackers
from util import settings

class PositionInfo():
    def __init__(self, monitor, halign, valign):
        self.monitor = monitor
        self.halign = halign
        self.valign = valign

class Floating:
    def __init__(self, initial_monitor=0, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER):
        super(Floating, self).__init__()
        self.awake_position = PositionInfo(initial_monitor, halign, valign)
        self.next_position = self.awake_position
        self.current_monitor = initial_monitor
        self.apply_next_position()

    def start_positioning(self):
        self.apply_next_position()
        self.show()

    def set_next_position(self, monitor, halign, valign):
        self.next_position = PositionInfo(monitor, halign, valign)

    def apply_next_position(self):
        self.current_monitor = self.next_position.monitor
        self.set_halign(self.next_position.halign)
        self.set_valign(self.next_position.valign)

    def set_awake_position(self, monitor):
        self.awake_position.monitor = monitor
        self.next_position = self.awake_position
