## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS =

appdir = $(datadir)/cinnamon-screensaver/util

app_PYTHON = \
        __init__.py \
        eventHandler.py \
        fader.py \
        focusNavigator.py \
        grabHelper.py \
        keybindings.py \
        keyboardLayout.py \
        settings.py \
        trackers.py \
        utils.py \
        x11.py

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
