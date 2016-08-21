#! /usr/bin/python3

from gi.repository import Gtk, Gdk, GLib, GObject
import dbus

import trackers
import status

class NotificationWidget(Gtk.Frame):
    __gsignals__ = {
        "notification": (GObject.SignalFlags.RUN_LAST, None, ()),
    }
    def __init__(self):
        super(NotificationWidget, self).__init__()
        self.get_style_context().add_class("notificationwidget")

        self.set_size_request(50, -1)

        self.notification_count = 0

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(box)

        self.label = Gtk.Label.new("0")
        box.pack_start(self.label, False, False, 4)

        self.image = Gtk.Image.new_from_icon_name("screensaver-notification-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        box.pack_end(self.image, False, False, 4)

        self.connect("destroy", self.on_destroy)

        self.session_bus = dbus.SessionBus()
        self.session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
        self.session_bus.add_message_filter(self.on_notification_observed)

    def on_notification_observed(self, bus, message):
        self.notification_count += 1

        self.update_label()

        self.emit("notification")

    def update_label(self):
        self.label.set_text(str(self.notification_count))

    def on_destroy(self, widget):
        # remove_message_filter fails.. why?
        self.session_bus.remove_message_filter(self.on_notification_observed)
        # but this works, which also apparently cleans up any remaining refs so we can dispose properly
        self.session_bus.remove_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")

