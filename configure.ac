dnl -*- mode: m4 -*-

AC_PREREQ(2.60)
AC_INIT([cinnamon-screensaver],
        [3.2.6],
        [https://github.com/linuxmint/cinnamon-screensaver/issues])

PKG_PROG_PKG_CONFIG([0.26])

AC_CONFIG_MACRO_DIR([m4])
AC_SUBST([ACLOCAL_AMFLAGS], ["-I $ac_macro_dir \${ACLOCAL_FLAGS}"])

m4_ifdef([AX_IS_RELEASE], [AX_IS_RELEASE([always])])

AC_CONFIG_SRCDIR(src/cinnamon-screensaver-main.py)

AM_INIT_AUTOMAKE([1.7 no-dist-gzip dist-xz])
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

m4_ifdef([AX_COMPILER_FLAGS],
         [AX_COMPILER_FLAGS([WARN_CFLAGS],[WARN_LDFLAGS])])

LT_INIT([disable-static])

AC_CONFIG_HEADERS(config.h)

AM_MAINTAINER_MODE([enable])

IT_PROG_INTLTOOL([0.40.0])

AC_CONFIG_MACRO_DIRS([m4])

dnl put the ACLOCAL flags in the makefile
ACLOCAL="$ACLOCAL $ACLOCAL_FLAGS"

GETTEXT_PACKAGE=cinnamon-screensaver
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT
GOBJECT_INTROSPECTION_CHECK([0.9.7])

AC_DEFUN([AC_CHECK_X_HEADER], [
  ac_save_CPPFLAGS="$CPPFLAGS"
  if test \! -z "$includedir" ; then 
    CPPFLAGS="$CPPFLAGS -I$includedir"
  fi
  CPPFLAGS="$CPPFLAGS $X_CFLAGS"
  AC_CHECK_HEADER([$1],[$2],[$3],[$4])
  CPPFLAGS="$ac_save_CPPFLAGS"])

AM_PATH_PYTHON(3.4)

PKG_CHECK_MODULES(SCREENSAVER_MAIN, glib-2.0)

PKG_CHECK_MODULES(CSCREENSAVER, gobject-2.0 gtk+-3.0 gdk-x11-3.0 x11 glib-2.0 gio-2.0)

have_shape=no
AC_CHECK_X_HEADER(X11/extensions/shape.h, [have_shape=yes],,
                    [#include <X11/Xlib.h>])
if test "$have_shape" = yes; then
  AC_DEFINE(HAVE_SHAPE_EXT, 1, [Define if shape extension is available])
fi

# Find out where the session service file goes
# The sad sed hack is recommended by section 27.10 of the automake manual.
DBUS_SESSION_SERVICE_DIR=`$PKG_CONFIG --variable session_bus_services_dir dbus-1 | sed -e 's,/usr/share,${datarootdir},g'`
AC_SUBST(DBUS_SESSION_SERVICE_DIR)

REAL_PREFIX=
if test "x$prefix" = "xNONE"; then
  REAL_PREFIX=$ac_default_prefix
else
  REAL_PREFIX=$prefix
fi

## temporarily change prefix and exec_prefix
old_prefix=$prefix
prefix=$REAL_PREFIX

if test "x$exec_prefix" = xNONE ; then
   REAL_EXEC_PREFIX=$REAL_PREFIX
else
   REAL_EXEC_PREFIX=$exec_prefix
fi
old_exec_prefix=$exec_prefix
exec_prefix=$REAL_EXEC_PREFIX

BINDIR_TMP="$bindir"
EXPANDED_BINDIR=`eval echo $BINDIR_TMP`
AC_SUBST(EXPANDED_BINDIR)

## put prefix and exec_prefix back
prefix=$old_prefix
exec_prefix=$old_exec_prefix

# Files

AC_OUTPUT([
Makefile
data/Makefile
data/org.cinnamon.ScreenSaver.service
data/cinnamon-screensaver.desktop.in
data/icons/Makefile
files/Makefile
libcscreensaver/Makefile
libcscreensaver/cscreensaver.pc
libcscreensaver/cscreensaver-uninstalled.pc
po/Makefile.in
screensavers/Makefile
screensavers/webkit@cinnamon.org/Makefile
screensavers/webkit@cinnamon.org/webkit-stars@cinnamon.org/Makefile
screensavers/xscreensaver@cinnamon.org/Makefile
src/Makefile
src/binfiles/Makefile
src/dbusdepot/Makefile
src/widgets/Makefile
src/util/Makefile
])
