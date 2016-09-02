#! /usr/bin/python3

from gi.repository import Gio

# Background settings, the only one interested in this is Backgrounds in
# singletons.py, and then only for the "changed" signal - it reloads
# any individual gsettings internally.

bg_settings = Gio.Settings(schema_id="org.cinnamon.desktop.background")

# Screensaver settings - we have no need to listen to changes here,
# They're read anew each time they're used, and while the screensaver
# is active, the user won't be changing them.

ss_settings = Gio.Settings(schema_id="org.cinnamon.desktop.screensaver")
DEFAULT_MESSAGE_KEY = "default-message"
SCREENSAVER_NAME_KEY = "screensaver-name"
USER_SWITCH_ENABLED_KEY = "user-switch-enabled"
IDLE_ACTIVATE_KEY = "idle-activation-enabled"
LOCK_ENABLED_KEY = "lock-enabled"
LOCK_DELAY_KEY = "lock-delay"
USE_CUSTOM_FORMAT_KEY = "use-custom-format"
DATE_FORMAT_KEY = "date-format"
TIME_FORMAT_KEY = "time-format"
FONT_DATE_KEY = "font-date"
FONT_MESSAGE_KEY = "font-message"
FONT_TIME_KEY = "font-time"
SHOW_FLAGS_KEY = "show-flags"
KB_LAYOUT_KEY = "layout-group"
SHOW_CLOCK_KEY = "show-clock"

# Interface settings - the same logic applies here as above - we don't
# need to listen to changes to these.
if_settings = Gio.Settings(schema_id="org.cinnamon.desktop.interface")
CLOCK_SHOW_DATE_KEY = "clock-show-date"
CLOCK_USE_24H_KEY = "clock-use-24h"

# Every setting has a getter (and setter, rarely).  This is mainly for
# organizational purposes and cleanliness - it's easier to read in the
# main code if you see "settings.get_default_away_message()" than seeing
# "settings.ss_settings.get_string(settings.DEFAULT_MESSAGE_KEY)" or keeping
# instances of GioSettings wherever we need them.

def _check_string(string):
    if string and string != "":
        return string

    return ""

def get_default_away_message():
    msg = ss_settings.get_string(DEFAULT_MESSAGE_KEY)

    return _check_string(msg)

def should_show_plugin():
    return get_screensaver_name() != ""

def get_screensaver_name():
    name = ss_settings.get_string(SCREENSAVER_NAME_KEY)

    return _check_string(name)

def get_user_switch_enabled():
    return ss_settings.get_boolean(USER_SWITCH_ENABLED_KEY)

def get_idle_activate():
    return ss_settings.get_boolean(IDLE_ACTIVATE_KEY)

def get_idle_lock_enabled():
    return ss_settings.get_boolean(LOCK_ENABLED_KEY)

def get_idle_lock_delay():
    return ss_settings.get_uint(LOCK_DELAY_KEY)

def get_use_custom_format():
    return ss_settings.get_boolean(USE_CUSTOM_FORMAT_KEY)

def get_custom_date_format():
    date_format = ss_settings.get_string(DATE_FORMAT_KEY)

    return _check_string(date_format)

def get_custom_time_format():
    time_format = ss_settings.get_string(TIME_FORMAT_KEY)

    return _check_string(time_format)

def get_date_font():
    date_font = ss_settings.get_string(FONT_DATE_KEY)

    return _check_string(date_font)

def get_message_font():
    message_font = ss_settings.get_string(FONT_MESSAGE_KEY)

    return _check_string(message_font)

def get_time_font():
    time_font = ss_settings.get_string(FONT_TIME_KEY)

    return _check_string(time_font)

def get_clock_should_show_date():
    return if_settings.get_boolean(CLOCK_SHOW_DATE_KEY)

def get_clock_should_use_24h():
    return if_settings.get_boolean(CLOCK_USE_24H_KEY)

def get_show_flags():
    return ss_settings.get_boolean(SHOW_FLAGS_KEY)

def get_kb_group():
    return ss_settings.get_int(KB_LAYOUT_KEY)

def set_kb_group(group):
    return ss_settings.set_int(KB_LAYOUT_KEY, group)

def get_show_clock():
    return ss_settings.get_boolean(SHOW_CLOCK_KEY)
