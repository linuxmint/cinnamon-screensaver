#! /usr/bin/python3

from gi.repository import Gio, GObject, GLib

class BaseClient(GObject.GObject):
    """
    The base constructor for all of our generated GDBusProxies.

    This initializes and sets self.proxy, then fires on_client_setup_complete()
    or on_failure(), which the subclasses implement, depending on the outcome.

    These clients are technically one more level of abstraction than would be
    needed in a perfect world, where all dbus proxies work as they should and
    are supported properly by the actual providers they proxy for, but they
    provide a convenient and relatively clean way of implementing workarounds
    and alternate ways of retrieving or calculating values when the interface
    itself is broken in some way (this is common.)

    They also provide a bit of fault tolerance in cases where one or more of
    these providers do not exist on the bus, and we can provide sane default
    values for our widgets.
    """
    def __init__(self, bustype, proxy_class, service, path):
        """
        Asynchronously initialize the GDBusProxy - we'll call
        on_client_setup_complete() or on_failure() depending on this outcome.
        """
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
        except GLib.Error:
            self.proxy = None
            self.on_failure()

        Gio.bus_unwatch_name(self.watch_name_id)

    def _on_proxy_ready(self, object, result, data=None):
        self.proxy = self.proxy_class.new_finish(result)

        self.on_client_setup_complete()

    def ensure_proxy_alive(self):
        """
        Use this as a safety check to see if a given proxy is valid
        and owned.
        """
        return self.proxy and self.proxy.get_name_owner() != None

    def on_client_setup_complete(self):
        """
        Subclasses must implement this - to complete setup after self.proxy is
        successfully initialized.
        """
        print("You need to implement on_client_setup_complete(self) in your real client class")
        raise NotImplementedError

    def on_failure(self, *args):
        """
        Can be implemented by subclasses, but not necessary.  Nothing further is done anyhow
        if on_client_setup_complete() is never called.
        """
        pass
