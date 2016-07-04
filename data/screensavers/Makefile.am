screensaversdir = $(DESTDIR)$(pkgdatadir)/screensavers

xscreensaver = xscreensaver@cinnamon.org
webkit = webkit@cinnamon.org

install-data-local:
	mkdir -p $(screensaversdir)
	cp -R $(xscreensaver) $(screensaversdir)
if HAS_WEBKIT
	cp -R $(webkit) $(screensaversdir)
endif

uninstall-local:
	rm -rf $(screensaversdir)

