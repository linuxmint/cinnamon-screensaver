## We require new-style dependency handling.
AUTOMAKE_OPTIONS = 1.7

SUBDIRS=
NULL =

%:%.in Makefile
	$(AM_V_GEN)sed                  \
        -e s!\@datadir\@!$(datadir)!        \
        < $< > $@

all-local: cinnamon-screensaver cinnamon-screensaver-command

bin_SCRIPTS = cinnamon-screensaver cinnamon-screensaver-command

EXTRA_DIST =                \
    cinnamon-screensaver.in \
    cinnamon-screensaver-command.in \
    $(NULL)

MAINTAINERCLEANFILES =          \
    *~              \
    Makefile.in

-include $(top_srcdir)/git.mk
