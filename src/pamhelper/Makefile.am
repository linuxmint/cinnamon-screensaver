## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

NULL =

SUBDIRS =

pamhelperdir = $(datadir)/cinnamon-screensaver/pamhelper

pamhelper_PYTHON = \
    authClient.py \
    $(NULL)

libexec_PROGRAMS = \
    cinnamon-screensaver-pam-helper \
    $(NULL)

cinnamon_screensaver_pam_helper_SOURCES = \
    cinnamon-screensaver-pam-helper.c \
    $(NULL)

cinnamon_screensaver_pam_helper_LDADD = \
    $(SCREENSAVER_PAM_LIBS)    \
    $(top_builddir)/libcscreensaver/libcscreensaver.la  \
    $(NULL)

cinnamon_screensaver_pam_helper_CPPFLAGS = \
    $(WARN_CFLAGS)          \
    $(SCREENSAVER_PAM_CFLAGS)           \
    -I$(top_builddir)/libcscreensaver \
    $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
