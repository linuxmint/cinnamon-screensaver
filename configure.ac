dnl -*- mode: m4 -*-

AC_PREREQ(2.60)
AC_INIT([cinnamon-screensaver],
        [3.1.0],
        [https://github.com/linuxmint/cinnamon-screensaver/issues])

PKG_PROG_PKG_CONFIG([0.26])

AC_CONFIG_SRCDIR(src/cinnamon-screensaver-main.py)

AM_INIT_AUTOMAKE([1.7 no-dist-gzip dist-xz])
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

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

AM_PATH_PYTHON(3.4)

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
po/Makefile.in
src/Makefile
src/cinnamon-screensaver.desktop.in
data/Makefile
src/screensavers/Makefile
data/org.cinnamon.ScreenSaver.service
data/org.cinnamon.ScreenSaver.PAMHelper.service
files/Makefile
])

