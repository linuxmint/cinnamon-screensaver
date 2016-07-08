NULL =

dbussessionservicedir = $(DBUS_SESSION_SERVICE_DIR)
dbussessionservice_DATA = org.cinnamon.ScreenSaver.service \
                          org.cinnamon.ScreenSaver.PAMHelper.service

SUBDIRS = screensavers

EXTRA_DIST = 				\
	org.cinnamon.ScreenSaver.service.in \
    org.cinnamon.ScreenSaver.PAMHelper.service.in
	$(NULL)

MAINTAINERCLEANFILES =			\
	*~				\
	Makefile.in

-include $(top_srcdir)/git.mk
