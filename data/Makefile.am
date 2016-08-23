NULL =
SUBDIRS = icons

desktopdir = $(datadir)/applications
desktop_in_files = cinnamon-screensaver.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

dbussessionservicedir = $(DBUS_SESSION_SERVICE_DIR)
dbussessionservice_DATA = org.cinnamon.ScreenSaver.service

EXTRA_DIST = 				\
    cinnamon-screensaver.desktop.in \
	org.cinnamon.ScreenSaver.service.in \
	$(NULL)

CLEANFILES =                \
    cinnamon-screensaver.desktop.in

MAINTAINERCLEANFILES =			\
	*~				\
	Makefile.in

-include $(top_srcdir)/git.mk
