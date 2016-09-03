## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS =

appdir = $(datadir)/cinnamon-screensaver/widgets

app_PYTHON = \
        __init__.py \
        blinkingLabel.py \
        marqueeLabel.py \
        notificationWidget.py \
        powerWidget.py \
        transparentButton.py \
        volumeSlider.py \
        $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
