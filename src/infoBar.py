#! /usr/bin/python3

import gi
gi.require_version('Cvc', '1.0')

from gi.repository import Gtk

import utils
from baseWindow import BaseWindow
from notificationWidget import NotificationWidget

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

        # self.attention_widget = AttentionWidget()
        # self.box.pack_end(self.attention_widget, False, False, 6)

        self.show_all()
