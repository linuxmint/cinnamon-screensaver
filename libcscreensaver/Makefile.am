lib_LTLIBRARIES = libcscreensaver.la

libcscreensaver_la_CPPFLAGS =            \
    $(WARN_CFLAGS)          \
    $(CSCREENSAVER_CFLAGS)           \
    -I$(srcdir)         \
    -DWITH_INTROSPECTION        \
    -DG_LOG_DOMAIN="\"CScreensaver\""

libcscreensaver_la_gir_sources =             \
    cscreensaver-gdk-event-filter.c \
    cscreensaver-gdk-event-filter.h \
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

CLEANFILES = $(gir_DATA) $(typelib_DATA)

MAINTAINERCLEANFILES =          \
    Makefile.in

EXTRA_DIST = \
    cscreensaver.pc.in          \
    cscreensaver-uninstalled.pc.in

