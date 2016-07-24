#NOTE:
currently requires https://github.com/mtwebster/cinnamon-desktop/tree/new-screensaver

How does it work?

### Program Entry

Main entry is from /usr/bin/cinnamon-screensaver to cinnamon-screensaver-main.py, which
launches a dbus service (org.cinnamon.Screensaver)

service.py launches the ScreensaverManager (manager.py), which is central command for all things here, as well as a session proxy to listen for idle changes from cinnamon-session.

### Running (listening state)
At this point we're listening, either for a command sent by the user (like via cinnamon-screensaver-command) or from the session manager proxy.

### Locking (active)
Once a lock command is received, the manager spawns a main window (ScreensaverOverlay in overlay.py) which covers the entire Gdk screen size (an imaginary rectangle containing all monitors).

Think of this overlay as very basic window manager.  Into this overlay it places:

- ScreensaverWindows (window.py) - one for each monitor, painted with the user's background, placed
  at the exact location of each window.
- A clock widget, which bounces around mostly randomly around all monitors
- An unlock widget, which is initially hidden

At this point we're also now setup to receive user events like button and key presses, and motion events.  This is assisted by GrabHelpers (grabhelper.py) that ensure only those keystrokes we want are allowed, and muffin is blocked from processing global keybindings.

- Any motion is a wake event (show the unlock widget)
- Any click is a wake event (ditto)
- Keypresses are first filtered - media keys are checked, and things like volume, brightness controls
  will not raise the unlock dialog (for now, only if they're simple key combinations - complex ones
  with modifiers will still do it)
- key strokes for characters will be forwarded to the dialog - if you start typing your password on a
  blank screensaver screen, it will be forwarded to the password entry.

### Unlocking
Once the user types their password and hits enter or clicks unlock, a pam service (pam-helper-service.py) is called to authenticate.  A service is used, as pam communications
don't thread properly, and it blocks the UI when authenticating.  In the event the service isn't
available, a blocking method is used to authenticate.

If the authentication is successful, all widgets are destroyed, all grabs released, and we go back
to the idle listening state.

### To do
- ~~gsettings, use existing settings where applicable,~~ consider refactoring of how screensaver/power
  stuff is presented to the user
- ~~notifications need tested - do they appear over the screensaver?~~
- add music player widget?  Show album art, etc..?
- make switch user/logout more robust
- implement motion event threshold - don't wake unless mouse has been moved XX pixels
- security testing... try to break it
- ~~re-add xscreensaver stuff~~
- ~~fix some spaghetti~~

