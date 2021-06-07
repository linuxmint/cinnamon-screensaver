#!/usr/bin/python3

from gi.repository import Gdk, GObject, GLib, Gio
import time
import traceback
import os
import signal
import subprocess

import config
import constants as c
import status

from stage import Stage
import singletons
from util import utils, settings, trackers
from util.focusNavigator import FocusNavigator
from util.grabHelper import GrabHelper

class ScreensaverManager(GObject.Object):
    """
    The ScreensaverManager is the central point where most major decision are made,
    and where ScreensaverService requests are acted upon.
    """
    __gsignals__ = {
        'active-changed': (GObject.SignalFlags.RUN_LAST, None, (bool, )),
    }

    def __init__(self):
        super(ScreensaverManager, self).__init__()

        self.activated_timestamp = 0

        self.stage = None
        self.fb_pid = 0
        self.fb_failed_to_start = False

        # Ensure our state
        status.Active = False
        status.Locked = False
        status.Awake = False

        self.grab_helper = GrabHelper(self)
        self.focus_nav = FocusNavigator()

        self.session_client = singletons.SessionClient
        trackers.con_tracker_get().connect(self.session_client,
                                           "idle-changed",
                                           self.on_session_idle_changed)

        self.cinnamon_client = singletons.CinnamonClient

        singletons.LoginClientResolver(self)

    def is_locked(self):
        """
        Return if we're Locked - we could be Active without being locked.
        """
        return status.Locked

    def set_locked(self, locked):
        if locked:
            status.Locked = True
            self.spawn_fallback_window()
        else:
            status.Locked = False
            self.kill_fallback_window()

    def lock(self, msg=""):
        """
        Initiate locking (activating first if necessary.)  Return True if we were
        already active and just need to set the lock flag (or we were already locked
        as well).  Return False if we're not active, and need to construct a stage, etc...
        """
        if not status.Active:
            if self.set_active(True, msg):
                self.stop_lock_delay()
                if utils.user_can_lock():
                    self.set_locked(True)
                return False
        else:
            if utils.user_can_lock():
                self.set_locked(True)
            self.stage.set_message(msg)

        # Return True to complete any invocation immediately because:
        # - we were already active and possibly already locked
        # - we were unable to achieve a server grab, or something else
        #   prevents the activation from proceeding, and we don't want to
        #   block anything...??
        return True

    def unlock(self):
        """
        Initiate unlocking and deactivating
        """
        self.set_active(False)
        self.set_locked(False)
        status.Awake = False

    def set_active(self, active, msg=None):
        """
        Activates or deactivates the screensaver.  Activation involves:
            - sending a request to Cinnamon to exit Overview or Expo -
              this could prevent a successful screen grab and keep the
              screensaver from activating.
            - grabbing the keyboard and mouse.
            - creating the screensaver Stage.
        Deactivation involves:
            - destroying the screensaver stage.
            - releasing our keyboard and mouse grabs.
        """
        if active:
            if not status.Active:
                self.cinnamon_client.exit_expo_and_overview()
                if self.grab_helper.grab_root(False):
                    if not self.stage:
                        Gio.Application.get_default().hold()
                        self.spawn_stage(msg, self.on_spawn_stage_complete)
                    else:
                        self.stage.activate(self.on_spawn_stage_complete)
                        self.stage.set_message(msg)
                    return True
                else:
                    status.Active = False
                    return False
            else:
                self.stage.set_message(msg)
                return True
        else:
            if self.stage:
                self.despawn_stage(self.on_despawn_stage_complete)
                Gio.Application.get_default().release()
                status.focusWidgets = []
            self.grab_helper.release()
            return True

    def get_active(self):
        """
        Return whether we're Active or not (showing) - this is not
        necessarily Locked.
        """
        return status.Active

    def get_active_time(self):
        """
        Return how long we've been activated, or 0 if we're not
        """
        if self.activated_timestamp != 0:
            return int(time.time() - self.activated_timestamp)
        else:
            return 0

    def simulate_user_activity(self):
        """
        Called upon any key, motion or button event, does different things
        depending on our current state.

        If we're idle:
            - do nothing

        If we're locked:
            - show the unlock widget (if it's already visible, this also has
              the effect of resetting the unlock timeout - see Stage.py)
            - show the mouse pointer, so the user can navigate the unlock screen.

        If we're Active but not Locked, simply deactivate (destroying the Stage
        and returning the screensaver back to idle mode.)
        """
        if not status.Active:
            return

        if status.Debug and not status.Awake:
            print("manager: user activity, waking")

        if status.Locked and self.stage.initialize_pam():
            if status.Debug and not status.Awake:
                print("manager: locked, raising unlock widget")

            self.stage.raise_unlock_widget()
            self.grab_helper.release_mouse()
            self.stage.maybe_update_layout()
        else:
            if status.Debug:
                print("manager: not locked, queueing idle deactivation")

            trackers.timer_tracker_get().add_idle("idle-deactivate",
                                                  self.idle_deactivate)

    def idle_deactivate(self):
        self.set_active(False)

        trackers.timer_tracker_get().cancel("idle-deactivate")

        return False

    def spawn_stage(self, away_message, callback=None):
        """
        Create the Stage and begin fading it in.  This may run quickly, in the case of
        user-initiated activation, or slowly, when the session has gone idle.
        """
        try:
            self.stage = Stage(self, away_message)
            self.stage.activate(callback)
        except Exception:
            print("Could not spawn screensaver stage:\n")
            traceback.print_exc()
            self.grab_helper.release()
            status.Active = False
            self.cancel_timers()

    def spawn_fallback_window(self):
        if self.fb_pid > 0:
            return

        if status.Debug:
            print("manager: spawning fallback window")

        if self.stage.get_realized():
            self._real_spawn_fallback_window(self)
        else:
            self.stage.connect("realize", self._real_spawn_fallback_window)

    def get_tty_vals(self):
        session_tty = None
        term_tty = None
        username = GLib.get_user_name()[:8]
        used_tty = []

        try:
            tty_output = subprocess.check_output(["w", "-h"]).decode("utf-8")
            for line in tty_output.split("\n"):
                if line.startswith(username):
                    if "cinnamon-session" in line and "tty" in line:
                        session_tty = line.split()[1].replace("tty", "")
                        used_tty.append(session_tty)
                    elif "tty" in line:
                        term_tty = line.split()[1].replace("tty", "")
                elif "tty" in line:
                    used_tty.append(line.split()[1].replace("tty", ""))

            used_tty.sort()

            if term_tty == None:
                for i in range(1, 6):
                    if str(i) not in used_tty:
                        term_tty = str(i)
                        break
        except Exception as e:
            print("Failed to get tty numbers using w -h: %s" % str(e))

        if session_tty == None:
            try:
                session_tty = os.environ["XDG_VTNR"]
            except KeyError:
                session_tty = "7"

        if term_tty == None:
            term_tty = "2" if session_tty != "2" else "1"

        return [term_tty, session_tty]

    def _real_spawn_fallback_window(self, stage, data=None):
        if self.fb_pid > 0:
            return

        term_tty, session_tty = self.get_tty_vals()

        argv = [
            os.path.join(config.libexecdir, "cs-backup-locker"),
            str(self.stage.get_window().get_xid()),
            term_tty,
            session_tty
        ]

        try:
            self.fb_pid = GLib.spawn_async(argv)[0]
        except GLib.Error as e:
            self.fb_failed_to_start = True
            print("Could not start screensaver fallback process: %s" % e.message)

        try:
            self.stage.disconnect_by_func(self._real_spawn_fallback_window)
        except:
            pass

    def kill_fallback_window(self):
        if self.fb_pid == 0 and not self.fb_failed_to_start:
            return

        if status.Debug:
            print("manager: killing fallback window")

        try:
            if status.Debug:
                print("manager: checking if fallback window exists first.")
            if self.fb_pid > 0:
                os.kill(self.fb_pid, 0)
            elif self.fb_failed_to_start:
                raise ProcessLookupError("Fallback window failed to start")
        except ProcessLookupError:
            if status.Debug:
                print("manager: fallback window terminated before the main screensaver, something went wrong!")
            notification = Gio.Notification.new(_("Cinnamon Screensaver has experienced an error"))

            notification.set_body(_("The 'cs-backup-locker' process terminated before the screensaver did. "
                                    "Please report this issue and try to describe any actions you may "
                                    "have performed prior to this occurring."))
            notification.set_icon(Gio.ThemedIcon(name="dialog-error"))
            notification.set_priority(Gio.NotificationPriority.URGENT)
            Gio.Application.get_default().send_notification("cinnamon-screensaver", notification)

        try:
            os.kill(self.fb_pid, signal.SIGTERM)
        except:
            pass

        self.fb_failed_to_start = False
        self.fb_pid = 0

    def despawn_stage(self, callback=None):
        """
        Begin destruction of the stage.
        """
        self.stage.cancel_unlocking()
        self.stage.deactivate(callback)

    def on_spawn_stage_complete(self):
        """
        Called after the stage become visible.  All user events are now
        redirected to GrabHelper, our status is updated, our active timer
        is started, and emit an active-changed signal (Which is listened to
        by our ConsoleKit client if we're using it, and our own ScreensaverService.)
        """
        self.grab_stage()

        status.Active = True

        self.emit("active-changed", True)

        self.start_timers()

    def on_despawn_stage_complete(self):
        """
        Called after the stage has been hidden - the stage is destroyed, our status
        is updated, timer is canceled and active-changed is fired.
        """
        was_active = status.Active == True
        status.Active = False

        if was_active:
            self.emit("active-changed", False)

        self.cancel_timers()

        self.stage.destroy_stage()
        self.stage = None

        # Ideal time to check for leaking connections that might prevent GC by python and gobject
        if trackers.DEBUG_SIGNALS:
            trackers.con_tracker_get().dump_connections_list()

        if trackers.DEBUG_TIMERS:
            trackers.timer_tracker_get().dump_timer_list()

    def grab_stage(self):
        """
        Makes a hard grab on the Stage window, all keyboard and mouse events are dispatched or eaten
        by us now.
        """
        if self.stage != None:
            self.grab_helper.move_to_window(self.stage.get_window(), True)

    def update_stage(self):
        """
        Tells the stage to check its canvas size and make sure its windows are up-to-date.  This is called
        when our login manager tells us its "Active" property has changed.  We are always connected to the
        login manager, so we first check if we have a stage.
        """
        if self.stage == None:
            return

        if status.Debug:
            print("manager: queuing stage refresh (login manager reported active?")

        self.stage.queue_refresh_stage()

    def start_timers(self):
        """
        Stamps our current time starts our lock delay timer (the elapsed time to allow after
        activation, to lock the computer.)
        """
        self.activated_timestamp = time.time()
        self.start_lock_delay()

    def cancel_timers(self):
        """
        Zeros out our activated timestamp and cancels our lock delay timer.
        """
        self.activated_timestamp = 0
        self.stop_lock_delay()

    def cancel_unlock_widget(self):
        """
        Return to sleep (not Awake) - hides the pointer and the unlock widget.
        """
        self.grab_stage()
        self.stage.cancel_unlocking();

    def on_lock_delay_timeout(self):
        """
        Updates the lock status when our timer has hit its limit
        """
        if status.Debug:
            print("manager: locking after delay ('lock-delay')")

        self.set_locked(True)

        return False

    def start_lock_delay(self):
        """
        Setup the lock delay timer based on user prefs - if there is
        no delay, or if idle locking isn't enabled, we run the callback
        immediately, or simply return, respectively.
        """
        if not settings.get_idle_lock_enabled():
            return

        if not utils.user_can_lock():
            return

        lock_delay = settings.get_idle_lock_delay()

        if lock_delay == 0:
            self.on_lock_delay_timeout()
        else:
            trackers.timer_tracker_get().start_seconds("idle-lock-delay",
                                                       lock_delay,
                                                       self.on_lock_delay_timeout)

    def stop_lock_delay(self):
        """
        Cancels the lock delay timer.
        """
        trackers.timer_tracker_get().cancel("idle-lock-delay")

##### EventHandler/GrabHelper/FocusNavigator calls.

    def queue_dialog_key_event(self, event):
        """
        Forwards a captured key event to the stage->unlock dialog.
        """
        self.stage.queue_dialog_key_event(event)

    def propagate_tab_event(self, shifted):
        """
        Forwards a tab event to the focus navigator.
        """
        self.focus_nav.navigate(shifted)

    def propagate_activation(self):
        """
        Forwards an activation event (return) to the focus navigator.
        """
        self.focus_nav.activate_focus()

    def get_focused_widget(self):
        """
        Returns the currently focused widget from the FocusNavigator
        """
        return self.focus_nav.get_focused_widget()

    def on_session_idle_changed(self, proxy, idle):
        """
        Call back for the session client - initiates a slow fade-in
        for the stage when the session goes idle.  Cancels the stage fade-in
        if idle becomes False before it has completed its animation.
        """
        if idle and not status.Active:
            self.set_active(True)
