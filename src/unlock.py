#! /usr/bin/python3
# coding: utf-8

import gi

from gi.repository import Gtk, Gdk, GObject, CScreensaver
import traceback


from util import utils, trackers
import status
import singletons
from baseWindow import BaseWindow
from widgets.framedImage import FramedImage
from passwordEntry import PasswordEntry
from pamhelper.authClient import AuthClient
from widgets.transparentButton import TransparentButton

class UnlockDialog(BaseWindow):
    """
    The main widget for the unlock dialog - this is a direct child of
    the Stage's GtkOverlay.

    It has a number of parts, namely:
        - The user face image.
        - The user's real name (or username if the real name is unavailable)
        - The password entry widget
        - Unlock and Switch User buttons
        - A caps lock warning label
        - An invalid password error label
    """
    __gsignals__ = {
        'inhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'uninhibit-timeout': (GObject.SignalFlags.RUN_LAST, None, ()),
        'authenticate-success': (GObject.SignalFlags.RUN_LAST, None, ()),
        'authenticate-failure': (GObject.SignalFlags.RUN_LAST, None, ()),
        'authenticate-cancel': (GObject.SignalFlags.RUN_LAST, None, ())
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
        self.face_image.get_style_context().add_class("faceimage")
        self.face_image.set_no_show_all(True)

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

        self.entry_box.pack_start(self.password_entry, False, False, 15)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.entry_box.pack_end(button_box, False, False, 0)

        self.auth_unlock_button = TransparentButton("screensaver-unlock-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.auth_unlock_button.set_tooltip_text(_("Unlock"))
        trackers.con_tracker_get().connect(self.auth_unlock_button,
                                           "clicked",
                                           self.on_unlock_clicked)

        button_box.pack_start(self.auth_unlock_button, False, False, 4)

        self.auth_switch_button = TransparentButton("screensaver-switch-users-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.auth_switch_button.set_tooltip_text(_("Switch users"))

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

        self.account_client = singletons.AccountsServiceClient
        if self.account_client.is_loaded:
            self.on_account_client_loaded(self.account_client)
        else:
            trackers.con_tracker_get().connect(self.account_client,
                                               "account-loaded",
                                               self.on_account_client_loaded)

        self.keymap = Gdk.Keymap.get_default()

        trackers.con_tracker_get().connect(self.keymap,
                                           "state-changed",
                                           self.keymap_handler)

        trackers.con_tracker_get().connect_after(self,
                                                 "notify::child-revealed",
                                                 self.on_revealed)

        self.auth_client = AuthClient()

        trackers.con_tracker_get().connect(self.auth_client,
                                           "auth-success",
                                           self.on_authentication_success)
        trackers.con_tracker_get().connect(self.auth_client,
                                           "auth-failure",
                                           self.on_authentication_failure)
        trackers.con_tracker_get().connect(self.auth_client,
                                           "auth-cancel",
                                           self.on_authentication_cancelled)
        trackers.con_tracker_get().connect(self.auth_client,
                                           "auth-busy",
                                           self.on_authentication_busy_changed)
        trackers.con_tracker_get().connect(self.auth_client,
                                           "auth-prompt",
                                           self.on_authentication_prompt_changed)

    def initialize_auth_client(self):
        return self.auth_client.initialize()

    def cancel_auth_client(self):
        self.auth_client.cancel()

    def on_authentication_success(self, auth_client):
        self.clear_entry()
        self.emit("authenticate-success")

    def on_authentication_failure(self, auth_client):
        """
        Called upon authentication failure, clears the password, sets an error message,
        and refocuses the password entry.
        """
        self.clear_entry()
        self.auth_message_label.set_text(_("Incorrect password"))

        self.emit("authenticate-failure")
        self.emit("uninhibit-timeout")

    def on_authentication_cancelled(self, auth_client):
        self.emit("authenticate-cancel")

    def on_authentication_busy_changed(self, auth_client, busy):
        if busy:
            self.auth_message_label.set_text("")
            self.clear_entry()
            self.entry_box.set_sensitive(False)
            self.password_entry.start_progress()
            self.password_entry.set_placeholder_text (_("Checking..."))
        else:
            self.entry_box.set_sensitive(True)
            self.password_entry.stop_progress()
            self.password_entry.set_placeholder_text (self.password_entry.placeholder_text)

    def on_authentication_prompt_changed(self, auth_client, prompt):
        if "password:" in prompt.lower():
            prompt = _("Please enter your password...")
        else:
            prompt = prompt.replace(":", "")

        self.password_entry.placeholder_text = prompt
        self.password_entry.set_placeholder_text(self.password_entry.placeholder_text)

    def cancel(self):
        """
        Clears the auth message text if we have any.
        """
        self.auth_message_label.set_text("")

    def on_revealed(self, widget, child):
        """
        Updates the capslock state and ensures the password is cleared when we're first shown.
        """
        if self.get_child_revealed():
            self.keymap_handler(self.keymap)
        else:
            self.password_entry.set_text("")

    def queue_key_event(self, event):
        """
        Takes a propagated key event from the stage and passes it to the entry widget,
        possibly queueing up the first character of the password.
        """
        if not self.password_entry.get_realized():
            self.password_entry.realize()
            self.password_entry.grab_focus()

        self.password_entry.event(event)

    def keymap_handler(self, keymap):
        """
        Handler for the GdkKeymap changing - updates our capslock indicator label.
        """
        if keymap.get_caps_lock_state():
            self.capslock_label.set_text(_("You have the Caps Lock key on."))
        else:
            self.capslock_label.set_text("")

    def on_account_client_loaded(self, client):
        """
        Handler for the AccountsService - requests the user real name and .face image.
        """
        if client.get_real_name() != None:
            self.real_name = client.get_real_name()
            self.update_realname_label()

        if client.get_face_path() != None:
            self.face_image.set_from_path(client.get_face_path())
            self.face_image.show()

    def on_password_entry_text_changed(self, editable):
        """
        Handler for the password entry text changing - this controls the sensitivity
        of the unlock button, as well as returning visual focus to the entry any time
        a key event is received.
        """

        if not self.password_entry.has_focus():
            self.password_entry.grab_focus()

    def on_password_entry_button_press(self, widget, event):
        """
        Prevents the usual copy/paste popup when right-clicking the PasswordEntry.
        """
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE

    def on_unlock_clicked(self, button=None):
        """
        Callback for the unlock button.  Activates the 'progress' animation
        in the GtkEntry, and attempts to authenticate the password.  During this
        time, we also inhibit the unlock timeout, so we don't fade out while waiting
        for an authentication result (highly unlikely.)
        """
        self.emit("inhibit-timeout")

        text = self.password_entry.get_text()

        # We must end with a newline, fgets relies upon that to continue.
        if text[-1:] != "\n":
            text += "\n"

        self.auth_client.message_to_child(text)

    def on_auth_enter_key(self, widget):
        """
        Implicitly activates the unlock button when the Enter/Return key is pressed.
        """

        self.on_unlock_clicked()

    def on_switch_user_clicked(self, widget):
        """
        Callback for the switch-user button.
        """
        utils.do_user_switch()

    def clear_entry(self):
        """
        Clear the password entry widget.
        """
        self.password_entry.set_text("")

    def update_realname_label(self):
        """
        Updates the name label to the current real_name.
        """
        self.realname_label.set_text(self.real_name)

