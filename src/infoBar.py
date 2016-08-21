#! /usr/bin/python3

from gi.repository import Gtk

import utils
import status
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

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.get_style_context().add_class("topbar")
        self.box.get_style_context().add_class("infobar")
        self.add(self.box)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(hbox, False, False, 6)

        self.notification_widget = NotificationWidget()
        hbox.pack_start(self.notification_widget, False, False, 6)
        self.notification_widget.connect("notification", self.on_notification_received)

        self.power_widget = PowerWidget()
        hbox.pack_start(self.power_widget, False, False, 6)
        self.power_widget.connect("power-state-changed", self.on_power_state_changed)

        self.show_all()

    def on_notification_received(self, obj):
        if not status.PluginRunning:
            self.reveal()

    def on_power_state_changed(self, obj):
        if self.power_widget.should_show():
            self.power_widget.set_visible(True)

    # Overrides BaseWindow.reveal()
    def reveal(self):
        do_reveal = False

        if self.notification_widget.should_show(): 
            self.notification_widget.set_visible(True)
            do_reveal = True
        else:
            self.notification_widget.set_visible(False)

        if self.power_widget.should_show():
            self.power_widget.set_visible(True)
            do_reveal = True

        # if self.attention_widget.needs_attention:
        #     self.attention_widget.set_visible(True)
        #     do_reveal = True
        # else:
        #     self.attention_widget.set_visible(False)

        if do_reveal:
            super(InfoBar, self).reveal()

