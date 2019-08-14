NULL =

public_icons_themes = \
    hicolor \
    $(NULL)

public_icons = \
    hicolor/scalable/actions/screensaver-unlock-symbolic.svg \
    hicolor/scalable/actions/screensaver-switch-users-symbolic.svg \
    hicolor/scalable/status/screensaver-notification-symbolic.svg \
    hicolor/scalable/status/screensaver-blank.svg \
    $(NULL)

EXTRA_DIST = \
    $(public_icons)     \
    $(NULL)


###############################################################################

gtk_update_icon_cache = gtk-update-icon-cache -f -t

update-icon-cache:
	@-if test -z "$(DESTDIR)"; then \
        echo "Updating Gtk icon cache."; \
        for theme in $(public_icons_themes); do \
            $(gtk_update_icon_cache) $(datadir)/icons/$$theme; \
        done; \
        else \
        echo "*** Icon cache not updated.  After (un)install, run this:"; \
        for theme in $(public_icons_themes); do \
            echo "***   $(gtk_update_icon_cache) $(datadir)/icons/$$theme"; \
        done; \
    fi

install-icons:
	for icon in $(public_icons); do \
        BASEDIR=$${icon%/*}; \
        ICONFILE=$${icon##*/}; \
        mkdir -p $(DESTDIR)$(datadir)/icons/$$BASEDIR; \
        $(INSTALL_DATA) $(srcdir)/$$icon $(DESTDIR)$(datadir)/icons/$$BASEDIR/$$ICONFILE; \
    done

uninstall-icons:
	-for icon in $(public_icons); do \
        BASEDIR=$${icon%/*}; \
        ICONFILE=$${icon##*/}; \
        rm -f $(DESTDIR)$(datadir)/icons/$$BASEDIR/$$ICONFILE; \
    done

install-data-local: install-icons update-icon-cache

uninstall-local: uninstall-icons update-icon-cache
