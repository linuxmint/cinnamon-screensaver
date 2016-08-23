#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib

class BaseClient(GObject.GObject):
    def __init__(self, bustype, proxy_class, service, path):
        super(BaseClient, self).__init__()

        self.proxy_class = proxy_class
        self.path = path

        self.proxy = None

        self.watch_name_id = Gio.bus_watch_name(bustype,
                                                service,
                                                Gio.BusNameWatcherFlags.NONE,
                                                self._on_appeared,
                                                self.on_failure)

    def _on_appeared(self, connection, name, name_owner, data=None):
        try:
            self.proxy_class.new(connection,
                                 Gio.DBusProxyFlags.NONE,
                                 name,
                                 self.path,
                                 None,
                                 self._on_proxy_ready)
        except GLib.Error as e:
            print("Could not acquire org.gnome.SessionManager proxy - idle listening is disabled", e)
            self.proxy = None
            self.on_failure()

        Gio.bus_unwatch_name(self.watch_name_id)

    def _on_proxy_ready(self, object, result, data=None):
        self.proxy = self.proxy_class.new_finish(result)

        self.on_client_setup_complete()

    def on_client_setup_complete(self):
        print("You need to implement on_client_setup_complete(self) in your real client class")
        raise NotImplementedError

    def on_failure(self, *args):
        pass
