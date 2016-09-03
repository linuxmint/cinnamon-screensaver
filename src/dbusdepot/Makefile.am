## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS = 

appdir = $(datadir)/cinnamon-screensaver/dbusdepot

app_PYTHON = \
        __init__.py \
        baseClient.py \
        cinnamonClient.py \
        consoleKitClient.py \
        keybindingHandlerClient.py \
        logindClient.py \
        loginInterface.py \
        mediaPlayerWatcher.py \
        screensaverClient.py \
        sessionClient.py \
        uPowerClient.py \
        $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
