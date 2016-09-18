#! /usr/bin/python3
# coding: utf-8

import gi
gi.require_version('AccountsService', '1.0')
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gtk, Gdk, AccountsService, GObject, CinnamonDesktop, GdkPixbuf
import os

from util import utils, trackers
import status
import singletons
from baseWindow import BaseWindow
from widgets.transparentButton import TransparentButton

acc_service = None

class FramedImage(Gtk.Image):
    def __init__(self):
        super(FramedImage, self).__init__()
        self.get_style_context().add_class("framedimage")
        self.min_height = 150

        self.set_size_request(-1, self.min_height)

    def set_from_file(self, path):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, -1, self.min_height, True)
        self.set_from_pixbuf(pixbuf)

class PasswordEntry(Gtk.Entry):
    def __init__(self):
        super(PasswordEntry, self).__init__()
        self.get_style_context().add_class("passwordentry")

        self.set_halign(Gtk.Align.FILL)
        self.set_has_frame(True)
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        self.set_property("caps-lock-warning", False)
        self.set_placeholder_text (_("Enter password..."))
        self.set_can_default(True)

        trackers.con_tracker_get().connect(self,
                                           "icon-press",
                                           self.on_icon_pressed)

        self.keyboard_layout = singletons.KeyboardLayout
        self.keyboard_layout.set_lockscreen_group()

        trackers.con_tracker_get().connect(self.keyboard_layout,
                                           "group-changed",
                                           self.on_group_changed)

        self.update_layout_icon()

        trackers.con_tracker_get().connect(self,
                                           "destroy",
                                           self.on_destroy)

    def on_group_changed(self, keyboard_layout):
        self.grab_focus_without_selecting()
        self.update_layout_icon()

    def on_icon_pressed(self, entry, icon_pos, event):
        if icon_pos == Gtk.EntryIconPosition.PRIMARY:
            self.keyboard_layout.next_group()

    def update_layout_icon(self):
        pixbuf = self.keyboard_layout.get_image_pixbuf(self)

        self.set_icon_from_pixbuf(Gtk.EntryIconPosition.PRIMARY, pixbuf)

    def grab_focus(self):
        Gtk.Entry.grab_focus_without_selecting(self)

    def on_destroy(self, widget, data=None):
        self.keyboard_layout.restore_original_group()


class UnlockDialog(BaseWindow):
    __gsignals__ = {
        'inhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'uninhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-success': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-failure': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self):
        super(UnlockDialog, self).__init__()

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_size_request(350, -1)

        self.real_name = None
        self.user_name = None

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.get_style_context().add_class("unlockbox")
        self.add(self.box)

        self.face_image = FramedImage()
        self.face_image.set_halign(Gtk.Align.CENTER)
        self.box.pack_start(self.face_image, False, False, 10)

        self.realname_label = Gtk.Label(None)
        self.realname_label.set_alignment(0, 0.5)
        self.realname_label.set_halign(Gtk.Align.CENTER)

        self.box.pack_start(self.realname_label, False, False, 10)

        self.entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.box.pack_start(self.entry_box, True, True, 2)

        self.password_entry = PasswordEntry()

        trackers.con_tracker_get().connect(self.password_entry,
                                           "changed",
                                           self.on_password_entry_text_changed)

        trackers.con_tracker_get().connect(self.password_entry,
                                           "button-press-event",
                                           self.on_password_entry_button_press)

        trackers.con_tracker_get().connect(self.password_entry,
                                           "activate",
                                           self.on_auth_enter_key)

        self.entry_box.pack_start(self.password_entry, True, True, 15)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.entry_box.pack_end(button_box, False, False, 0)

        self.auth_unlock_button = TransparentButton("screensaver-unlock-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.auth_unlock_button.set_sensitive(False)

        trackers.con_tracker_get().connect(self.auth_unlock_button,
                                           "clicked",
                                           self.on_unlock_clicked)

        button_box.pack_start(self.auth_unlock_button, False, False, 4)

        self.auth_switch_button = TransparentButton("screensaver-switch-users-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        trackers.con_tracker_get().connect(self.auth_switch_button,
                                           "clicked",
                                           self.on_switch_user_clicked)

        button_box.pack_start(self.auth_switch_button, False, False, 4)

        status.focusWidgets = [self.password_entry,
                               self.auth_unlock_button,
                               self.auth_switch_button]

        vbox_messages = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        self.capslock_label = Gtk.Label("")
        self.capslock_label.get_style_context().add_class("caps-message")
        self.capslock_label.set_alignment(0.5, 0.5)
        vbox_messages.pack_start(self.capslock_label, False, False, 2)

        self.auth_message_label = Gtk.Label("")
        self.auth_message_label.get_style_context().add_class("auth-message")
        self.auth_message_label.set_alignment(0.5, 0.5)
        vbox_messages.pack_start(self.auth_message_label, False, False, 2)

        self.box.pack_start(vbox_messages, False, False, 0)

        self.real_name = utils.get_user_display_name()
        self.user_name = utils.get_user_name()

        self.update_realname_label()

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

    def cancel(self):
        self.auth_message_label.set_text("")

    def on_revealed(self, widget, child):
        if self.get_child_revealed():
            self.keymap_handler(self.keymap)
        else:
            self.password_entry.set_text("")

    def queue_key_event(self, event):
        if not self.password_entry.get_realized():
            self.password_entry.realize()

        self.password_entry.event(event)

    def keymap_handler(self, keymap):
        if keymap.get_caps_lock_state():
            self.capslock_label.set_text(_("You have the Caps Lock key on."))
        else:
            self.capslock_label.set_text("")

    def on_accounts_service_loaded(self, service, param):
        self.real_name = service.get_real_name()
        self.update_realname_label()

        for path in [os.path.join(service.get_home_dir(), ".face"),
                     service.get_icon_file(),
                     "/usr/share/cinnamon/faces/user-generic.png"]:
            if os.path.exists(path):
                self.face_image.set_from_file(path)
                break

    def on_password_entry_text_changed(self, editable):
        if not self.password_entry.has_focus():
            self.password_entry.grab_focus()
        self.auth_unlock_button.set_sensitive(editable.get_text() != "")

    def on_password_entry_button_press(self, widget, event):
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def on_unlock_clicked(self, button=None):
        self.emit("inhibit-timeout")

        text = self.password_entry.get_text()
        self.start_progress()

        self.password_entry.set_placeholder_text (_("Checking..."))

        self.authenticate(text)

    def on_auth_enter_key(self, widget):
        if widget.get_text() == "":
            return

        self.on_unlock_clicked()

    def on_switch_user_clicked(self, widget):
        utils.do_user_switch()

    def pulse(self):
        self.password_entry.progress_pulse()
        return True

    def start_progress(self):
        self.password_entry.set_progress_pulse_step(0.2)
        trackers.timer_tracker_get().start("auth-progress",
                                           100,
                                           self.pulse)

    def stop_progress(self):
        trackers.timer_tracker_get().cancel("auth-progress")
        self.password_entry.set_progress_fraction(0.0)

    def clear_entry(self):
        self.password_entry.set_text("")

    def update_realname_label(self):
        self.realname_label.set_text(self.real_name)

    def authenticate(self, password):
        CinnamonDesktop.desktop_check_user_password(self.user_name,
                                                    password,
                                                    self.authenticate_callback)

    def authenticate_callback(self, success, data=None):
        self.stop_progress()

        if success:
            self.clear_entry()
            self.emit("auth-success")
        else:
            self.authentication_failed()
            self.emit("auth-failure")

    def authentication_failed(self):
        self.clear_entry()

        self.password_entry.set_placeholder_text (_("Enter password..."))
        self.auth_message_label.set_text(_("Password incorrect - try again."))

        self.password_entry.grab_focus()

        self.emit("uninhibit-timeout")
