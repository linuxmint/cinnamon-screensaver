NULL =

SPEC_XML_FILES =			\
	cinnamon-screensaver.xml		\
	dbus-interface.xml		\
	$(NULL)

if DOCBOOK_DOCS_ENABLED

htmldocdir = $(DOCDIR)/spec
htmldoc_DATA = cinnamon-screensaver.html

cinnamon-screensaver.html : dbus-interface.xml
	$(XMLTO) html-nochunks -m config.xsl cinnamon-screensaver.xml

endif # DOCBOOK_DOCS_ENABLED

EXTRA_DIST =				\
	cinnamon-screensaver.xml.in	\
	config.xsl			\
	docbook.css			\
	$(SPEC_XML_FILES)
	$(NULL)

clean-local:
	rm -f *~
	rm -f cinnamon-screensaver.html

-include $(top_srcdir)/git.mk
