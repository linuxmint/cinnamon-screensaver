#! /usr/bin/python3

import gi
gi.require_version('CinnamonDesktop', '3.0')
from gi.repository import Gio, CinnamonDesktop

bg_settings = Gio.Settings(schema_id="org.cinnamon.desktop.background")

bg = CinnamonDesktop.BG()
bg.load_from_preferences(bg_settings)
bg_settings.connect("changed", lambda s,k: bg.load_from_preferences(bg_settings))

####
ss_settings = Gio.Settings(schema_id="org.cinnamon.desktop.screensaver")
DEFAULT_MESSAGE_KEY = "default-message"
SCREENSAVER_NAME_KEY = "screensaver-name"
USER_SWITCH_ENABLED_KEY = "user-switch-enabled"
LOGOUT_ENABLED_KEY = "logout-enabled"
LOGOUT_DELAY_KEY = "logout-delay"
LOGOUT_COMMAND_KEY = "logout-command"
IDLE_ACTIVATE_KEY = "idle-activation-enabled"
LOCK_ENABLED_KEY = "lock-enabled"
LOCK_DELAY_KEY = "lock-delay"
USE_CUSTOM_FORMAT_KEY = "use-custom-format"
DATE_FORMAT_KEY = "date-format"
TIME_FORMAT_KEY = "time-format"
FONT_DATE_KEY = "font-date"
FONT_MESSAGE_KEY = "font-message"
FONT_TIME_KEY = "font-time"
####
if_settings = Gio.Settings(schema_id="org.cinnamon.desktop.interface")
CLOCK_SHOW_DATE_KEY = "clock-show-date"
CLOCK_USE_24H_KEY = "clock-use-24h"

def check_string(string):
    if string and string != "":
        return string

    return ""

def get_default_away_message():
    msg = ss_settings.get_string(DEFAULT_MESSAGE_KEY)

    return check_string(msg)

def get_screensaver_name():
    name = ss_settings.get_string(SCREENSAVER_NAME_KEY)

    return check_string(name)

def get_user_switch_enabled():
    return ss_settings.get_boolean(USER_SWITCH_ENABLED_KEY)

def get_logout_enabled():
    return ss_settings.get_boolean(LOGOUT_ENABLED_KEY)

def get_logout_delay():
    return ss_settings.get_uint(LOGOUT_DELAY_KEY)

def get_logout_command():
    cmd = ss_settings.get_string(LOGOUT_COMMAND_KEY)

    return check_string(cmd)

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

    return check_string(date_format)

def get_custom_time_format():
    time_format = ss_settings.get_string(TIME_FORMAT_KEY)

    return check_string(time_format)

def get_date_font():
    date_font = ss_settings.get_string(FONT_DATE_KEY)

    return check_string(date_font)

def get_message_font():
    message_font = ss_settings.get_string(FONT_MESSAGE_KEY)

    return check_string(message_font)

def get_time_font():
    time_font = ss_settings.get_string(FONT_TIME_KEY)

    return check_string(time_font)

def get_clock_should_show_date():
    return if_settings.get_boolean(CLOCK_SHOW_DATE_KEY)

def get_clock_should_use_24h():
    return if_settings.get_boolean(CLOCK_USE_24H_KEY)
