#!/usr/bin/python3

from gi.repository import GObject, GLib

DEBUG_TIMERS=False
DEBUG_SIGNALS=False

def _debug(*args):
    first = True
    output = ""
    for arg in args:
        if not first:
            output += ": "
        first = False

        output += str(arg)
    print(output)

def debug_timers(*args):
    if DEBUG_TIMERS:
        _debug(*args)

def debug_sigs(*args):
    if DEBUG_SIGNALS:
        _debug(*args)


class TimerTracker:
    """
    Utility class for tracking mainloop timers - they are stored as
    [name : timeout id] pairs.  This is simply a way of managing them
    without having to individually track source ids.
    """
    def __init__(self):
        self.timers = {}

    def do_callback(self, callback, name, *args):
        ret = callback(*args)

        if ret:
            return True

        self.cancel(name)
        return False

    def start(self, name, duration, callback, *args):
        self.cancel(name)
        timeout_id = GObject.timeout_add(duration, self.do_callback, callback, name, *args)
        debug_timers("adding timer of name", name, "duration (sec)", duration / 1000.0, "callback", str(callback), "id", timeout_id)

        self.timers[name] = timeout_id

    def start_seconds(self, name, duration, callback, *args):
        self.cancel(name)
        timeout_id = GObject.timeout_add_seconds(duration, self.do_callback, callback, name, *args)
        debug_timers("adding timer of name", name, "duration (sec)", duration, "callback", str(callback), "id", timeout_id)

        self.timers[name] = timeout_id

    def add_idle(self, name, callback, *args):
        self.cancel(name)
        idle_id = GObject.idle_add(self.do_callback, callback, name, *args)
        debug_timers("adding idle callback of name", name, "callback", str(callback), "id", idle_id)

        self.timers[name] = idle_id

    def cancel(self, name):
        try:
            if self.timers[name]:
                if GLib.MainContext.default().find_source_by_id(self.timers[name]):
                    GObject.source_remove(self.timers[name])
                    debug_timers("cancel succeeded for", name, "source id", self.timers[name])
                else:
                    debug_timers("cancel failed (not a valid id) for", name, "source id", self.timers[name])

                del self.timers[name]
        except KeyError:
            pass

    def dump_timer_list(self):
        print("Timer tracker dump:")

        i = 0

        for timer in self.timers:
            print(timer)
            i += 1

        print("%d timers total" % i)


timer_tracker = TimerTracker()

def timer_tracker_get():
    global timer_tracker
    return timer_tracker

class ConnectionTracker:
    """
    Utility class for tracking GObject signal connections.  It is tracked in
    [ name : (source id, instance) ] pairs.  The name is generated as a magic
    string consisting of "instance hash+signal name+callback hash".

    As a convenience, we hang a weak reference on both the signal caller's instance
    as well as the callback's instance.  If either of these instances are destroyed
    we will receive a notification and automatically attempt to disconnect the original
    signal connection.  This will frequently fail, depending on what gets destroyed first
    (destruction of the source instance will usually mean implicit destruction of the
    callback.)
    """
    def __init__(self):
        self.connections = {}

    def _name(self, instance, signal, callback):
        name = "%s-%s-%s" % (str(hash(instance)), signal, str(hash(callback)))

        return name

    def _disconnect_by_name(self, name):
        try:
            if self.connections[name]:
                (source_id, instance) = self.connections[name]

                if GObject.signal_handler_is_connected(instance, source_id):
                    instance.disconnect(source_id)
                    debug_sigs("_disconnect_by_name succeeded for", name, "id", source_id)
                else:
                    debug_sigs("_disconnect_by_name failed (not a valid id) for", name, "id", source_id)

                del self.connections[name]

        except KeyError as e:
            debug_sigs("_disconnect_by_name failed (not being tracked or already disco'd) for", name, str(e))

    def _connect_to_dispose(self, name, instance, callback):
        callback_instance = None
        try:
            callback_instance = callback.__self__
            if callback_instance and isinstance(callback_instance, GObject.GObject):
                callback_instance.weak_ref(self._cleanup_disposed, name, "callback_instance")
                debug_sigs("_connect_to_dispose (callback_instance)", name)
        except:
            pass

        instance.weak_ref(self._cleanup_disposed, name, "instance")
        debug_sigs("_connect_to_dispose (instance)", name)

    def _cleanup_disposed(self, name, type_name):
        debug_sigs("_cleanup_disposed", type_name, name)
        self._disconnect_by_name(name)

    def connect(self, instance, signal, callback, *data):
        """
        Wrapper for instance.connect()
        """
        name = self._name(instance, signal, callback)
        self._disconnect_by_name(name)

        if data:
            source_id = instance.connect(signal, callback, *data)
        else:
            source_id = instance.connect(signal, callback)

        self.connections[name] = (source_id, instance)
        debug_sigs("connected", name, "id", source_id)

        self._connect_to_dispose(name, instance, callback)

    def connect_after(self, instance, signal, callback, *data):
        """
        Wrapper for instance.connect_after()
        """
        name = self._name(instance, signal, callback)
        self._disconnect_by_name(name)

        if data:
            source_id = instance.connect_after(signal, callback, data)
        else:
            source_id = instance.connect_after(signal, callback)

        self.connections[name] = (source_id, instance)
        debug_sigs("connected after", name, "id", source_id)

        self._connect_to_dispose(name, instance, callback)

    def handler_block(self, instance, signal, callback):
        """
        Wrapper for g_signal_handler_block().
        """
        name = self._name(instance, signal, callback)

        if self.connections[name]:
            self.connections[name][1].handler_block(self.connections[name][0])

    def handler_unblock(self, instance, signal, callback):
        """
        Wrapper for g_signal_handler_unblock()
        """
        name = self._name(instance, signal, callback)

        if self.connections[name]:
            self.connections[name][1].handler_unblock(self.connections[name][0])

    def disconnect(self, instance, signal, callback):
        """
        Wrapper for instance.disconnect()
        """
        name = self._name(instance, signal, callback)
        debug_sigs("disconnect", name)

        self._disconnect_by_name(name)

    def dump_connections_list(self):
        print("Connection tracker dump:")

        i = 0

        for connection in self.connections:
            print(connection)
            i += 1

        print("%d connections total" % i)

connection_tracker = ConnectionTracker()

def con_tracker_get():
    global connection_tracker
    return connection_tracker
