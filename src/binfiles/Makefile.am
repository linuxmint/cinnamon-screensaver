## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

SUBDIRS=
NULL =

%:%.in Makefile
	$(AM_V_GEN)sed                  \
        -e s!\@datadir\@!$(datadir)!        \
        < $< > $@

all-local: cinnamon-screensaver-command

bin_SCRIPTS = cinnamon-screensaver-command

bin_PROGRAMS = cinnamon-screensaver

cinnamon_screensaver_SOURCES =  \
    cinnamon-screensaver.c \
    setuid.h \
    setuid.c \
    $(NULL)

cinnamon_screensaver_LDADD =    \
    $(SCREENSAVER_MAIN_LIBS)    \
    $(NULL)

cinnamon_screensaver_CPPFLAGS =            \
    $(WARN_CFLAGS)          \
    $(SCREENSAVER_MAIN_CFLAGS)           \
    -I$(srcdir)         \
    $(NULL)

EXTRA_DIST =                \
    cinnamon-screensaver.in \
    $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
