lib_LTLIBRARIES = libcscreensaver.la

dbus_built_sources =\
	cscreensaver-cinnamon-proxy.c \
    cscreensaver-cinnamon-proxy.h \
    cscreensaver-session-presence-proxy.c \
    cscreensaver-session-presence-proxy.h \
    cscreensaver-screensaver-proxy.c \
    cscreensaver-screensaver-proxy.h \
    cscreensaver-notifications-proxy.c \
    cscreensaver-notifications-proxy.h \
    cscreensaver-upower-proxy.c \
    cscreensaver-upower-proxy.h \
    cscreensaver-upower-device-proxy.c \
    cscreensaver-upower-device-proxy.h \
    cscreensaver-logind-manager-proxy.c \
    cscreensaver-logind-manager-proxy.h \
    cscreensaver-logind-session-proxy.c \
    cscreensaver-logind-session-proxy.h \
    cscreensaver-consolekit-manager-proxy.c \
    cscreensaver-consolekit-manager-proxy.h \
    cscreensaver-consolekit-session-proxy.c \
    cscreensaver-consolekit-session-proxy.h \
    cscreensaver-keybinding-handler-proxy.c \
    cscreensaver-keybinding-handler-proxy.h

cscreensaver-cinnamon-proxy.h : Makefile.am org.Cinnamon.xml
	gdbus-codegen										\
		--annotate "org.Cinnamon" org.gtk.GDBus.C.Name "Cinnamon"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-cinnamon-proxy	\
		org.Cinnamon.xml							\
		$(NULL)
cscreensaver-cinnamon-proxy.c : cscreensaver-cinnamon-proxy.h

cscreensaver-session-presence-proxy.h : Makefile.am org.gnome.SessionManager.Presence.xml
	gdbus-codegen										\
		--annotate "org.gnome.SessionManager.Presence" org.gtk.GDBus.C.Name "SessionPresence"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-session-presence-proxy	\
		org.gnome.SessionManager.Presence.xml							\
		$(NULL)
cscreensaver-session-presence-proxy.c : cscreensaver-session-presence-proxy.h

cscreensaver-notifications-proxy.h : Makefile.am org.freedesktop.Notifications.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.Notifications" org.gtk.GDBus.C.Name "Notifications"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-notifications-proxy	\
		org.freedesktop.Notifications.xml							\
		$(NULL)
cscreensaver-notifications-proxy.c : cscreensaver-notifications-proxy.h

cscreensaver-upower-proxy.h : Makefile.am org.freedesktop.UPower.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.UPower" org.gtk.GDBus.C.Name "UPower"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-upower-proxy	\
		--annotate "org.freedesktop.UPower.EnumerateDevices()[devices]" org.gtk.GDBus.C.ForceGVariant true \
		org.freedesktop.UPower.xml							\
		$(NULL)
cscreensaver-upower-proxy.c : cscreensaver-upower-proxy.h

cscreensaver-upower-device-proxy.h : Makefile.am org.freedesktop.UPower.Device.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.UPower.Device" org.gtk.GDBus.C.Name "UPowerDevice"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-upower-device-proxy	\
		org.freedesktop.UPower.Device.xml							\
		$(NULL)
cscreensaver-upower-device-proxy.c : cscreensaver-upower-device-proxy.h

cscreensaver-logind-manager-proxy.h : Makefile.am org.freedesktop.login1.Manager.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.login1.Manager" org.gtk.GDBus.C.Name "LogindManager"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-logind-manager-proxy	\
		org.freedesktop.login1.Manager.xml							\
		$(NULL)
cscreensaver-logind-manager-proxy.c : cscreensaver-logind-manager-proxy.h

cscreensaver-logind-session-proxy.h : Makefile.am org.freedesktop.login1.Session.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.login1.Session" org.gtk.GDBus.C.Name "LogindSession"		\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-logind-session-proxy	\
		org.freedesktop.login1.Session.xml							\
		$(NULL)
cscreensaver-logind-session-proxy.c : cscreensaver-logind-session-proxy.h

cscreensaver-consolekit-manager-proxy.h : Makefile.am org.freedesktop.ConsoleKit.Manager.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.ConsoleKit.Manager" org.gtk.GDBus.C.Name "ConsoleKitManager"	\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-consolekit-manager-proxy	\
		org.freedesktop.ConsoleKit.Manager.xml							\
		$(NULL)
cscreensaver-consolekit-manager-proxy.c : cscreensaver-consolekit-manager-proxy.h

cscreensaver-consolekit-session-proxy.h : Makefile.am org.freedesktop.ConsoleKit.Session.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.ConsoleKit.Session" org.gtk.GDBus.C.Name "ConsoleKitSession"	\
		--c-namespace CScreensaver						\
		--generate-c-code cscreensaver-consolekit-session-proxy	\
		org.freedesktop.ConsoleKit.Session.xml							\
		$(NULL)
cscreensaver-consolekit-session-proxy.c : cscreensaver-consolekit-session-proxy.h

cscreensaver-screensaver-proxy.h : Makefile.am org.cinnamon.ScreenSaver.xml
	gdbus-codegen                                       \
        --annotate "org.cinnamon.ScreenSaver" org.gtk.GDBus.C.Name "ScreenSaver"    \
        --c-namespace CScreensaver                      \
        --generate-c-code cscreensaver-screensaver-proxy \
        org.cinnamon.ScreenSaver.xml                          \
        $(NULL)
cscreensaver-screensaver-proxy.c : cscreensaver-screensaver-proxy.h

cscreensaver-keybinding-handler-proxy.h : Makefile.am org.cinnamon.SettingsDaemon.KeybindingHandler.xml
	gdbus-codegen                                       \
        --annotate "org.cinnamon.SettingsDaemon.KeybindingHandler" org.gtk.GDBus.C.Name "KeybindingHandler" \
        --c-namespace CScreensaver                      \
        --generate-c-code cscreensaver-keybinding-handler-proxy   \
        org.cinnamon.SettingsDaemon.KeybindingHandler.xml                           \
        $(NULL)
cscreensaver-keybinding-handler-proxy.c : cscreensaver-keybinding-handler-proxy.h

libcscreensaver_la_CPPFLAGS =            \
    $(WARN_CFLAGS)          \
    $(CSCREENSAVER_CFLAGS)           \
    -I$(srcdir)         \
    -DWITH_INTROSPECTION        \
    -DG_LOG_DOMAIN="\"CScreensaver\""

libcscreensaver_la_gir_sources =             \
    cscreensaver-gdk-event-filter.c \
    cscreensaver-gdk-event-filter.h \
    $(dbus_built_sources) \
    $(NULL)

libcscreensaver_la_SOURCES =             \
    $(libcscreensaver_la_gir_sources)        \
    $(NULL)

libcscreensaver_la_LIBADD =  \
    $(CSCREENSAVER_LIBS) \
    $(NULL)

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = cscreensaver.pc

include $(INTROSPECTION_MAKEFILE)

INTROSPECTION_SCANNER_ARGS = --add-include-path=$(srcdir) --warn-all
INTROSPECTION_COMPILER_ARGS = --includedir=$(srcdir)

CScreensaver-1.0.gir: libcscreensaver.la
CScreensaver_1_0_gir_INCLUDES = Gtk-3.0
CScreensaver_1_0_gir_CFLAGS = $(INCLUDES) -I$(top_srcdir)/libcscreensaver -DWITH_INTROSPECTION
CScreensaver_1_0_gir_LIBS = libcscreensaver.la
CScreensaver_1_0_gir_SCANNERFLAGS = --identifier-prefix=CScreensaver --symbol-prefix=cscreensaver_
CScreensaver_1_0_gir_FILES = $(libcscreensaver_la_gir_sources)
INTROSPECTION_GIRS = CScreensaver-1.0.gir

girdir = $(datadir)/gir-1.0
gir_DATA = CScreensaver-1.0.gir

typelibdir = $(libdir)/girepository-1.0
typelib_DATA = $(INTROSPECTION_GIRS:.gir=.typelib)

CLEANFILES = $(gir_DATA) \
             $(typelib_DATA) \
             $(dbus_built_sources)

MAINTAINERCLEANFILES =          \
    Makefile.in

EXTRA_DIST = \
    cscreensaver.pc.in          \
    cscreensaver-uninstalled.pc.in \
    org.cinnamon.Screensaver.xml \
    org.Cinnamon.xml \
	org.freedesktop.ConsoleKit.Manager.xml \
	org.freedesktop.ConsoleKit.Session.xml \
	org.freedesktop.Notifications.xml \
	org.freedesktop.UPower.Device.xml \
	org.freedesktop.UPower.xml \
	org.gnome.SessionManager.Presence.xml
