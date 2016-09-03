#! /usr/bin/python3

from gi.repository import Gtk, GObject, GLib
from util import trackers

class BlinkingLabel(Gtk.Label):
    def __init__(self, text, rate):
        super(BlinkingLabel, self).__init__()

        self.rate = rate

        self.current_opacity = 1.0
        self.target_opacity = 0.0

        self.blinking = False

        self.tick_id = 0
        self.stop_blinking = False

        self.start_time = 0
        self.end_time = 0

        trackers.con_tracker_get().connect(self,
                                           "realize",
                                           self.on_realized)

    def on_realized(self, widget, data=None):
        if self.blinking and self.tick_id == 0:
            GObject.idle_add(self._blink_idle)

        trackers.con_tracker_get().disconnect(self,
                                              "realize",
                                              self.on_realized)

    def set_blinking(self, blinking):
        self.blinking = blinking

        if blinking and self.tick_id == 0:
            GObject.idle_add(self._blink_idle)
        elif self.tick_id > 0:
            self.stop_blinking = True

    def get_blinking(self, blinking):
        return self.tick_id > 0

    def cancel(self):
        if self.tick_id > 0:
            self.remove_tick_callback(self.tick_id)
            self.tick_id = 0

        self.stop_blinking = False

    def _blink_idle(self):
        self.current_opacity = self.get_opacity()

        if self.current_opacity == 1.0:
            self.target_opacity = 0.0
        else:
            self.target_opacity = 1.0

        if not self.get_visible():
            self.set_visible(True)

        if self.get_mapped():
            self.start_time = self.get_frame_clock().get_frame_time()
            self.end_time = self.start_time + (self.rate * 1000) # ms to microsec

            if self.tick_id == 0:
                self.tick_id = self.add_tick_callback(self._on_blink_tick)

            self._blink_step(self.start_time)

        return GLib.SOURCE_REMOVE

    def _on_blink_tick(self, widget, clock, data=None):
        now = clock.get_frame_time()

        self._blink_step(now)

        if self.stop_blinking:
            self.target_opacity = 1.0

        if self.current_opacity == self.target_opacity:
            if self.stop_blinking and self.current_opacity == 1.0:
                self.cancel()
                return GLib.SOURCE_REMOVE

            self.start_time = self.end_time
            self.end_time += (self.rate * 1000)
            self.reverse_direction()

        return GLib.SOURCE_CONTINUE

    def _blink_step(self, now):
        if now < self.end_time:
            if self.current_opacity < self.target_opacity:
                t = (now - self.start_time) / (self.end_time - self.start_time)
            else:
                t = 1.0 - ((now - self.start_time) / (self.end_time - self.start_time))
        else:
            t = self.target_opacity

        self.current_opacity = t
        self.set_opacity(self.current_opacity)
        self.queue_draw()

    def reverse_direction(self):
        if self.target_opacity == 0.0:
            self.target_opacity = 1.0
        else:
            self.target_opacity = 0.0
