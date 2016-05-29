## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

saverdir = $(libexecdir)/cinnamon-screensaver

INCLUDES =							\
	-I.							\
	-I$(srcdir)						\
	$(CINNAMON_SCREENSAVER_CFLAGS)				\
	$(CINNAMON_SCREENSAVER_DIALOG_CFLAGS)			\
	$(CINNAMON_SCREENSAVER_CAPPLET_CFLAGS)			\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	-DPREFIX=\""$(prefix)"\" 				\
	-DBINDIR=\""$(bindir)"\"				\
	-DLIBDIR=\""$(libdir)"\" 				\
	-DLIBEXECDIR=\""$(libexecdir)"\"			\
	-DDATADIR=\""$(datadir)"\"				\
	-DSYSCONFDIR=\""$(sysconfdir)"\" 			\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	-DSAVERDIR=\""$(saverdir)"\"				\
	-DGTKBUILDERDIR=\"$(pkgdatadir)\"				\
	-DPAM_SERVICE_NAME=\""cinnamon-screensaver"\"		\
	$(WARN_CFLAGS)						\
	$(AUTH_CFLAGS)						\
	$(DEBUG_CFLAGS)						\
	$(DBUS_CFLAGS)						\
	$(LIBGNOMEKBDUI_CFLAGS)					\
	$(LIBNOTIFY_CFLAGS)					\
	$(LOGIND_CFLAGS)					\
	$(NULL)

bin_PROGRAMS = \
	cinnamon-screensaver		\
	cinnamon-screensaver-command	\
	$(NULL)

libexec_PROGRAMS = \
	cinnamon-screensaver-dialog	\
	$(NULL)

noinst_PROGRAMS = 	\
	test-fade	\
	test-passwd	\
	test-watcher	\
	test-window	\
	$(NULL)

desktopdir = $(datadir)/applications
desktop_in_files = cinnamon-screensaver.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

cinnamon_screensaver_command_SOURCES = 	\
	bus.h				\
	cinnamon-screensaver-command.c	\
	$(NULL)

cinnamon_screensaver_command_LDADD =	\
	$(CINNAMON_SCREENSAVER_COMMAND_LIBS)	\
	$(NULL)

AUTH_SOURCES =				\
	gs-auth-@AUTH_SCHEME@.c		\
	$(NULL)

test_fade_SOURCES = 			\
	test-fade.c 			\
	gs-fade.c	 		\
	gs-fade.h	 		\
	gs-debug.c			\
	gs-debug.h			\
	$(NULL)

test_fade_LDADD =			\
	$(CINNAMON_SCREENSAVER_LIBS)	\
	$(SAVER_LIBS)			\
	$(NULL)

test_passwd_SOURCES = 			\
	test-passwd.c 			\
	gs-auth.h			\
	$(AUTH_SOURCES)			\
	setuid.c			\
	setuid.h			\
	subprocs.c			\
	subprocs.h			\
	$(NULL)

test_passwd_LDADD =			\
	$(CINNAMON_SCREENSAVER_DIALOG_LIBS)\
	$(AUTH_LIBS)			\
	$(NULL)

test_watcher_SOURCES =			\
	bus.h				\
	test-watcher.c			\
	gs-watcher.h			\
	gs-watcher-x11.c		\
	gs-marshal.c 			\
	gs-marshal.h			\
	gs-debug.c			\
	gs-debug.h			\
	$(NULL)

test_watcher_LDADD =			\
	$(CINNAMON_SCREENSAVER_LIBS)	\
	$(SAVER_LIBS)			\
	$(NULL)

test_window_SOURCES =			\
	test-window.c			\
    gs-lock-socket.c \
    gs-lock-socket.h \
	gs-window.h			\
	gs-window-x11.c			\
	gs-grab-x11.c			\
	gs-grab.h			\
	gs-marshal.c 			\
	gs-marshal.h			\
	gs-debug.c			\
	gs-debug.h			\
	subprocs.c			\
	subprocs.h			\
	$(NULL)

test_window_LDADD =			\
	$(CINNAMON_SCREENSAVER_LIBS)	\
	$(SAVER_LIBS)			\
	$(NULL)

cinnamon_screensaver_dialog_SOURCES = 	\
	cinnamon-screensaver-dialog.c	\
	gs-lock-plug.c			\
	gs-lock-plug.h			\
	gs-debug.c			\
	gs-debug.h			\
	setuid.c			\
	setuid.h			\
	subprocs.c			\
	subprocs.h			\
	gs-auth.h			\
	$(AUTH_SOURCES)			\
	$(NULL)

cinnamon_screensaver_dialog_LDADD =	\
	$(CINNAMON_SCREENSAVER_DIALOG_LIBS)\
	$(SAVER_LIBS)			\
	$(AUTH_LIBS)			\
	$(LIBGNOMEKBDUI_LIBS)		\
	$(LIBNOTIFY_LIBS)		\
	$(NULL)

BUILT_SOURCES = 		\
	gs-marshal.c 		\
	gs-marshal.h		\
	$(NULL)

gs-marshal.c: gs-marshal.list
	echo "#include \"gs-marshal.h\"" > $@ && \
	@GLIB_GENMARSHAL@ $< --prefix=gs_marshal --body >> $@

gs-marshal.h: gs-marshal.list
	@GLIB_GENMARSHAL@ $< --prefix=gs_marshal --header > $@

cinnamon_screensaver_SOURCES =	\
	bus.h			\
	cinnamon-screensaver.c	\
	cinnamon-screensaver.h	\
	gs-monitor.c		\
	gs-monitor.h		\
	gs-watcher-x11.c	\
	gs-watcher.h		\
	gs-listener-dbus.c	\
	gs-listener-dbus.h	\
    gs-lock-socket.c \
    gs-lock-socket.h \
	gs-manager.c		\
	gs-manager.h		\
	gs-window-x11.c		\
	gs-window.h		\
	gs-prefs.c		\
	gs-prefs.h		\
	gs-debug.c		\
	gs-debug.h		\
	subprocs.c		\
	subprocs.h		\
	gs-grab-x11.c		\
	gs-grab.h		\
	gs-fade.c		\
	gs-fade.h		\
	gnome-datetime-source.c \
	gnome-datetime-source.h \
	gnome-wall-clock.c \
	gnome-wall-clock.h \
	$(BUILT_SOURCES)	\
	$(NULL)

cinnamon_screensaver_LDADD =		\
	$(CINNAMON_SCREENSAVER_LIBS)	\
	$(SAVER_LIBS)			\
	$(LOGIND_LIBS)                 \
	$(NULL)

cinnamon_screensaver_LDFLAGS = -export-dynamic

EXTRA_DIST =				\
	debug-screensaver.sh		\
	gs-marshal.list			\
	cinnamon-screensaver.desktop.in	\
	$(NULL)

CLEANFILES = 				\
	$(desktop_DATA) 		\
	cinnamon-screensaver.desktop.in	\
	$(BUILT_SOURCES)

MAINTAINERCLEANFILES =			\
	*~				\
	Makefile.in

install-exec-hook:
	@if [ "x@NEED_SETUID@" = "xyes" ]; then \
	    echo "***" ; \
	    echo "***  Warning: cinnamon-screensaver has been compiled with support for" ; \
	    echo "***           bsdauth(3) and must be installed as a setuid root" ; \
	    echo "***           program in order for locking to work.  To do this, you" ; \
	    echo "***           must run:" ; \
	    echo "***" ; \
	    echo "***           chown root $(DESTDIR)$(libexecdir)/cinnamon-screensaver-dialog" ; \
	    echo "***           chmod +s $(DESTDIR)$(libexecdir)/cinnamon-screensaver-dialog" ; \
	    echo "***" ; \
	    echo "***           For now, it will be installed non-setuid, which" ; \
	    echo "***           means that locking might not work." ; \
	    echo "***" ; \
	fi

-include $(top_srcdir)/git.mk
