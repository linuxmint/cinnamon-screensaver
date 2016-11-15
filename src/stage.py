#! /usr/bin/python3

from gi.repository import Gtk, Gdk, CScreensaver
import random

import status
import constants as c
import singletons
from monitorView import MonitorView
from unlock import UnlockDialog
from clock import ClockWidget
from albumArt import AlbumArt
from audioPanel import AudioPanel
from infoPanel import InfoPanel
from floating import ALIGNMENTS
from util import utils, trackers, settings
from util.fader import Fader
from util.eventHandler import EventHandler

class Stage(Gtk.Window):
    """
    The Stage is the toplevel window of the entire screensaver while
    in Active mode.

    It's the first thing made, the last thing destroyed, and all other
    widgets live inside of it (or rather, inside the GtkOverlay below)

    It is Gtk.WindowType.POPUP to avoid being managed/composited by muffin,
    and to prevent animation during its creation and destruction.

    The Stage reponds pretty much only to the instructions of the
    ScreensaverManager.
    """
    def __init__(self, screen, manager, away_message):
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
        self.screen = screen
        self.away_message = away_message

        self.monitors = []
        self.last_focus_monitor = -1
        self.overlay = None
        self.clock_widget = None
        self.albumart_widget = None
        self.unlock_dialog = None
        self.status_bar = None

        self.floaters = []

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

        self.update_geometry()
        self.set_opacity(0.0)

        self.overlay = Gtk.Overlay()
        self.fader = Fader(self)

        trackers.con_tracker_get().connect(self.overlay,
                                           "realize",
                                           self.on_realized)

        trackers.con_tracker_get().connect(self.overlay,
                                           "get-child-position",
                                           self.position_overlay_child)

        self.overlay.show_all()
        self.add(self.overlay)

        # We hang onto the UPowerClient here so power events can
        # trigger changes to and from low-power mode (no plugins.)
        self.power_client = singletons.UPowerClient

        # This filter suppresses any other windows that might share
        # our window group in muffin, from showing up over the Stage.
        # For instance: Chrome and Firefox native notifications.
        self.gdk_filter = CScreensaver.GdkEventFilter()

        trackers.con_tracker_get().connect(self.screen,
                                           "monitors-changed",
                                           self.on_screen_changed)

        trackers.con_tracker_get().connect(self.screen,
                                           "size-changed",
                                           self.on_screen_changed)

    def on_screen_changed(self, screen, data=None):
        self.update_geometry()
        self.size_to_screen()

        for monitor in self.monitors:
            monitor.update_geometry()

        self.overlay.queue_resize()

    def transition_in(self, effect_time, callback):
        """
        This is the primary way of making the Stage visible.
        """
        self.realize()
        self.fader.fade_in(effect_time, callback)

    def transition_out(self, effect_time, callback):
        """
        This is the primary way of destroying the stage.  This can
        end up being called multiple times, so we keep track of if we've
        already started a transition, and ignore further calls.
        """
        if self.destroying:
            return

        self.destroying = True

        self.fader.cancel()

        if utils.have_gtk_version("3.18.0"):
            self.fader.fade_out(effect_time, callback)
        else:
            self.hide()
            callback()

    def on_realized(self, widget):
        """
        Repositions the window when it is realized, to cover the entire
        GdkScreen (a rectangle exactly encompassing all monitors.)

        From here we also proceed to construct all overlay children and
        activate our window suppressor.
        """
        self.size_to_screen()
        self.setup_children()

        self.gdk_filter.start(self)

    def size_to_screen(self):
        window = self.get_window()

        utils.override_user_time(window)
        window.move_resize(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

    def setup_children(self):
        """
        Creates all of our overlay children.  If a new 'widget' gets added,
        this should be the setup point for it.
        """
        self.setup_monitors()
        self.setup_clock()
        self.setup_albumart()
        self.setup_unlock()
        self.setup_status_bars()

    def destroy_stage(self):
        """
        Performs all tear-down necessary to destroy the Stage, destroying
        all children in the process, and finally destroying itself.
        """
        trackers.con_tracker_get().disconnect(singletons.Backgrounds,
                                              "changed",
                                              self.on_bg_changed)

        trackers.con_tracker_get().disconnect(self.power_client,
                                              "power-state-changed",
                                              self.on_power_state_changed)

        self.set_timeout_active(None, False)

        self.destroy_monitor_views()

        self.fader = None

        self.unlock_dialog.destroy()
        self.clock_widget.destroy()
        self.albumart_widget.destroy()
        self.info_panel.destroy()
        self.audio_panel.destroy()

        self.unlock_dialog = None
        self.clock_widget = None
        self.albumart_widget = None
        self.info_panel = None
        self.audio_panel = None
        self.away_message = None
        self.monitors = []
        self.floaters = []

        self.gdk_filter.stop()
        self.gdk_filter = None

        trackers.con_tracker_get().disconnect(self.screen,
                                              "monitors-changed",
                                              self.on_screen_changed)

        trackers.con_tracker_get().disconnect(self.screen,
                                              "size-changed",
                                              self.on_screen_changed)

        self.destroy()

    def setup_monitors(self):
        """
        Iterate through the monitors, and create MonitorViews for each one
        to cover them.
        """
        self.monitors = []

        n = self.screen.get_n_monitors()

        for index in range(n):
            monitor = MonitorView(self.screen, index)

            image = Gtk.Image()

            singletons.Backgrounds.create_and_set_gtk_image (image,
                                                             monitor.rect.width,
                                                             monitor.rect.height)

            monitor.set_initial_wallpaper_image(image)

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

        This is in two parts - it looks nicer to reveal/hide the info panel
        only after the MonitorView changes, so we attach to a MonitorView signal
        temporarily, which tells us then any animation is complete.
        """
        trackers.con_tracker_get().connect(self.monitors[0],
                                           "current-view-change-complete",
                                           self.after_power_state_changed)

        self.update_monitor_views()

    def after_power_state_changed(self, monitor):
        """
        Update the visibility of the InfoPanel after updating the MonitorViews
        """
        trackers.con_tracker_get().disconnect(monitor,
                                              "current-view-change-complete",
                                              self.after_power_state_changed)

        self.info_panel.update_revealed()

    def setup_clock(self):
        """
        Construct the clock widget and add it to the overlay, but only actually
        show it if we're a) Not running a plug-in, and b) The user wants it via
        preferences.

        Initially invisible, regardless - its visibility is controlled via its
        own positioning timer.
        """
        self.clock_widget = ClockWidget(self.screen, self.away_message, utils.get_mouse_monitor())
        self.add_child_widget(self.clock_widget)

        self.floaters.append(self.clock_widget)

        if not settings.should_show_plugin() and settings.get_show_clock():
            self.clock_widget.start_positioning()

    def setup_albumart(self):
        """
        Construct the AlbumArt widget and add it to the overlay, but only actually
        show it if we're a) Not running a plug-in, and b) The user wants it via
        preferences.

        Initially invisible, regardless - its visibility is controlled via its
        own positioning timer.
        """
        self.albumart_widget = AlbumArt(self.screen, self.away_message, utils.get_mouse_monitor())
        self.add_child_widget(self.albumart_widget)

        self.floaters.append(self.clock_widget)

        if not settings.should_show_plugin() and settings.get_show_albumart():
            self.albumart_widget.start_positioning()

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
                                           "auth-success",
                                           self.authentication_result_callback, True)
        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "auth-failure",
                                           self.authentication_result_callback, False)

    def setup_status_bars(self):
        """
        Constructs the AudioPanel and InfoPanel and adds them to the overlay.
        """
        self.audio_panel = AudioPanel(self.screen)
        self.add_child_widget(self.audio_panel)

        self.info_panel = InfoPanel(self.screen)
        self.add_child_widget(self.info_panel)

        trackers.con_tracker_get().connect(self.power_client,
                                           "power-state-changed",
                                           self.on_power_state_changed)

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
        if active:
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
        self.manager.cancel_unlock_widget()

        return False

    def authentication_result_callback(self, dialog, success):
        """
        Called by authentication success or failure.  Either starts
        the stage despawning process or simply 'blinks' the unlock
        widget, depending on the outcome.
        """
        if success:
            self.clock_widget.hide()
            self.albumart_widget.hide()
            self.unlock_dialog.hide()
            self.manager.unlock()
        else:
            self.unlock_dialog.blink()

    def set_message(self, msg):
        """
        Passes along an away-message to the clock.
        """
        self.clock_widget.set_message(msg)

    def raise_unlock_widget(self):
        """
        Bring the unlock widget to the front and make sure it's visible.

        This is done in two steps - we don't want to show anything over a plugin
        (graphic glitches abound) - so we update the MonitorViews first, then do
        our other reveals after its transition is complete.
        """
        self.reset_timeout()

        if status.Awake:
            return

        self.clock_widget.stop_positioning()
        self.albumart_widget.stop_positioning()

        status.Awake = True

        # Connect to one of our monitorViews (we have at least one always), to wait for
        # its transition to finish before running after_wallpaper_shown_for_unlock()
        trackers.con_tracker_get().connect(self.monitors[0],
                                           "current-view-change-complete",
                                           self.after_wallpaper_shown_for_unlock)

        self.update_monitor_views()

    def after_wallpaper_shown_for_unlock(self, monitor, data=None):
        """
        Finish raising the unlock widget - also bring up our status bars if applicable.
        """
        trackers.con_tracker_get().disconnect(monitor,
                                              "current-view-change-complete",
                                              self.after_wallpaper_shown_for_unlock)

        self.clock_widget.reveal()
        self.albumart_widget.reveal()
        self.unlock_dialog.reveal()
        self.audio_panel.reveal()
        self.info_panel.update_revealed()

    def cancel_unlock_widget(self):
        """
        Hide the unlock widget (and others) if the unlock has been canceled

        This process is in three steps for aesthetic reasons - 
            a) Unreveal all widgets (begin fading them out)
            b) Switch over MonitorViews from wallpaper to plug-ins if needed.
            c) Re-reveal the InfoPanel if applicable
        """
        if not status.Awake:
            return

        self.set_timeout_active(None, False)

        trackers.con_tracker_get().connect(self.unlock_dialog,
                                           "notify::child-revealed",
                                           self.after_unlock_unrevealed)
        self.unlock_dialog.unreveal()
        self.clock_widget.unreveal()
        self.albumart_widget.unreveal()
        self.audio_panel.unreveal()
        self.info_panel.unreveal()

    def after_unlock_unrevealed(self, obj, pspec):
        """
        Called after unlock unreveal is complete.  Tells the MonitorViews
        to update themselves.
        """
        self.unlock_dialog.hide()
        self.unlock_dialog.cancel()
        self.audio_panel.hide()
        self.clock_widget.hide()
        self.albumart_widget.hide()

        trackers.con_tracker_get().disconnect(self.unlock_dialog,
                                              "notify::child-revealed",
                                              self.after_unlock_unrevealed)

        status.Awake = False

        trackers.con_tracker_get().connect(self.monitors[0],
                                           "current-view-change-complete",
                                           self.after_transitioned_back_to_sleep)

        self.update_monitor_views()

    def after_transitioned_back_to_sleep(self, monitor, data=None):
        """
        Called after the MonitorViews have updated - re-show the clock (if desired)
        and the InfoPanel (if required.)
        """
        trackers.con_tracker_get().disconnect(monitor,
                                              "current-view-change-complete",
                                              self.after_transitioned_back_to_sleep)

        self.info_panel.update_revealed()

        if not status.PluginRunning:
            if settings.get_show_clock():
                self.clock_widget.start_positioning()
            if settings.get_show_albumart():
                self.albumart_widget.start_positioning()

    def update_monitor_views(self):
        """
        Updates all of our MonitorViews based on the power
        or Awake states.
        """
        low_power = not self.power_client.plugged_in

        for monitor in self.monitors:
            monitor.update_view(status.Awake, low_power)

            if not monitor.get_reveal_child():
                monitor.reveal()

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
        GdkScreen size
        """
        self.rect = Gdk.Rectangle()
        self.rect.x = 0
        self.rect.y = 0
        self.rect.width = self.screen.get_width()
        self.rect.height = self.screen.get_height()

        hints = Gdk.Geometry()
        hints.min_width = self.rect.width
        hints.min_height = self.rect.height
        hints.max_width = self.rect.width
        hints.max_height = self.rect.height
        hints.base_width = self.rect.width
        hints.base_height = self.rect.height

        self.set_geometry_hints(self, hints, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE | Gdk.WindowHints.BASE_SIZE)

# Overlay window management

    def maybe_update_layout(self):
        """
        Called on all user events, moves widgets to the currently
        focused monitor if it changes (whichever monitor the mouse is in)
        """
        current_focus_monitor = utils.get_mouse_monitor()

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
            monitor = utils.get_mouse_monitor()
            monitor_rect = self.screen.get_monitor_geometry(monitor)

            min_rect, nat_rect = child.get_preferred_size()

            allocation.width = nat_rect.width
            allocation.height = nat_rect.height

            allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (nat_rect.width / 2)
            allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)

            return True

        if isinstance(child, ClockWidget) or isinstance(child, AlbumArt):
            """
            ClockWidget and AlbumArt behave differently depending on if status.Awake is True or not.

            The widgets' halign and valign properties are used to store their gross position on the
            monitor.  This limits the number of possible positions to (3 * 3 * n_monitors) when our
            screensaver is not Awake, and the widgets have an internal timer that randomizes halign,
            valign, and current monitor every so many seconds, calling a queue_resize on itself after
            each timer tick (which forces this function to run).
            """
            min_rect, nat_rect = child.get_preferred_size()

            current_monitor = child.current_monitor

            if status.Awake:
                """
                If we're Awake, force the clock to track to the active monitor, and be aligned to
                the left-center.  The albumart widget aligns right-center.
                """
                if isinstance(child, ClockWidget):
                    child.set_halign(Gtk.Align.START)
                else:
                    child.set_halign(Gtk.Align.END)
                child.set_valign(Gtk.Align.CENTER)
                current_monitor = utils.get_mouse_monitor()
            else:
                for floater in self.floaters:
                    """
                    Don't let our floating widgets end up in the same spot.
                    """
                    if floater is child:
                        continue
                    if floater.get_halign() != child.get_halign() and floater.get_valign() != child.get_valign():
                        continue

                    fa = floater.get_halign()
                    ca = child.get_halign()
                    while fa == ca:
                        ca = ALIGNMENTS[random.randint(0, 2)]
                    child.set_halign(ca)

                    fa = floater.get_valign()
                    ca = child.get_valign()
                    while fa == ca:
                        ca = ALIGNMENTS[random.randint(0, 2)]
                    child.set_valign(ca)

            monitor_rect = self.screen.get_monitor_geometry(current_monitor)

            allocation.width = nat_rect.width
            allocation.height = nat_rect.height

            halign = child.get_halign()
            valign = child.get_valign()

            if halign == Gtk.Align.START:
                allocation.x = monitor_rect.x
            elif halign == Gtk.Align.CENTER:
                allocation.x = monitor_rect.x + (monitor_rect.width / 2) - (nat_rect.width / 2)
            elif halign == Gtk.Align.END:
                allocation.x = monitor_rect.x + monitor_rect.width - nat_rect.width

            if valign == Gtk.Align.START:
                allocation.y = monitor_rect.y
            elif valign == Gtk.Align.CENTER:
                allocation.y = monitor_rect.y + (monitor_rect.height / 2) - (nat_rect.height / 2)
            elif valign == Gtk.Align.END:
                allocation.y = monitor_rect.y + monitor_rect.height - nat_rect.height

            return True

        if isinstance(child, AudioPanel):
            """
            The AudioPanel is only shown when Awake, and attaches
            itself to the upper-left corner of the active monitor.
            """
            min_rect, nat_rect = child.get_preferred_size()

            if status.Awake:
                current_monitor = utils.get_mouse_monitor()
                monitor_rect = self.screen.get_monitor_geometry(current_monitor)
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
            The InfoPanel can be shown while not Awake, but only if we're not running
            a screensaver plugin.  In any case, it will only appear if a) We have received
            notifications while the screensaver is running, or b) we're either on battery
            or plugged in but with a non-full battery.  It attaches itself to the upper-right
            corner of the monitor.
            """
            min_rect, nat_rect = child.get_preferred_size()

            if status.Awake:
                current_monitor = utils.get_mouse_monitor()
                monitor_rect = self.screen.get_monitor_geometry(current_monitor)
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


        return False
