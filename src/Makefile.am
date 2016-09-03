## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS = binfiles dbusdepot widgets util

appdir = $(datadir)/cinnamon-screensaver

app_PYTHON = \
        __init__.py \
        audioBar.py \
        baseWindow.py \
        clock.py \
        config.py \
        constants.py \
        singletons.py \
        infoBar.py \
        manager.py \
        monitorView.py \
        playerWidget.py \
        service.py \
        stage.py \
        status.py \
        unlock.py \
        volumeWidget.py \
        $(NULL)

app_DATA = application.css

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
