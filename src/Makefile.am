## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS =

desktopdir = $(datadir)/applications
desktop_in_files = cinnamon-screensaver.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

appdir = $(datadir)/cinnamon-screensaver

app_PYTHON = \
        __init__.py \
        authenticator.py \
        baseWindow.py \
        clock.py \
        config.py \
        constants.py \
        eventHandler.py \
        fader.py \
        grabHelper.py \
        keybindings.py \
        manager.py \
        monitorView.py \
        overlay.py \
        service.py \
        sessionProxy.py \
        settings.py \
        status.py \
        trackers.py \
        unlock.py \
        utils.py \
        x11.py

app_SCRIPTS = cinnamon-screensaver-main.py \
              cinnamon-screensaver-command.py \
              pam-helper-service.py

%:%.in Makefile
	$(AM_V_GEN)sed                  \
        -e s!\@datadir\@!$(datadir)!        \
        < $< > $@

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

all-local: config.py cinnamon-screensaver cinnamon-screensaver-pam-helper cinnamon-screensaver-command

bin_SCRIPTS = cinnamon-screensaver cinnamon-screensaver-pam-helper cinnamon-screensaver-command

EXTRA_DIST =                \
    cinnamon-screensaver-pam-helper.in \
    cinnamon-screensaver.desktop.in \
    cinnamon-screensaver.in \
    config.py.in \
    debug-screensaver.sh        \
    $(NULL)

CLEANFILES =                \
    cinnamon-screensaver.desktop.in

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
