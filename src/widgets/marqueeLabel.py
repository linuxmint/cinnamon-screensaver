#! /usr/bin/python3

from gi.repository import Gtk, GObject, GLib

from util import trackers

class _fixedViewport(Gtk.Viewport):
    def __init__(self):
        super(_fixedViewport, self).__init__()

        self.set_shadow_type(Gtk.ShadowType.NONE)

    def do_get_preferred_width(self):
        return (300, 300)

class MarqueeLabel(Gtk.Stack):
    # time->position mapping
    PATTERN = [( 0.0, 0.0),
               ( 2.0, 0.0),
               (10.0, 1.0),
               (12.0, 1.0),
               (15.0, 0.0)]

    LENGTH = len(PATTERN)

    def __init__(self, text):
        super(MarqueeLabel, self).__init__()

        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_transition_duration(300)

        self.tick_id = 0

        self.current = self._make_label(text)

        self.add(self.current)
        self.set_visible_child(self.current)

    def _make_label(self, text):
        vp = _fixedViewport()

        label = Gtk.Label(text)
        label.set_halign(Gtk.Align.START)

        vp.add(label)
        vp.show_all()

        return vp

    def set_text(self, text):
        if self.current.get_child().get_text() == text:
            return

        self.cancel_tick()

        self.queued = self._make_label(text)

        self.add(self.queued)
        self.set_visible_child(self.queued)

        tmp = self.current
        self.current = self.queued
        self.queued = None

        GObject.idle_add(tmp.destroy)

        if not self.current.get_realized():
            trackers.con_tracker_get().connect(self.current,
                                               "realize",
                                               self.on_current_realized)
        else:
            GObject.idle_add(self._marquee_idle)

    def on_current_realized(self, widget, data=None):
        GObject.idle_add(self._marquee_idle)

        trackers.con_tracker_get().disconnect(widget,
                                              "realize",
                                              self.on_current_realized)

    def cancel_tick(self):
        if self.tick_id > 0:
            self.remove_tick_callback(self.tick_id)
            self.tick_id = 0

    def _marquee_idle(self):
        self.hadjust = self.current.get_hadjustment()

        if (self.hadjust.get_upper() == self.hadjust.get_page_size()) == self.get_allocated_width():
            return False

        self.start_time = self.get_frame_clock().get_frame_time()
        self.end_time = self.start_time + (self.PATTERN[self.LENGTH - 1][0] * 1000 * 1000) # sec to ms to μs

        if self.tick_id == 0:
            self.tick_id = self.add_tick_callback(self._on_marquee_tick)

        self._marquee_step(self.start_time)

        return GLib.SOURCE_REMOVE

    def _on_marquee_tick(self, widget, clock, data=None):
        now = clock.get_frame_time()

        self._marquee_step(now)

        if now >= self.end_time:
            self.start_time = self.end_time
            self.end_time += (self.PATTERN[self.LENGTH - 1][0] * 1000 * 1000) # sec to ms to μs

        return GLib.SOURCE_CONTINUE

    def interpolate_point(self, now):
        point = ((now - self.start_time) / 1000 / 1000)

        i = 0
        while i < self.LENGTH:
            cindex, cval = self.PATTERN[i]

            if point > cindex:
                i += 1
                continue

            if point == cindex:
                return cval

            pindex, pval = self.PATTERN[i - 1]
            diff = cval - pval
            duration = cindex - pindex

            ratio = diff / duration
            additive = (point - pindex) * ratio
            return pval + additive

    def _marquee_step(self, now):
        if now < self.end_time:
            t = self.interpolate_point(now)
        else:
            t = self.PATTERN[self.LENGTH - 1][1]

        new_position = ((self.hadjust.get_upper() - self.hadjust.get_page_size()) * t)

        self.hadjust.set_value(new_position)
        self.queue_draw()
