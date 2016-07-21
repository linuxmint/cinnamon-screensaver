#! /usr/bin/python3
# coding: utf-8


import gi
gi.require_version('Gkbd', '3.0')
gi.require_version('AccountsService', '1.0')
from gi.repository import Gtk, Gdk, Gkbd, AccountsService, GObject

from authenticator import PAMServiceProxy
import utils
import os
import trackers
from grabHelper import GrabHelper
from baseWindow import BaseWindow
import settings
import status

# This segfaults if called more than once??
kbd_config = None
acc_service = None

class UnlockDialog(BaseWindow):
    __gsignals__ = {
        'inhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'uninhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-success': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-failure': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self):
        super(UnlockDialog, self).__init__()

        self.grab_helper = GrabHelper()

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_size_request(400, -1)

        self.frame = Gtk.Frame()

        self.frame.get_style_context().add_class("button")

        self.real_name = None
        self.user_name = None

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame.add(self.box)

        self.add(self.frame)

        self.box.set_margin_start(6)
        self.box.set_margin_end(6)
        self.box.set_margin_top(6)
        self.box.set_margin_bottom(6)

        hbox_user = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.box.pack_start(hbox_user, False, False, 6)

        self.face_image = Gtk.Image()
        hbox_user.pack_start(self.face_image, True, True, 0)
        self.face_image.set_alignment(1.0, 0.5)

        vbox_user = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox_user.pack_start(vbox_user, True, True, 0)
        vbox_user.set_border_width(6)

        self.realname_label = Gtk.Label(None)
        self.realname_label.set_alignment(0, 0.5)
        vbox_user.pack_start(self.realname_label, True, True, 0)

        self.username_label = Gtk.Label(None)
        self.username_label.set_alignment(0, 0)
        vbox_user.pack_start(self.username_label, True, True, 0)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE,
                               transition_duration=100)
        self.stack.show()

        self.box.pack_start(self.stack, False, False, 6)

        hbox_pass = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.stack.add_named(hbox_pass, "entry")

        self.spinner = Gtk.Spinner()
        self.stack.add_named(self.spinner, "spinner")

        self.stack.set_visible_child(hbox_pass)

        # Password prompt

        self.auth_prompt_label = Gtk.Label.new_with_mnemonic(_("_Password:"))
        self.auth_prompt_label.set_alignment(0.5, 0.5)
        hbox_pass.pack_start(self.auth_prompt_label, False, False, 6)

        self.auth_prompt_entry = Gtk.Entry()
        self.auth_prompt_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.auth_prompt_entry.set_visibility(False)
        hbox_pass.pack_start(self.auth_prompt_entry, True, True, 0)
        self.auth_prompt_entry.set_can_default(True)
        self.auth_prompt_label.set_mnemonic_widget(self.auth_prompt_entry)

        trackers.con_tracker_get().connect(self.auth_prompt_entry,
                                           "changed",
                                           self.on_auth_prompt_entry_text_changed)

        trackers.con_tracker_get().connect(self.auth_prompt_entry,
                                           "button-press-event",
                                           self.on_auth_prompt_entry_button_press)

        trackers.con_tracker_get().connect(self.auth_prompt_entry,
                                           "activate",
                                           self.on_auth_enter_key)

        # Keyboard layout button

        self.kbd_layout_indicator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox_pass.pack_start(self.kbd_layout_indicator, False, False, 0)

        # Status

        vbox_status = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.box.pack_start(vbox_status, True, True, 6)

        # Caps warning

        self.capslock_label = Gtk.Label("")
        self.capslock_label.set_alignment(0.5, 0.5)
        vbox_status.pack_start(self.capslock_label, False, False, 0)

        # Status Text

        self.auth_message_label = Gtk.Label(None)
        self.auth_message_label.set_alignment(0.5, 0.5)
        vbox_status.pack_start(self.auth_message_label, False, False, 0)

        # Buttons

        self.action_area = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        self.action_area.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        self.action_area.show()

        self.box.pack_start(self.action_area, False, True, 0)
        self.action_area.show()

        self.auth_switch_button = self.add_button(_("S_witch User…"))
        trackers.con_tracker_get().connect(self.auth_switch_button,
                                           "clicked",
                                           self.on_switch_user_clicked)
        self.auth_switch_button.set_visible(settings.get_user_switch_enabled())

        self.auth_logout_button = self.add_button(_("Log _Out"))
        trackers.con_tracker_get().connect(self.auth_logout_button,
                                           "clicked",
                                           self.on_logout_clicked)
        self.auth_logout_button.set_visible(settings.get_logout_enabled())


        self.auth_unlock_button = self.add_button(_("_Unlock"))
        self.auth_unlock_button.set_sensitive(False)
        trackers.con_tracker_get().connect(self.auth_unlock_button,
                                           "clicked",
                                           self.on_unlock_clicked)
        self.auth_unlock_button.set_visible(True)

        self.real_name = utils.get_user_display_name()
        self.user_name = utils.get_user_name()

        self.update_realname_label()
        self.update_username_label()

        self.setup_kbd_layout_button()

        global acc_service

        if acc_service is not None:
            self.on_accounts_service_loaded(acc_service, None)
        else:
            acc_service = AccountsService.UserManager.get_default().get_user(self.user_name)

        trackers.con_tracker_get().connect(acc_service,
                                           "notify::is-loaded",
                                           self.on_accounts_service_loaded)

        self.keymap = Gdk.Keymap.get_default()

        trackers.con_tracker_get().connect(self.keymap,
                                           "state-changed",
                                           self.keymap_handler)

        trackers.con_tracker_get().connect_after(self,
                                                 "notify::child-revealed",
                                                 self.on_revealed)

        self.auth_proxy = PAMServiceProxy()

        self.show_all()

    def cancel(self):
        self.unreveal()
        self.auth_message_label.set_text("")

    def on_revealed(self, widget, child):
        if self.get_child_revealed():
            self.keymap_handler(self.keymap)
            self.grab_helper.release()
            self.grab_helper.grab_window(self.get_window(), False)
            self.auth_prompt_entry.grab_focus_without_selecting()
        else:
            self.auth_prompt_entry.set_text("")

    def entry_is_focus(self):
        return self.auth_prompt_entry.is_focus()

    def queue_key_event(self, event):
        if not self.auth_prompt_entry.get_realized():
            self.auth_prompt_entry.realize()

        self.auth_prompt_entry.event(event)
        self.auth_prompt_entry.set_position(-1)

    def keymap_handler(self, keymap):
        if keymap.get_caps_lock_state():
            self.capslock_label.set_text(_("You have the Caps Lock key on."))
        else:
            self.capslock_label.set_text("")

    def add_button(self, text):
        button = Gtk.Button.new_from_stock(text)
        button.set_focus_on_click(False)
        button.set_can_default(True)
        button.set_no_show_all(True)
        self.action_area.pack_end(button, False, True, 0)
        return button

    def on_accounts_service_loaded(self, service, param):
        self.real_name = service.get_real_name()
        self.update_realname_label()

        for path in [os.path.join(service.get_home_dir(), ".face"),
                     service.get_icon_file(),
                     "/usr/share/cinnamon/faces/user-generic.png"]:
            if os.path.exists(path):
                self.face_image.set_from_file(path)
                break

    def on_auth_prompt_entry_text_changed(self, editable):
        self.auth_unlock_button.set_sensitive(editable.get_text() != "")

    def on_auth_prompt_entry_button_press(self, widget, event):
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def on_unlock_clicked(self, button=None):
        self.emit("inhibit-timeout")

        text = self.auth_prompt_entry.get_text()
        self.show_spinner()

        self.clear_entry()

        self.authenticate(text)

    def on_auth_enter_key(self, widget):
        if widget.get_text() == "":
            return
        self.on_unlock_clicked()

    def on_switch_user_clicked(self, widget):
        utils.do_user_switch()

    def on_logout_clicked(self, widget):
        self.set_sensitive(False)
        utils.do_logout()

    def setup_kbd_layout_button(self):
        global kbd_config

        if kbd_config is None:
            kbd_config = Gkbd.Configuration()

        if len(kbd_config.get_group_names()) > 1:
            indicator = Gkbd.Indicator()
            indicator.set_parent_tooltips(True)
            self.kbd_layout_indicator.pack_start(indicator, False, False, 0)

            self.kbd_layout_indicator.show_all()
        else:
            self.kbd_layout_indicator.hide()

    def show_spinner(self):
        self.spinner.start()
        self.stack.set_visible_child_name("spinner")

    def show_entry(self):
        self.spinner.stop()
        self.stack.set_visible_child_name("entry")

    def clear_entry(self):
        self.auth_prompt_entry.set_text("")

    def update_realname_label(self):
        markup = "<span foreground=\"#3F3F3F\" font_desc=\"Ubuntu 14\"><b>%s</b></span>" % (self.real_name)

        self.realname_label.set_markup(markup)

    def update_username_label(self):
        hostname = utils.get_host_name()

        markup = "<span foreground=\"#3F3F3F\" font_desc=\"Ubuntu 10\"><i>%s @ %s</i></span>" % (self.user_name, hostname)

        self.username_label.set_markup(markup)

    def authenticate(self, password):
        self.auth_proxy.check_password(self.user_name,
                                       password,
                                       self.authenticate_callback)

    def authenticate_callback(self, success, msg):
        if success:
            self.clear_entry()
            self.emit("auth-success")
        else:
            self.authentication_failed(msg)
            self.emit("auth-failure")

    def authentication_failed(self, msg):
        self.show_entry()
        self.auth_message_label.set_text(msg)

        self.auth_prompt_entry.grab_focus()

        self.emit("uninhibit-timeout")

    def update_logout_button(self):
        self.auth_logout_button.set_visible(status.LogoutEnabled)
