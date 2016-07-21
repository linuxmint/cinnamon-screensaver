#! /usr/bin/python3

from gi.repository import Gio

SCREENSAVER_NAME_KEY = "screensaver-name"


bg_settings = Gio.Settings(schema_id="org.cinnamon.desktop.background")
ss_settings = Gio.Settings(schema_id="org.cinnamon.desktop.screensaver")

def get_screensaver_name():
    name = ss_settings.get_string(SCREENSAVER_NAME_KEY)

    if name and name != "":
        return name

    return None



