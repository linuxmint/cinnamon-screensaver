#!/usr/bin/python3

import gi
gi.require_version('CDesktopEnums', '3.0')

from gi.repository import GLib, Gtk, Gdk, CScreensaver, CDesktopEnums, GObject
import random

import status
import constants as c
import singletons
from floating import Floating
from monitorView import MonitorView
from unlock import UnlockDialog
from clock import ClockWidget
from albumArt import AlbumArt
from audioPanel import AudioPanel
from infoPanel import InfoPanel
from osk import OnScreenKeyboard
from util import utils, trackers, settings
from util.eventHandler import EventHandler
from util.utils import DEBUG

FLOATER_POSITIONING_TIMEOUT = 30

class Stage(Gtk.Window):
    """
    The Stage is the toplevel window of the entire screensaver while
    in Active mode.

    It's the first thing made, the last thing destroyed, and all other
    widgets live inside of it (or rather, inside the GtkOverlay below)

    It is Gtk.WindowType.POPUP to avoid being managed/composited by muffin,
    and to prevent animation during its creation and destruction.

    The Stage responds pretty much only to the instructions of the
    ScreensaverManager.
    """
    __gsignals__ = {
        'needs-refresh': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, manager, away_message):
        if status.InteractiveDebug:
            Gtk.Window.__init__(self,
                                type=Gtk.WindowType.TOPLEVEL,
                                decorated=True,
                                skip_taskbar_hint=False)
        else:
            Gtk.Window.__init__(self,
                                type=Gtk.WindowType.POPUP,
                                decorated=False,
                                skip_taskbar_hint=True)

        self.get_style_context().add_class("csstage")

        trackers.con_tracker_get().connect(singletons.Backgrounds,
                                           "changed",
                                           self.on_bg_changed)

        self.destroying = False

        self.manager = manager
        self.away_message = away_message

        self.activate_callback = None

        self.monitors = []
        self.last_focus_monitor = -1
        self.overlay = None
        self.clock_widget = None
        self.albumart_widget = None
        self.unlock_dialog = None
        self.audio_panel = None
        self.info_panel = None
        self.osk = None

        self.floaters = []
        self.floaters_need_update = False

        self.event_handler = EventHandler(manager)

        self.get_style_context().remove_class("background")

        self.set_events(self.get_events() |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.KEY_RELEASE_MASK |
                        Gdk.EventMask.EXPOSURE_MASK |
                        Gdk.EventMask.VISIBILITY_NOTIFY_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK |
                        Gdk.EventMask.FOCUS_CHANGE_MASK)

        c = Gdk.RGBA(0, 0, 0, 0)
        self.override_background_color(Gtk.StateFlags.NORMAL, c)

        self.update_geometry()

        self.overlay = Gtk.Overlay()

        trackers.con_tracker_get().connect(self.overlay,
                                           "realize",
                                           self.on_realized)

        trackers.con_tracker_get().connect(self.overlay,
                                           "get-child-position",
                                           self.position_overlay_child)

        self.overlay.show_all()
        self.add(self.overlay)

        # We hang onto the UPowerClient here so power events can
        # trigger changes to the info panel.
        self.power_client = singletons.UPowerClient

        trackers.con_tracker_get().connect(self.power_client,
                                           "power-state-changed",
                                           self.on_power_state_changed)

        # This filter suppresses any other windows that might share
        # our window group in muffin, from showing up over the Stage.
        # For instance: Chrome and Firefox native notifications.
        self.gdk_filter = CScreensaver.GdkEventFilter.new(self, 0)

        trackers.con_tracker_get().connect(status.screen,
                                           "size-changed",
                                           self.on_screen_size_changed)

        trackers.con_tracker_get().connect(status.screen,
                                           "monitors-changed",
                                           self.on_monitors_changed)

        trackers.con_tracker_get().connect(status.screen,
                                           "composited-changed",
                                           self.on_composited_changed)

        trackers.con_tracker_get().connect(self,
                                           "grab-broken-event",
                                           self.on_grab_broken_event)

        if status.InteractiveDebug:
            self.set_interactive_debugging(True)

    def update_monitors(self):
        self.destroy_monitor_views()

        try:
            self.setup_monitors()
            for monitor in self.monitors:
                self.sink_child_widget(monitor)
        except Exception as e:
            print("Problem updating monitor views views: %s" % str(e))

    def on_screen_size_changed(self, screen, data=None):
        """
        The screen changing size should be acted upon immediately, to ensure coverage.
        Wallpapers are secondary.
        """

        DEBUG("Stage: Received screen size-changed signal, refreshing stage")

        self.emit("needs-refresh")

    def on_monitors_changed(self, screen, data=None):
        """
        Updating monitors also will trigger an immediate stage coverage update (same
        as on_screen_size_changed), and follow up at idle with actual monitor view
        refreshes (wallpapers.)
        """
        DEBUG("Stage: Received screen monitors-changed signal, refreshing stage")

        self.emit("needs-refresh")

    def on_composited_changed(self, screen, data=None):
        if self.get_realized():
            DEBUG("Stage: Received screen composited-changed signal, refreshing stage")

            self.emit("needs-refresh")

    def on_grab_broken_event(self, widget, event, data=None):
        GObject.idle_add(self.manager.grab_stage)

        return False

    def activate(self, callback):
        """
        This is the primary way of making the Stage visible.
        """

        self.set_opacity(1.0)
        self.move_onscreen()
        self.show()

        if self.get_realized():
            callback()
        else:
            self.activate_callback = callback

    def deactivate(self, callback):
        """
        This is the primary way of destroying the stage.
        """
        self.hide()
        callback()

    def on_realized(self, widget):
        """
        Repositions the window when it is realized, to cover the entire
        GdkScreen (a rectangle exactly encompassing all monitors.)

        From here we also proceed to construct all overlay children and
        activate our window suppressor.
        """
        window = self.get_window()
        utils.override_user_time(window)

        CScreensaver.Screen.set_net_wm_name(window, "cinnamon-screensaver-window")

        self.setup_children()

        self.gdk_filter.start(singletons.MuffinClient.get_using_fractional_scaling(), status.Debug)

        trackers.con_tracker_get().disconnect(self.overlay,
                                              "realize",
                                              self.on_realized)

        if self.activate_callback is not None:
            self.activate_callback()

    def move_onscreen(self):
        w = self.get_window()

        if w:
            w.move_resize(self.rect.x,
                          self.rect.y,
                          self.rect.width,
                          self.rect.height)

        self.move(self.rect.x, self.rect.y)
        self.resize(self.rect.width, self.rect.height)

    def deactivate_after_timeout(self):
        self.manager.set_active(False)

    def setup_children(self):
        """
        Creates all of our overlay children.  If a new 'widget' gets added,
        this should be the setup point for it.

        We bail if something goes wrong on a critical widget - a monitor view or
        unlock widget.
        """
        total_failure = False

        try:
            self.setup_monitors()
        except Exception as e:
            print("Problem setting up monitor views: %s" % str(e))
            total_failure = True

        try:
            self.setup_unlock()
        except Exception as e:
            print("Problem setting up unlock dialog: %s" % str(e))
            total_failure = True

        if not total_failure:
            try:
                self.setup_clock()
            except Exception as e:
                print("Problem setting up clock widget: %s" % str(e))
                self.clock_widget = None

            try:
                self.setup_osk()
            except Exception as e:
                print("Problem setting up on-screen keyboard: %s" % str(e))
                self.osk = None

            trackers.timer_tracker_get().start("setup-delayed-components",
                                               2000,
                                               self.setup_delayed_components)
        else:
            print("Total failure somewhere, deactivating screensaver.")
            GObject.idle_add(self.deactivate_after_timeout)

    def setup_delayed_components(self, data=None):
        try:
            self.setup_albumart()
        except Exception as e:
            print("Problem setting up albumart widget: %s" % str(e))
            self.albumart_widget = None
        try:
            self.setup_status_bars()
        except Exception as e:
            print("Problem setting up status bars: %s" % str(e))
            self.audio_panel = None
            self.info_panel = None

        self.start_float_timer()

    def start_float_timer(self):
        if settings.get_allow_floating():
            if status.Debug:
                timeout = 5
            else:
                timeout = FLOATER_POSITIONING_TIMEOUT
            trackers.timer_tracker_get().start_seconds("floater-update", timeout, self.update_floaters)

    def update_floaters(self):
        self.floaters_need_update = True
        self.overlay.queue_allocate()
        return GLib.SOURCE_CONTINUE

    def stop_float_timer(self):
        trackers.timer_tracker_get().cancel("floater-update")
        self.floaters_need_update = False

    def destroy_children(self):
        self.stop_float_timer()

        try:
            self.destroy_monitor_views()
        except Exception as e:
            print(e)

        try:
            if self.unlock_dialog is not None:
                self.unlock_dialog.destroy()
        except Exception as e:
            print(e)

        try:
            if self.clock_widget is not None:
                self.clock_widget.destroy()
        except Exception as e:
            print(e)

        try:
            if self.albumart_widget is not None:
                self.albumart_widget.destroy()
        except Exception as e:
            print(e)

        try:
            if self.info_panel is not None:
                self.info_panel.destroy()
        except Exception as e:
            print(e)

        try:
            if self.info_panel is not None:
                self.audio_panel.destroy()
        except Exception as e:
            print(e)

        try:
            if self.osk is not None:
                self.osk.destroy()
        except Exception as e:
            print(e)

        self.unlock_dialog = None
        self.clock_widget = None
        self.albumart_widget = None
        self.info_panel = None
        self.audio_panel = None
        self.osk = None
        self.away_message = None

        self.monitors = []
        self.floaters = []

    def destroy_stage(self):
        """
        Performs all tear-down necessary to destroy the Stage, destroying
        all children in the process, and finally destroying itself.
        """

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "inhibit-timeout",
                                              self.set_timeout_active)

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "uninhibit-timeout",
                                              self.set_timeout_active)

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "authenticate-success",
                                              self.authentication_result_callback)

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "authenticate-failure",
                                              self.authentication_result_callback)

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "authenticate-cancel",
                                              self.authentication_cancel_callback)

        trackers.con_tracker_get().disconnect(singletons.Backgrounds,
                                              "changed",
                                              self.on_bg_changed)

        trackers.con_tracker_get().disconnect(self.power_client,
                                              "power-state-changed",
                                              self.on_power_state_changed)

        trackers.con_tracker_get().disconnect(self,
                                              "grab-broken-event",
                                              self.on_grab_broken_event)

        self.set_timeout_active(None, False)

        trackers.timer_tracker_get().cancel("setup-delayed-components")
        self.destroy_children()

        self.gdk_filter.stop()
        self.gdk_filter = None

        trackers.con_tracker_get().disconnect(status.screen,
                                              "size-changed",
                                              self.on_screen_size_changed)

        trackers.con_tracker_get().disconnect(status.screen,
                                              "monitors-changed",
                                              self.on_monitors_changed)

        trackers.con_tracker_get().disconnect(self.overlay,
                                              "get-child-position",
                                              self.position_overlay_child)

        self.destroy()

    def setup_monitors(self):
        """
        Iterate through the monitors, and create MonitorViews for each one
        to cover them.
        """
        self.monitors = []
        status.Spanned = settings.bg_settings.get_enum("picture-options") == CDesktopEnums.BackgroundStyle.SPANNED

        if status.InteractiveDebug or status.Spanned:
            monitors = (status.screen.get_primary_monitor(),)
        else:
            n = status.screen.get_n_monitors()
            monitors = ()
            for i in range(n):
                monitors += (i,)

        for index in monitors:
            monitor = MonitorView(index)

            image = Gtk.Image()

            singletons.Backgrounds.create_and_set_gtk_image (image,
                                                             monitor.rect.width,
                                                             monitor.rect.height)

            monitor.set_next_wallpaper_image(image)

            self.monitors.append(monitor)

            self.add_child_widget(monitor)

        self.update_monitor_views()

    def on_bg_changed(self, bg):
        """
        Callback for our GnomeBackground instance, this tells us when
        the background settings have changed, so we can update our wallpaper.
        """
        for monitor in self.monitors:
            image = Gtk.Image()

            singletons.Backgrounds.create_and_set_gtk_image (image,
                                                             monitor.rect.width,
                                                             monitor.rect.height)

            monitor.set_next_wallpaper_image(image)

    def on_power_state_changed(self, client, data=None):
        """
        Callback for UPower changes, this will make our MonitorViews update
        themselves according to user setting and power state.
        """
        DEBUG("stage: Power state changed, updating info panel")

        if self.info_panel is not None:
            self.info_panel.update_visibility()

    def setup_clock(self):
        """
        Construct the clock widget and add it to the overlay, but only actually
        show it if we're a) Not running a plug-in, and b) The user wants it via
        preferences.

        Initially invisible, regardless - its visibility is controlled via its
        own positioning timer.
        """
        self.clock_widget = ClockWidget(self.away_message, status.screen.get_mouse_monitor(), status.screen.get_low_res_mode())
        self.add_child_widget(self.clock_widget)

        self.floaters.append(self.clock_widget)

        if settings.get_show_clock():
            self.clock_widget.start_positioning()

    def setup_albumart(self):
        """
        Construct the AlbumArt widget and add it to the overlay, but only actually
        show it if we're a) Not running a plug-in, and b) The user wants it via
        preferences.

        Initially invisible, regardless - its visibility is controlled via its
        own positioning timer.
        """
        self.albumart_widget = AlbumArt(status.screen.get_mouse_monitor(), status.screen.get_low_res_mode())
        self.add_child_widget(self.albumart_widget)

        self.floaters.append(self.albumart_widget)

        if settings.get_show_albumart():
            self.albumart_widget.start_positioning()

    def setup_osk(self):
        self.osk = OnScreenKeyboard()

        self.add_child_widget(self.osk)

    def setup_unlock(self):
        """
        Construct the unlock dialog widget and add it to the overlay.  It will always
        initially be invisible.

        Any time the screensaver is awake, and the unlock dialog is raised, a timer runs.
        After a certain elapsed time, the state will be reset, and the dialog will be hidden
        once more.  Mouse and key events reset this timer, and the act of authentication
        temporarily suspends it - the unlock widget accomplishes this via its inhibit- and
        uninhibit-timeout signals

        We also listen to actual authentication events, to destroy the stage if there is success,
        and to do something cute if we fail (for now, this consists of 'blinking' the unlock
        dialog.)
        """
        self.unlock_dialog = UnlockDialog()
        self.set_default(self.unlock_dialog.auth_unlock_button)
        self.add_child_widget(self.unlock_dialog)

        # Prevent a dialog timeout during authentication
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "inhibit-timeout",
                                           self.set_timeout_active, False)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "uninhibit-timeout",
                                           self.set_timeout_active, True)

        # Respond to authentication success/failure
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "authenticate-success",
                                           self.authentication_result_callback, True)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "authenticate-failure",
                                           self.authentication_result_callback, False)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "authenticate-cancel",
                                           self.authentication_cancel_callback)

    def setup_status_bars(self):
        """
        Constructs the AudioPanel and InfoPanel and adds them to the overlay.
        """
        self.audio_panel = AudioPanel()
        self.add_child_widget(self.audio_panel)

        if status.Awake:
            self.audio_panel.show_panel()

        self.info_panel = InfoPanel()
        self.add_child_widget(self.info_panel)

        self.info_panel.refresh_power_state()

    def queue_dialog_key_event(self, event):
        """
        Sent from our EventHandler via the ScreensaverManager, this catches
        initial key events before the unlock dialog is made visible, so that
        the user doesn't have to first jiggle the mouse to wake things up before
        beginning to type their password.  They can just start typing, and no
        keystrokes will be lost.
        """
        self.unlock_dialog.queue_key_event(event)

# Timer stuff - after a certain time, the unlock dialog will cancel itself.
# This timer is suspended during authentication, and any time a new user event is received

    def reset_timeout(self):
        """
        This is called when any user event is received in our EventHandler.
        This restarts our dialog timeout.
        """
        self.set_timeout_active(None, True)

    def set_timeout_active(self, dialog, active):
        """
        Start or stop the dialog timer
        """
        if active and not status.InteractiveDebug:
            trackers.timer_tracker_get().start("wake-timeout",
                                               c.UNLOCK_TIMEOUT * 1000,
                                               self.on_wake_timeout)
        else:
            trackers.timer_tracker_get().cancel("wake-timeout")

    def on_wake_timeout(self):
        """
        Go back to Sleep if we hit our timer limit
        """
        self.set_timeout_active(None, False)
        self.manager.cancel_unlocking()

        return False

    def authentication_result_callback(self, dialog, success):
        """
        Called by authentication success or failure.  Either starts
        the stage despawning process or simply 'blinks' the unlock
        widget, depending on the outcome.
        """
        if success:
            if self.clock_widget is not None:
                self.clock_widget.hide()
            if self.albumart_widget is not None:
                self.albumart_widget.hide()
            self.unlock_dialog.hide()
            self.manager.unlock()
        else:
            self.unlock_dialog.blink()

    def authentication_cancel_callback(self, dialog):
        self.manager.cancel_unlocking()

    def set_message(self, msg):
        """
        Passes along an away-message to the clock.
        """
        if self.clock_widget is not None:
            self.clock_widget.set_message(msg)

    def initialize_pam(self):
        return self.unlock_dialog.initialize_auth_client()

    def raise_unlock_widget(self):
        """
        Bring the unlock widget to the front and make sure it's visible.
        """
        self.reset_timeout()

        if status.Awake:
            return

        status.screen.place_pointer_in_primary_monitor ()

        utils.clear_clipboards(self.unlock_dialog)

        self.stop_float_timer()

        status.Awake = True

        if self.info_panel:
            self.info_panel.refresh_power_state()

        self.unlock_dialog.show()

        if self.audio_panel is not None:
            self.audio_panel.show_panel()
        if self.info_panel is not None:
            self.info_panel.refresh_power_state()
        if self.osk is not None:
            self.osk.show()

    def cancel_unlocking(self):
        if self.unlock_dialog:
            self.unlock_dialog.cancel()

        self.set_timeout_active(None, False)
        utils.clear_clipboards(self.unlock_dialog)

        if self.unlock_dialog is not None:
            self.unlock_dialog.hide()
        if self.audio_panel is not None:
            self.audio_panel.hide()
        if self.info_panel is not None:
            self.info_panel.hide()
        if self.osk is not None:
            self.osk.hide()

        status.Awake = False

        self.update_monitor_views()
        self.start_float_timer()

        if self.info_panel is not None:
            self.info_panel.refresh_power_state()

    def update_monitor_views(self):
        """
        Updates all of our MonitorViews based on the power
        or Awake states.
        """
        for monitor in self.monitors:
                monitor.show()

    def destroy_monitor_views(self):
        """
        Destroy all MonitorViews
        """
        for monitor in self.monitors:
            monitor.destroy()
            del monitor

    def do_motion_notify_event(self, event):
        """
        GtkWidget class motion-event handler.  Delegate to EventHandler
        """
        return self.event_handler.on_motion_event(event)

    def do_key_press_event(self, event):
        """
        GtkWidget class key-press-event handler.  Delegate to EventHandler
        """
        return self.event_handler.on_key_press_event(event)

    def do_button_press_event(self, event):
        """
        GtkWidget class button-press-event handler.  Delegate to EventHandler
        """
        return self.event_handler.on_button_press_event(event)

    def update_geometry(self):
        """
        Override BaseWindow.update_geometry() - the Stage should always be the
        GdkScreen size, unless status.InteractiveDebug is True
        """

        if status.InteractiveDebug:
            monitor_n = status.screen.get_primary_monitor()
            self.rect = status.screen.get_monitor_geometry(monitor_n)
        else:
            self.rect = status.screen.get_screen_geometry()

            scale = status.screen.get_global_scale()
            self.rect.width *= scale
            self.rect.height *= scale

        DEBUG("Stage.update_geometry - new backdrop position: %d, %d  new size: %d x %d" % (self.rect.x, self.rect.y, self.rect.width, self.rect.height))

        hints = Gdk.Geometry()
        hints.min_width = self.rect.width
        hints.min_height = self.rect.height
        hints.max_width = self.rect.width
        hints.max_height = self.rect.height
        hints.base_width = self.rect.width
        hints.base_height = self.rect.height

        self.set_geometry_hints(self, hints, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE | Gdk.WindowHints.BASE_SIZE)

# Overlay window management

    def get_mouse_monitor(self):
        if status.InteractiveDebug:
            return status.screen.get_primary_monitor()
        else:
            return status.screen.get_mouse_monitor()

    def maybe_update_layout(self):
        """
        Called on all user events, moves widgets to the currently
        focused monitor if it changes (whichever monitor the mouse is in)
        """
        current_focus_monitor = status.screen.get_mouse_monitor()

        if self.last_focus_monitor == -1:
            self.last_focus_monitor = current_focus_monitor
            return

        if self.unlock_dialog and current_focus_monitor != self.last_focus_monitor:
            self.last_focus_monitor = current_focus_monitor
            self.overlay.queue_resize()

    def add_child_widget(self, widget):
        """
        Add a new child to the overlay
        """
        self.overlay.add_overlay(widget)

    def sink_child_widget(self, widget):
        """
        Move a child to the bottom of the overlay
        """
        self.overlay.reorder_overlay(widget, 0)

    def position_overlay_child(self, overlay, child, allocation):
        """
        Callback for our GtkOverlay, think of this as a mini-
        window manager for our Stage.

        Depending on what type child is, we position it differently.
        We always call child.get_preferred_size() whether we plan to use
        it or not - this prevents allocation warning spew, particularly in
        Gtk >= 3.20.

        Returning True says, yes draw it.  Returning False tells it to skip
        drawing.

        If a new widget type is introduced that spawns directly on the stage,
        it must have its own handling code here.
        """
        if isinstance(child, MonitorView):
            """
            MonitorView is always the size and position of its assigned monitor.
            This is calculated and stored by the child in child.rect)
            """
            w, h = child.get_preferred_size()
            allocation.x = child.rect.x
            allocation.y = child.rect.y
            allocation.width = child.rect.width
            allocation.height = child.rect.height

            return True

        if isinstance(child, UnlockDialog):
            """
            UnlockDialog always shows on the currently focused monitor (the one the
            mouse is currently in), and is kept centered.
            """
            monitor = status.screen.get_mouse_monitor()
            monitor_rect = status.screen.get_monitor_geometry(monitor)

            min_rect, nat_rect = child.get_preferred_size()

            allocation.width = nat_rect.width
            allocation.height = nat_rect.height

            allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (allocation.width / 2)
            allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (allocation.height / 2)

            return True

        if isinstance(child, Floating):
            """
            ClockWidget and AlbumArt behave differently depending on if status.Awake is True or not.

            The widgets' halign and valign properties are used to store their gross position on the
            monitor.  This limits the number of possible positions to (3 * 3 * n_monitors) when our
            screensaver is not Awake, and the widgets have an internal timer that randomizes halign,
            valign, and current monitor every so many seconds, calling a queue_resize on itself after
            each timer tick (which forces this function to run).
            """
            if settings.get_allow_floating():
                if self.floaters_need_update:
                    alignments = [int(Gtk.Align.START), int(Gtk.Align.END), int(Gtk.Align.CENTER)]
                    n_monitors = status.screen.get_n_monitors()
                    alignment_positions = []
                    for i in range(n_monitors):
                        for halign in alignments:
                            for valign in alignments:
                                alignment_positions.append((i, halign, valign))

                    for floater in self.floaters:
                        position = alignment_positions.pop(random.randint(0, len(alignment_positions) - 1))
                        floater.set_next_position(*position)

                    self.floaters_need_update = False

                child.apply_next_position()

            min_rect, nat_rect = child.get_preferred_size()
            current_monitor = child.current_monitor
            monitor_rect = status.screen.get_monitor_geometry(current_monitor)
            region_w = monitor_rect.width / 3
            region_h = monitor_rect.height / 3

            if status.Awake:
                current_monitor = status.screen.get_mouse_monitor()
                monitor_rect = status.screen.get_monitor_geometry(current_monitor)
                region_w = monitor_rect.width / 3
                region_h = monitor_rect.height / 3

                """
                If we're Awake, force the clock to track to the active monitor, and be aligned to
                the left-center.  The albumart widget aligns right-center.
                """
                unlock_mw, unlock_nw = self.unlock_dialog.get_preferred_width()
                """
                If, for whatever reason, we need more than 1/3 of the screen to fully display
                the unlock dialog, reduce our available region width to accommodate it, reducing
                the allocation for the floating widgets as required.
                """
                if unlock_nw > region_w:
                    region_w = (monitor_rect.width - unlock_nw) / 2

                child.set_awake_position(current_monitor)
                child.apply_next_position()

            # Restrict the widget size to the allowable region sizes if necessary.
            allocation.width = min(nat_rect.width, region_w)
            allocation.height = min(nat_rect.height, region_h)

            # Calculate padding required to center widgets within their particular 1/9th of the monitor
            padding_left = padding_right = (region_w - allocation.width) / 2
            padding_top = padding_bottom = (region_h - allocation.height) / 2

            halign = child.get_halign()
            valign = child.get_valign()

            if halign == Gtk.Align.START:
                allocation.x = monitor_rect.x + padding_left
            elif halign == Gtk.Align.CENTER:
                allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (allocation.width / 2)
            elif halign == Gtk.Align.END:
                allocation.x = monitor_rect.x + monitor_rect.width - allocation.width - padding_right

            if valign == Gtk.Align.START:
                allocation.y = monitor_rect.y + padding_top
            elif valign == Gtk.Align.CENTER:
                allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (allocation.height / 2)
            elif valign == Gtk.Align.END:
                allocation.y = monitor_rect.y + monitor_rect.height - allocation.height - padding_bottom

            return True

        if isinstance(child, AudioPanel):
            """
            The AudioPanel is only shown when Awake, and attaches
            itself to the upper-left corner of the active monitor.
            """
            min_rect, nat_rect = child.get_preferred_size()

            if status.Awake:
                current_monitor = status.screen.get_mouse_monitor()
                monitor_rect = status.screen.get_monitor_geometry(current_monitor)
                allocation.x = monitor_rect.x
                allocation.y = monitor_rect.y
                allocation.width = nat_rect.width
                allocation.height = nat_rect.height
            else:
                allocation.x = child.rect.x
                allocation.y = child.rect.y
                allocation.width = nat_rect.width
                allocation.height = nat_rect.height

            return True

        if isinstance(child, InfoPanel):
            """
            The InfoPanel can be shown while not Awake, but will only appear if a) We have received
            notifications while the screensaver is running, or b) we're either on battery
            or plugged in but with a non-full battery.  It attaches itself to the upper-right
            corner of the monitor.
            """
            min_rect, nat_rect = child.get_preferred_size()

            if status.Awake:
                current_monitor = status.screen.get_mouse_monitor()
                monitor_rect = status.screen.get_monitor_geometry(current_monitor)
                allocation.x = monitor_rect.x + monitor_rect.width - nat_rect.width
                allocation.y = monitor_rect.y
                allocation.width = nat_rect.width
                allocation.height = nat_rect.height
            else:
                allocation.x = child.rect.x + child.rect.width - nat_rect.width
                allocation.y = child.rect.y
                allocation.width = nat_rect.width
                allocation.height = nat_rect.height

            return True

        if isinstance(child, OnScreenKeyboard):
            """
            The InfoPanel can be shown while not Awake, but will only appear if a) We have received
            notifications while the screensaver is running, or b) we're either on battery
            or plugged in but with a non-full battery.  It attaches itself to the upper-right
            corner of the monitor.
            """
            min_rect, nat_rect = child.get_preferred_size()

            current_monitor = status.screen.get_mouse_monitor()
            monitor_rect = status.screen.get_monitor_geometry(current_monitor)
            allocation.x = monitor_rect.x
            allocation.y = monitor_rect.y + monitor_rect.height - (monitor_rect.height / 3)
            allocation.width = monitor_rect.width
            allocation.height = monitor_rect.height / 3

            return True

        return False
