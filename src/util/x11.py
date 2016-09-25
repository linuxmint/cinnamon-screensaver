#! /usr/bin/python3

from Xlib import display, X

def nuke_focus():
    """
    Used by GrabHelper (only if python3-xlib is available) to help
    break a grab.  Usually never reached.
    """
    print("screensaver - x11 - nuking focus")
    xdisplay = display.Display()
    ret = xdisplay.get_input_focus()

    xdisplay.set_input_focus(X.NONE, X.RevertToNone, X.CurrentTime, None)
