#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib, CScreensaver

from dbusdepot.baseClient import BaseClient


class NotificationClient(BaseClient):
    __gsignals__ = {
        'notification-received': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    NOTIFICATION_SERVICE = "org.freedesktop.Notifications"
    NOTIFICATION_PATH    = "/org/freedesktop/Notifications"

    DBUS_SERVICE = "org.freedesktop.DBus"
    DBUS_PATH = "/org/freedesktop/DBus"
    DBUS_INTERFACE = "org.freedesktop.DBus"

    def __init__(self):
        super(NotificationClient, self).__init__(Gio.BusType.SESSION,
                                                 CScreensaver.NotificationsProxy,
                                                 self.NOTIFICATION_SERVICE,
                                                 self.NOTIFICATION_PATH)

    def on_client_setup_complete(self):
        self.connection = self.proxy.get_connection()

        Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION,
                                  Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES | Gio.DBusProxyFlags.DO_NOT_CONNECT_SIGNALS,
                                  None,
                                  self.DBUS_SERVICE,
                                  self.DBUS_PATH,
                                  self.DBUS_INTERFACE,
                                  None,
                                  self.on_dbus_proxy_ready)

    def on_dbus_proxy_ready(self, source, res, data=None):
        self.dbus_proxy = Gio.DBusProxy.new_for_bus_finish(res)

        self.dbus_proxy.call_sync("AddMatch",
                                  GLib.Variant("(s)",
                                  ("eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'",)),
                                  Gio.DBusCallFlags.NONE,
                                  -1,
                                  None)

        self.filter_id = self.proxy.get_connection().add_filter(self.filter_callback, None)

    def filter_callback(self, connection, message, incoming, data=None):
        if message.get_message_type() == Gio.DBusMessageType.METHOD_CALL:
            if message.get_interface() == "org.freedesktop.Notifications":
                if message.get_member() == "Notify":
                    self.emit("notification-received")

        return message.copy()

    def on_failure(self, *args):
        print("Failed to establish a dbus messaging monitor for notifications.  A notification count will not be displayed.")