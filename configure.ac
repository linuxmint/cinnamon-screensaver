dnl -*- mode: m4 -*-

AC_PREREQ(2.60)
AC_INIT([cinnamon-screensaver],
        [4.4.0],
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

AC_CHECK_HEADERS(unistd.h)
AC_CHECK_HEADERS(crypt.h sys/select.h)
AC_CHECK_FUNCS(select fcntl uname nice setpriority getcwd getwd putenv sbrk)
AC_CHECK_FUNCS(sigaction syslog realpath setrlimit)
AC_TYPE_UID_T

AC_CHECK_FUNCS([setenv unsetenv clearenv])

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

# Like AC_TRY_COMPILE, but it uses the already-computed -I directories.
#
AC_DEFUN([AC_TRY_X_COMPILE], [
  ac_save_CPPFLAGS="$CPPFLAGS"
  if test \! -z "$includedir" ; then
    CPPFLAGS="$CPPFLAGS -I$includedir"
  fi
  CPPFLAGS="$CPPFLAGS $X_CFLAGS"
  AC_TRY_COMPILE([$1], [$2], [$3], [$4])
  CPPFLAGS="$ac_save_CPPFLAGS"])

ALL_X_LIBS="$X_LIBS $X_PRE_LIBS -lX11 $X_EXTRA_LIBS"

# Check for Xinerama extension (Solaris impl or Xfree impl)
cs_save_cppflags="$CPPFLAGS"
CPPFLAGS="$CPPFLAGS $X_CFLAGS"

AC_ARG_ENABLE(xinerama,
  AC_HELP_STRING([--disable-xinerama],
                 [disable use of the Xinerama extension]),
  try_xinerama=$enable_xinerama,try_xinerama=yes)
dnl '

use_solaris_xinerama=no
use_xfree_xinerama=no
if test "${try_xinerama}" != no; then
    case "$host" in
        *-*-solaris*)
            # Check for solaris
            use_solaris_xinerama=yes
            AC_CHECK_LIB(Xext, XineramaGetInfo,
                         use_solaris_xinerama=yes, use_solaris_xinerama=no,
                         $ALL_X_LIBS)
            if test "x$use_solaris_xinerama" = "xyes"; then
                AC_CHECK_HEADER(X11/extensions/xinerama.h,
                                if test -z "`echo $ALL_X_LIBS | grep "\-lXext" 2> /dev/null`"; then
                                    X_EXTRA_LIBS="-lXext $X_EXTRA_LIBS"
                                fi
                                AC_DEFINE(HAVE_SOLARIS_XINERAMA, , [Have Solaris-style Xinerama])
                                AC_DEFINE(HAVE_XINERAMA, , [Have some version of Xinerama]),
                                use_solaris_xinerama=no,
                                [#include <X11/Xlib.h>])
            fi
            AC_MSG_CHECKING(for Xinerama support on Solaris)
            AC_MSG_RESULT($use_solaris_xinerama);
            ;;
        *)
            # Check for XFree
            use_xfree_xinerama=yes
            AC_CHECK_LIB(Xinerama, XineramaQueryExtension,
                [AC_CHECK_HEADER(X11/extensions/Xinerama.h,
                                 X_EXTRA_LIBS="-lXinerama $X_EXTRA_LIBS"
                                 if test -z "`echo $ALL_X_LIBS | grep "\-lXext" 2> /dev/null`"; then
                                     X_EXTRA_LIBS="-lXext $X_EXTRA_LIBS"
                                 fi
                                 AC_DEFINE(HAVE_XFREE_XINERAMA, , [Have XFree86-style Xinerama])
                                 AC_DEFINE(HAVE_XINERAMA,, [Have some version of Xinerama]),
                                 use_xfree_xinerama=no,
                                 [#include <X11/Xlib.h>])],
                use_xfree_xinerama=no, -lXext $ALL_X_LIBS)
            AC_MSG_CHECKING(for Xinerama support on XFree86)
            AC_MSG_RESULT($use_xfree_xinerama);
            ;;
    esac
fi

CPPFLAGS="$cs_save_cppflags"

RANDR_LIBS=
found_randr=no
AC_CHECK_LIB(Xrandr, XRRUpdateConfiguration,
               [AC_CHECK_HEADER(X11/extensions/Xrandr.h,
                                RANDR_LIBS=-lXrandr found_randr=yes,,
                [#include <X11/Xlib.h>])],
               , -lXrender -lXext $ALL_X_LIBS)

if test "x$found_randr" = "xyes"; then
   AC_DEFINE(HAVE_RANDR, , [Have the Xrandr extension library])
fi

AM_PATH_PYTHON(3.4)

PKG_CHECK_MODULES(SCREENSAVER_PAM, gtk+-3.0 glib-2.0)
AC_SUBST(SCREENSAVER_PAM_CFLAGS)
AC_SUBST(SCREENSAVER_PAM_LIBS)

PKG_CHECK_MODULES(CSCREENSAVER, gobject-2.0 gtk+-3.0 gdk-x11-3.0 x11 xext glib-2.0 gio-2.0 gthread-2.0)

AC_SUBST(CSCREENSAVER_CFLAGS)
AC_SUBST(CSCREENSAVER_LIBS)

CSCREENSAVER_LIBS="$CSCREENSAVER_LIBS $RANDR_LIBS $X_PRE_LIBS $X_EXTRA_LIBS -lm"

dnl ---------------------------------------------------------------------------
dnl - The --enable-setres option
dnl ---------------------------------------------------------------------------

AC_ARG_ENABLE(setres,[
setres option:

  --enable-setres   Use setresuid/setresgid in the setuid.c helper
  --disable-setres   Don't use setresuid/setresgid (this is the default behavior)],
  [enable_setres="$enableval"],[enable_setres=no])
if test "$enable_setres" = yes; then
  echo "****************************************"
  AC_CHECK_FUNC(setresuid, [have_setresuid=yes], [have_setresuid=no])
  AC_CHECK_FUNC(setresgid, [have_setresgid=yes], [have_setresgid=no])
  if test "x$have_setresuid" = "xyes" -a "x$have_setresgid" = "xyes"; then
    AC_DEFINE(USE_SETRES, 1, [Define to have the setuid helper use setresuid/setresgid instead of setuid/setgid.])
  else
    AC_MSG_ERROR("setres requested but not available so we are ignoring the option")
  fi
elif test "$enable_setres" = no; then
  true
fi

dnl ---------------------------------------------------------------------------
dnl - Check for PAM
dnl ---------------------------------------------------------------------------

withval=""
AC_ARG_WITH(pam-prefix,
            AS_HELP_STRING([--with-pam-prefix=<prefix>],
                           [specify where pam files go]),
            [if test x$withval != x; then
               AC_MSG_RESULT("PAM files will be installed in prefix ${withval}.")
             fi])

if test x$withval != x; then
    PAM_PREFIX="$withval"
else
    PAM_PREFIX='${sysconfdir}'
fi
AC_SUBST(PAM_PREFIX)

have_pam=no
AC_CHECK_LIB(pam, pam_start, have_pam=yes)

if test "x$have_pam" = "xyes"; then
        AUTH_LIBS="${AUTH_LIBS} -lpam"
        AUTH_SCHEME=pam
        # On Linux, sigtimedwait() is in libc; on Solaris, it's in librt.
        have_timedwait=no
        AC_CHECK_LIB(c, sigtimedwait, [have_timedwait=yes])
        if test "$have_timedwait" = no ; then
                AC_CHECK_LIB(rt, sigtimedwait, [AUTH_LIBS="${AUTH_LIBS} -lrt"])
        fi

        AC_MSG_CHECKING(how to call pam_strerror)
        AC_CACHE_VAL(ac_cv_pam_strerror_args,
         [AC_TRY_COMPILE([#include <stdio.h>
                          #include <stdlib.h>
                          #include <security/pam_appl.h>],
                         [pam_handle_t *pamh = 0;
                          char *s = pam_strerror(pamh, PAM_SUCCESS);],
                         [ac_pam_strerror_args=2],
                         [AC_TRY_COMPILE([#include <stdio.h>
                                          #include <stdlib.h>
                                          #include <security/pam_appl.h>],
                                         [char *s =
                                           pam_strerror(PAM_SUCCESS);],
                                         [ac_pam_strerror_args=1],
                                         [ac_pam_strerror_args=0])])
          ac_cv_pam_strerror_args=$ac_pam_strerror_args])
        ac_pam_strerror_args=$ac_cv_pam_strerror_args
        if test "$ac_pam_strerror_args" = 1 ; then
          AC_MSG_RESULT(one argument)
        elif test "$ac_pam_strerror_args" = 2 ; then
          AC_DEFINE(PAM_STRERROR_TWO_ARGS, 1, [Define if pam_strerror takes two arguments])
          AC_MSG_RESULT(two arguments)
        else
          AC_MSG_RESULT(unknown)
        fi

else
    AC_MSG_ERROR("PAM libraries not found")
fi
AC_SUBST(HAVE_PAM)
AC_SUBST(AUTH_LIBS)
AC_SUBST(AUTH_SCHEME)

if test "x$have_pam" = "xyes"; then
  AC_CHECK_HEADERS([security/pam_modutil.h security/pam_ext.h])
  AC_CHECK_LIB(pam, pam_syslog, [AC_DEFINE(HAVE_PAM_SYSLOG, [], [Define to 1 if you have the pam_syslog function])])
fi

dnl test whether struct pam_message is const (Linux) or not (Sun)
if test "x$have_pam" = "xyes"; then
   pam_appl_h="$ac_pam_includes/security/pam_appl.h"
   AC_MSG_CHECKING(for const pam_message)
   AC_EGREP_HEADER([struct pam_message],
      $pam_appl_h,
      [ AC_EGREP_HEADER([const struct pam_message],
                        $pam_appl_h,
                        [AC_MSG_RESULT(["const: Linux-type PAM"]) ],
                        [AC_MSG_RESULT(["nonconst: Sun-type PAM"])
                        AC_DEFINE(PAM_MESSAGE_NONCONST, 1, [Define if your PAM support takes non-const arguments (Solaris)])]
                        )],
       [AC_MSG_RESULT(["not found - assume const, Linux-type PAM"])]
       )
fi

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

AC_SUBST(AUTH_LIBS)
AC_SUBST(CSCREENSAVER_LIBS)

# Files

AC_OUTPUT([
Makefile
data/Makefile
data/org.cinnamon.ScreenSaver.service
data/cinnamon-screensaver.desktop
data/icons/Makefile
files/Makefile
libcscreensaver/Makefile
libcscreensaver/cscreensaver.pc
libcscreensaver/cscreensaver-uninstalled.pc
po/Makefile.in
src/Makefile
src/binfiles/Makefile
src/dbusdepot/Makefile
src/widgets/Makefile
src/util/Makefile
src/pamhelper/Makefile
])
