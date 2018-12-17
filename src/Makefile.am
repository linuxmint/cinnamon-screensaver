## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS = binfiles dbusdepot widgets util pamhelper

appdir = $(datadir)/cinnamon-screensaver

app_PYTHON = \
        __init__.py \
        albumArt.py \
        audioPanel.py \
        baseWindow.py \
        clock.py \
        config.py \
        constants.py \
        floating.py \
        infoPanel.py \
        manager.py \
        monitorView.py \
        osk.py \
        passwordEntry.py \
        playerControl.py \
        service.py \
        singletons.py \
        stage.py \
        status.py \
        unlock.py \
        volumeControl.py \
        $(NULL)

app_DATA = cinnamon-screensaver-gtk3.14.css \
           cinnamon-screensaver-gtk3.18.css \
           cinnamon-screensaver-gtk3.20.css \
           $(NULL)

app_SCRIPTS = cinnamon-screensaver-main.py \
              cinnamon-screensaver-command.py \
              $(NULL)

config.py: config.py.in Makefile
	$(AM_V_GEN)sed                  \
        -e s!\@prefix\@!$(prefix)!      \
        -e s!\@datadir\@!$(datadir)!        \
        -e s!\@pkgdatadir\@!$(pkgdatadir)!  \
        -e s!\@libexecdir\@!$(libexecdir)!  \
        -e s!\@libdir\@!$(libdir)!      \
        -e s!\@PACKAGE\@!$(PACKAGE)!        \
        -e s!\@VERSION\@!$(VERSION)!        \
        -e s!\@GETTEXT_PACKAGE\@!$(GETTEXT_PACKAGE)!    \
        < $< > $@

all-local: config.py

EXTRA_DIST =                \
    config.py.in \
    debug-screensaver.sh        \
    $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
