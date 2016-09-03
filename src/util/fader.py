#! /usr/bin/python3

from gi.repository import GLib, GObject

class Fader:
    def __init__(self, widget):
        self.widget = widget
        self.finished_cb = None

        self.current_opacity = 0.0
        self.target_opacity = 0.0

        self.tick_id = 0

        self.start_time = 0
        self.end_time = 0

    def fade_in(self, ms, finished_cb=None):
        GObject.idle_add(self._fade_in_idle, ms, finished_cb)

    def fade_out(self, ms, finished_cb=None):
        GObject.idle_add(self._fade_out_idle, ms, finished_cb)

    def cancel(self):
        if self.tick_id > 0:
            self.widget.remove_tick_callback(self.tick_id)
            self.tick_id = 0

    def _fade_in_idle(self, ms, finished_cb=None):
        self.finished_cb = finished_cb
        self.current_opacity = self.widget.get_opacity()
        self.target_opacity = 1.0

        if not self.widget.get_visible():
            self.widget.set_visible(True)

        if self.widget.get_mapped():
            self.start_time = self.widget.get_frame_clock().get_frame_time()
            self.end_time = self.start_time + (ms * 1000) # ms to microsec

            if self.tick_id == 0:
                self.tick_id = self.widget.add_tick_callback(self._on_frame_tick_fade_in)

            self._fade_in_step(self.start_time)

        return GLib.SOURCE_REMOVE

    def _fade_out_idle(self, ms, finished_cb=None):
        self.finished_cb = finished_cb
        self.current_opacity = self.widget.get_opacity()
        self.target_opacity = 0.0

        if self.widget.get_mapped():
            self.start_time = self.widget.get_frame_clock().get_frame_time()
            self.end_time = self.start_time + (ms * 1000) # ms to microsec

            if self.tick_id == 0:
                self.tick_id = self.widget.add_tick_callback(self._on_frame_tick_fade_out)

            self._fade_out_step(self.start_time)

        return GLib.SOURCE_REMOVE

    def _on_frame_tick_fade_in(self, widget, clock, data=None):
        now = clock.get_frame_time()

        self._fade_in_step(now)

        if self.current_opacity == self.target_opacity:
            self.tick_id = 0
            self.finished_cb()
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def _fade_in_step(self, now):
        if now < self.end_time:
            t = (now - self.start_time) / (self.end_time - self.start_time)
        else:
            t = 1.0

        self.current_opacity = t

        self.widget.set_opacity(self.current_opacity)
        self.widget.queue_draw()

    def _on_frame_tick_fade_out(self, widget, clock, data=None):
        now = clock.get_frame_time()

        self._fade_out_step(now)

        if self.current_opacity == self.target_opacity:
            self.tick_id = 0
            self.finished_cb()
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def _fade_out_step(self, now):
        if now < self.end_time:
            t = 1.0 - ((now - self.start_time) / (self.end_time - self.start_time))
        else:
            t = 0.0

        self.current_opacity = t

        self.widget.set_opacity(self.current_opacity)
        self.widget.queue_draw()
