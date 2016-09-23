### To do
- ~~Add GdkFilter to prevent new windows raising themselves above the stage~~
- ~~Gtk 3.20.. make a new CSS file, do a check at startup which file to use based on gtk version check~~
- ~~Make styling work at fallback provider priority (1 instead of 600)~~
- ~~clock positioning broken in Gtk 3.20 (widget.queue_resize instead of widget.queue_draw to trigger GtkOverlay~~
  ~~redraws, but still issues?)~~
- ~~add music player widget?  Next to volume, track info, position (read-only) or time, 3 buttons (pause-forw-back)~~
- security testing... try to break it
- add our own flag gsettings key to org.cinnamon.desktop.screensaver, instead of using libgnomekbd?  it's a dependency
  anyhow.  Add user setting for this as well?
- Evaluate allowed keybindings - add more?  Some missing? (keybindings.py)
- ~~No boxes around infobar widgets?  just a separator maybe, or nothing..~~
- monitor window urgent/demands-attention hints - add to info bar?
- ~~Evaluate throttle - it's in the freedesktop spec.. idea being, you don't want a plugin screensaver running while 
  you're on battery.  Since we talk to upower, we can implement this ourselves, or let our session manager tell us
  when to throttle back/throttle forward (plug in, switch back to x plugin or whatever?)~~
- ~~keep track of last keyboard layout used in the unlocker, use that one by default (keeps user from having to switch
  repeatedly when unlocking, while using a different input layout in general)~~


How does it work?

### Program Entry

Main entry is from /usr/bin/cinnamon-screensaver to cinnamon-screensaver-main.py, which
launches a dbus service (org.cinnamon.Screensaver)

service.py launches the ScreensaverManager (manager.py), which is central command for all things here, as well as a
session proxy to listen for idle changes from cinnamon-session, and logind or consolekit proxues.

### Running
At this point we're listening, either for a command sent by the user (like via cinnamon-screensaver-command) or from one
of our proxies.

### Locking (active)
Once a lock command is received, the manager spawns a main window (Stage in stage.py) which covers the entire Gdk screen
size (an imaginary rectangle containing all monitors).

Think of this overlay as very basic window manager.  Into this overlay it places:

- MonitorViews (monitorView.py) - one for each monitor, painted with the user's background, placed
  at the exact location of each window.
- A clock widget, which bounces around mostly randomly around all monitors
- An unlock widget, which is initially hidden

At this point we're also now setup to receive user events like button and key presses, and motion events.  This is assisted by the GrabHelper and EventHandler that ensure only those keystrokes we want are allowed, and muffin is blocked from processing global keybindings.

- Any motion is a wake event (show the unlock widget or kill the stage if we're not locked)
- Any click is a wake event (ditto)
- Keypresses are first filtered - media keys are checked, and things like volume, brightness controls
  will not raise the unlock dialog (for now, only if they're simple key combinations - complex ones
  with modifiers will still do it)
- key strokes for characters will be forwarded to the dialog - if you start typing your password on a
  blank screensaver screen, it will be forwarded to the password entry.

### Unlocking
Once the user types their password and hits enter or clicks unlock, we authenticate via a pam helper in cinnamon-desktop.

If the authentication is successful, all widgets are destroyed, all grabs released, and we go back
to the idle listening state.

Files:

application.css:  Application priority css, stuff to make the unlock dialog, clock widgets look ok against
varying backgrounds

cinnamon-screensaver-command.py:  Send commands to the screensaver via the command line

cinnamon-screensaver-main.py: Main entry point into the program, handles a couple of arguments, adds our css provider, fires up the ScreensaverService.

baseWindow.py: A base revealer class that the Clock and Unlock widgets implement - any widget that will move around the Stage should implement this (except the monitorViews) - the revealer base lets you do simple fade-ins and fade-outs.

cinnamonProxy.py: Connects to Cinnamon's dbus interface, asks Cinnamon to make sure expo or overview are closed (as they make a server grab that we can't wrest focus from, preventing the screensaver from activating).

clock.py (inherits BaseWindow): The clock widget that bounces around the screen, this contains all of that.  Positioning is done via a randomizer on a timer that adjusts vertical and horizontal alignment properties (one of
start, center, or end) along with current monitor, which is used by the Stage positioning function to tell it where to place the Clock widget.

config.py.in (compiles into config.py): Contains system-specific file locations that are used by various files here.

consoleKitProxy.py: Listens to commands from consolekit over dbus

constants.py: A file containing simply a list of hardcoded screens/values that various files here use.

eventHandler.py: Gets forwarded all events received from various sources, and acts on them.  Does not propagate except
in the case of motion.

fader.py: A helper for the Stage that uses a frame tick callback to fade the stage in our out over a specific timeframe.  Since it uses the frame clock instead of a GSource, times remain consistent, and only as many frames are drawn as there is time for (a 1 second animation will take one second, but you might not see all 60 frame draws)

focusNavigator.py: A helper for navigating focus and performing activation on the navigable widgets on the unlock screen.  Since we funnel events so strictly, and don't perform any propagation (to prevent wm or desktop keybindings from triggering) we have to manage the focus ourselves, as well as performing activation on the focused widget when enter or space is pressed.

grabHelper.py: A helper for achieving exclusive mouse and key grabs, as well as hiding the mouse pointer when appropriate.

keybindings.py: gets fed key events from the EventHandler, and acts on them or not - allows certain media keys, handles escape, enter, space events.

logindProxy.py: Listens to commands from logind over dbus

manager.py: This is the head honcho, the big cheese, el numero uno.  It spawns the GrabHelper, FocusNavigator, along with the session and logind/ck proxies.  It acts on commands received from there, as well as our own dbus service (ScreensaverService).  It manages all the flags in status.py, spawns and despawns the stage.

monitorView.py: This is a widget that gets placed in the stage that provides the backgrounds or screensaver plugin view.  There is one per monitor, and they are positioned directly where each monitor is by the Stage positioning function.  It handles transitioning between backgrounds (during a slideshow) and transitioning between plugins and wallpaper.

service.py: This is our implementation of the dbus service "org.cinnamon.Screensaver" - commands received via this interface are sent to the manager for answers and action.  This spawns the manager.

sessionProxy.py: Listens to cinnamon-session for idle changes and notifies the manager when they change.

settings.py: holds our GSettings instances, as well as getters for each of the different keys.  Also takes care of our CinnamonDesktop BG instance, and updates it when settings change.

stage.py: This is our toplevel window, a GtkWindow.  It is made the size of the GdkScreen (a theoretical rectangle that exactly encompasses all monitors).  At its core is a GtkOverlay, which we sort of use like a window manager.  The position_overlay_child callback is used to position our children (Clock, UnlockWidget, MonitorView).  A forced call to this position function can be done via overlay.queue_resize().  This class talks fairly freely with the manager, even though it is spawned and despawned by the manager repeatedly (when the screensaver is activated/deactivated)

status.py: A global state tracker, used by many widgets - Active means the screensaver stage exists, and we're displaying wallpaper or whatever.  Locked means we will need to enter our password to unlock.  Awake means the unlock dialog is currently shown.  focusChain is where a list of focusable widgets should be stored that tab will navigate between. (This is currently done just in the UnlockDialog)

trackers.py: A utility for easy tracking of timers and signal connections.  It basically performs any cleanup for you, with no need to track source ids or signal ids generally.

unlock.py: Provides the unlock dialog, including the user image, name, password entry and buttons

utils.py: Various utilities that seem best to keep in one place.

x11.py: X11-specific focus helper function - optional, python3-xlib doesn't exist everywhere yet.

