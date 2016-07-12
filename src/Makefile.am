## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

desktopdir = $(datadir)/applications
desktop_in_files = cinnamon-screensaver.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

appdir = $(datadir)/cinnamon-screensaver

app_PYTHON = \
        __init__.py \
        authenticator.py \
        baseWindow.py \
        config.py \
        clock.py \
        constants.py \
        eventHandler.py \
        keybindings.py \
        unlock.py \
        manager.py \
        overlay.py \
        service.py \
        sessionProxy.py \
        trackers.py \
        utils.py \
        window.py

app_SCRIPTS = cinnamon-screensaver-main.py pam-helper-service.py

cinnamon-screensaver: cinnamon-screensaver.in
	$(AM_V_GEN)sed                  \
        -e s!\@datadir\@!$(datadir)!        \
        < $< > $@
cinnamon-screensaver: Makefile

cinnamon-screensaver-pam-helper: cinnamon-screensaver-pam-helper.in
	$(AM_V_GEN)sed                  \
        -e s!\@datadir\@!$(datadir)!        \
        < $< > $@
cinnamon-screensaver-pam-helper: Makefile

config.py: config.py.in
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
config.py: Makefile

all-local: config.py cinnamon-screensaver cinnamon-screensaver-pam-helper

bin_SCRIPTS = cinnamon-screensaver cinnamon-screensaver-pam-helper

EXTRA_DIST =                \
    debug-screensaver.sh        \
    cinnamon-screensaver.desktop.in \
    config.py.in \
    cinnamon-screensaver.in \
    cinnamon-screensaver-pam-helper.in \
    $(NULL)

CLEANFILES =                \
    cinnamon-screensaver.desktop.in

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
