lib_LTLIBRARIES = libcscreensaver.la

dbus_built_sources =\
	cs-cinnamon-proxy.c \
    cs-cinnamon-proxy.h \
    cs-session-presence-proxy.c \
    cs-session-presence-proxy.h \
    cs-screensaver-proxy.c \
    cs-screensaver-proxy.h \
    cs-upower-proxy.c \
    cs-upower-proxy.h \
    cs-upower-device-proxy.c \
    cs-upower-device-proxy.h \
    cs-logind-manager-proxy.c \
    cs-logind-manager-proxy.h \
    cs-logind-session-proxy.c \
    cs-logind-session-proxy.h \
    cs-consolekit-manager-proxy.c \
    cs-consolekit-manager-proxy.h \
    cs-consolekit-session-proxy.c \
    cs-consolekit-session-proxy.h \
    cs-keybinding-handler-proxy.c \
    cs-keybinding-handler-proxy.h \
    cs-media-player-proxy.c \
    cs-media-player-proxy.h

cs-cinnamon-proxy.h : Makefile.am org.Cinnamon.xml
	gdbus-codegen										\
		--annotate "org.Cinnamon" org.gtk.GDBus.C.Name "Cinnamon"		\
		--c-namespace Cs						\
		--generate-c-code cs-cinnamon-proxy	\
		org.Cinnamon.xml							\
		$(NULL)
cs-cinnamon-proxy.c : cs-cinnamon-proxy.h

cs-session-presence-proxy.h : Makefile.am org.gnome.SessionManager.Presence.xml
	gdbus-codegen										\
		--annotate "org.gnome.SessionManager.Presence" org.gtk.GDBus.C.Name "SessionPresence"		\
		--c-namespace Cs						\
		--generate-c-code cs-session-presence-proxy	\
		org.gnome.SessionManager.Presence.xml							\
		$(NULL)
cs-session-presence-proxy.c : cs-session-presence-proxy.h

cs-upower-proxy.h : Makefile.am org.freedesktop.UPower.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.UPower" org.gtk.GDBus.C.Name "UPower"		\
		--c-namespace Cs						\
		--generate-c-code cs-upower-proxy	\
		--annotate "org.freedesktop.UPower.EnumerateDevices()[devices]" org.gtk.GDBus.C.ForceGVariant true \
		org.freedesktop.UPower.xml							\
		$(NULL)
cs-upower-proxy.c : cs-upower-proxy.h

cs-upower-device-proxy.h : Makefile.am org.freedesktop.UPower.Device.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.UPower.Device" org.gtk.GDBus.C.Name "UPowerDevice"		\
		--c-namespace Cs						\
		--generate-c-code cs-upower-device-proxy	\
		org.freedesktop.UPower.Device.xml							\
		$(NULL)
cs-upower-device-proxy.c : cs-upower-device-proxy.h

cs-logind-manager-proxy.h : Makefile.am org.freedesktop.login1.Manager.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.login1.Manager" org.gtk.GDBus.C.Name "LogindManager"		\
		--c-namespace Cs						\
		--generate-c-code cs-logind-manager-proxy	\
		org.freedesktop.login1.Manager.xml							\
		$(NULL)
cs-logind-manager-proxy.c : cs-logind-manager-proxy.h

cs-logind-session-proxy.h : Makefile.am org.freedesktop.login1.Session.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.login1.Session" org.gtk.GDBus.C.Name "LogindSession"		\
		--c-namespace Cs						\
		--generate-c-code cs-logind-session-proxy	\
		org.freedesktop.login1.Session.xml							\
		$(NULL)
cs-logind-session-proxy.c : cs-logind-session-proxy.h

cs-consolekit-manager-proxy.h : Makefile.am org.freedesktop.ConsoleKit.Manager.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.ConsoleKit.Manager" org.gtk.GDBus.C.Name "ConsoleKitManager"	\
		--c-namespace Cs						\
		--generate-c-code cs-consolekit-manager-proxy	\
		org.freedesktop.ConsoleKit.Manager.xml							\
		$(NULL)
cs-consolekit-manager-proxy.c : cs-consolekit-manager-proxy.h

cs-consolekit-session-proxy.h : Makefile.am org.freedesktop.ConsoleKit.Session.xml
	gdbus-codegen										\
		--annotate "org.freedesktop.ConsoleKit.Session" org.gtk.GDBus.C.Name "ConsoleKitSession"	\
		--c-namespace Cs						\
		--generate-c-code cs-consolekit-session-proxy	\
		org.freedesktop.ConsoleKit.Session.xml							\
		$(NULL)
cs-consolekit-session-proxy.c : cs-consolekit-session-proxy.h

cs-screensaver-proxy.h : Makefile.am org.cinnamon.ScreenSaver.xml
	gdbus-codegen                                       \
        --annotate "org.cinnamon.ScreenSaver" org.gtk.GDBus.C.Name "ScreenSaver"    \
        --c-namespace Cs                      \
        --generate-c-code cs-screensaver-proxy \
        org.cinnamon.ScreenSaver.xml                          \
        $(NULL)
cs-screensaver-proxy.c : cs-screensaver-proxy.h

cs-keybinding-handler-proxy.h : Makefile.am org.cinnamon.SettingsDaemon.KeybindingHandler.xml
	gdbus-codegen                                       \
        --annotate "org.cinnamon.SettingsDaemon.KeybindingHandler" org.gtk.GDBus.C.Name "KeybindingHandler" \
        --c-namespace Cs                      \
        --generate-c-code cs-keybinding-handler-proxy   \
        org.cinnamon.SettingsDaemon.KeybindingHandler.xml                           \
        $(NULL)
cs-keybinding-handler-proxy.c : cs-keybinding-handler-proxy.h

cs-media-player-proxy.h : Makefile.am org.mpris.MediaPlayer2.Player.xml
	gdbus-codegen                                       \
        --annotate "org.mpris.MediaPlayer2.Player" org.gtk.GDBus.C.Name "MediaPlayer" \
        --c-namespace Cs                      \
        --generate-c-code cs-media-player-proxy   \
        org.mpris.MediaPlayer2.Player.xml                           \
        $(NULL)
cs-media-player-proxy.c : cs-media-player-proxy.h

libcscreensaver_la_CPPFLAGS =            \
    $(WARN_CFLAGS)          \
    $(CSCREENSAVER_CFLAGS)           \
    -I$(srcdir)         \
    -DWITH_INTROSPECTION        \
    -DG_LOG_DOMAIN="\"CScreensaver\""

libcscreensaver_la_gir_sources =             \
    cs-gdk-event-filter.c \
    cs-gdk-event-filter.h \
    cs-notification-watcher.c \
    cs-notification-watcher.h \
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
CScreensaver_1_0_gir_SCANNERFLAGS = --identifier-prefix=Cs --symbol-prefix=cs_
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
    org.Cinnamon.xml \
    org.gnome.SessionManager.Presence.xml \
    org.freedesktop.UPower.xml \
    org.freedesktop.UPower.Device.xml \
    org.freedesktop.login1.Manager.xml \
    org.freedesktop.login1.Session.xml \
    org.freedesktop.ConsoleKit.Manager.xml \
    org.freedesktop.ConsoleKit.Session.xml \
    org.cinnamon.ScreenSaver.xml \
    org.cinnamon.SettingsDaemon.KeybindingHandler.xml \
    org.mpris.MediaPlayer2.Player.xml