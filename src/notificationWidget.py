#! /usr/bin/python3

from gi.repository import Gtk, Gdk, GLib
import dbus

import trackers

class NotificationWidget(Gtk.Box):
    def __init__(self):
        super(NotificationWidget, self).__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.get_style_context().add_class("notificationwidget")

        self.set_size_request(50, -1)

        self.notification_count = 0

        self.label = Gtk.Label.new("0")
        self.pack_start(self.label, False, False, 4)

        self.image = Gtk.Image.new_from_icon_name("screensaver-notification-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.pack_end(self.image, False, False, 4)

        session_bus = dbus.SessionBus()
        session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
        session_bus.add_message_filter(self.on_notification_observed)

    def on_notification_observed(self, bus, message):
        self.notification_count += 1

        self.update_label()

    def update_label(self):
        self.label.set_text(str(self.notification_count))

