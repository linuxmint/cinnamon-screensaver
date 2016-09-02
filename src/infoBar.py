#! /usr/bin/python3

from gi.repository import Gtk

import status
from util import utils, trackers
from baseWindow import BaseWindow
from notificationWidget import NotificationWidget
from powerWidget import PowerWidget

class InfoBar(BaseWindow):
    def __init__(self, screen):
        super(InfoBar, self).__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        self.screen = screen
        self.monitor_index = utils.get_primary_monitor()

        self.update_geometry()

        self.show_power = False
        self.show_notifications = False

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_halign(Gtk.Align.FILL)
        self.box.get_style_context().add_class("topbar")
        self.box.get_style_context().add_class("infobar")
        self.add(self.box)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(hbox, False, False, 6)

        self.notification_widget = NotificationWidget()
        self.notification_widget.set_no_show_all(True)
        hbox.pack_start(self.notification_widget, True, True, 3)
        self.notification_widget.connect("notification", self.on_notification_received)

        self.power_widget = PowerWidget()
        self.power_widget.set_no_show_all(True)
        hbox.pack_start(self.power_widget, True, True, 3)

        self.show_all()

    def on_notification_received(self, obj):
        self.update_revealed()

    def update_revealed(self):
        do_reveal = False

        self.show_power = self.power_widget.should_show()
        self.show_notifications = self.notification_widget.should_show()

        # Determine if we want to show all the time or only when status.Awake

        if status.Awake:
            if self.show_power or self.show_notifications:
                do_reveal = True
        elif status.Active and not status.PluginRunning:
            if self.show_notifications:
                do_reveal = True

       
        if do_reveal:
            self.power_widget.set_visible(self.show_power)
            self.notification_widget.set_visible(self.show_notifications)
            self.reveal()
        else:
            self.unreveal()
            trackers.con_tracker_get().connect(self,
                                               "notify::child-revealed",
                                               self.after_unreveal)

    def after_unreveal(self, obj, pspec):
        self.power_widget.set_visible(self.show_power)
        self.notification_widget.set_visible(self.show_notifications)
        trackers.con_tracker_get().disconnect(self,
                                              "notify::child-revealed",
                                              self.after_unreveal)

