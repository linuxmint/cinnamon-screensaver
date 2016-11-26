# This file will be processed with automake-1.7 to create Makefile.in

srcdir = @srcdir@
top_srcdir = @top_srcdir@
top_builddir = @top_builddir@

AUTOMAKE_OPTIONS = 1.7

DISTCHECK_CONFIGURE_FLAGS = --enable-introspection

NULL =

SUBDIRS =			\
    libcscreensaver \
	src			\
	po 			\
	data			\
    files       \
    screensavers \
	$(NULL)

EXTRA_DIST =			\
	COPYING			\
	COPYING.LIB		\
	AUTHORS			\
	INSTALL			\
	README			\
	ChangeLog		\
	NEWS			\
	HACKING			\
	intltool-extract.in     \
	intltool-merge.in       \
	intltool-update.in	\
	$(NULL)

DISTCLEANFILES =		\
	intltool-extract	\
	intltool-merge		\
	intltool-update		\
	./po/.intltool-merge-cache	\
	$(NULL)

MAINTAINERCLEANFILES =		\
	*~			\
	intltool-*.in		\
	compile			\
	configure		\
	INSTALL			\
	install-sh		\
	missing			\
	mkinstalldirs		\
	config.guess		\
	ltmain.sh		\
	config.sub		\
	depcomp			\
	Makefile.in		\
	config.h.*		\
	aclocal.m4		\
	acinclude.m4		\
	$(NULL)


-include $(top_srcdir)/git.mk
