#!/usr/bin/python

'''Apport package hook for gnome-screensaver

(c) 2010 Canonical Ltd.
Contributors:
Marc Deslauriers <marc.deslauriers@canonical.com>
Chris Coulson <chris.coulson@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

from apport.hookutils import *
import dbus

def add_info(report):

    attach_file_if_exists(report, '/etc/X11/xorg.conf', 'XorgConf')
    attach_file_if_exists(report, '/var/log/Xorg.0.log', 'XorgLog')
    attach_file_if_exists(report, '/var/log/Xorg.0.log.old', 'XorgLogOld')

    report['WindowManager'] = command_output(['gconftool-2','--get','/desktop/gnome/session/required_components/windowmanager'])

    # We want the whole thing, not just the changes
    report['GsettingsGnomeScreensaver'] = command_output(['gsettings', 'list-recursively', 'org.gnome.desktop.screensaver'])
    report['GsettingsGnomePowerManager'] = command_output(['gsettings', 'list-recursively', 'org.gnome.settings-daemon.plugins.power'])
    report['GsettingsGnomeSession'] = command_output(['gsettings', 'list-recursively', 'org.gnome.desktop.session'])
    report['GsettingsGnomeLockdown'] = command_output(['gsettings', 'list-recursively', 'org.gnome.desktop.lockdown'])

    try:
        bus = dbus.SessionBus()
        session_manager = bus.get_object('org.gnome.SessionManager', '/org/gnome/SessionManager')
        session_manager_iface = dbus.Interface(session_manager, dbus_interface='org.gnome.SessionManager')
        inhibitors = session_manager_iface.GetInhibitors()
        inhibitors_str = ''
        master_flag = 0
        j = 1
        for i in inhibitors:
            obj = bus.get_object('org.gnome.SessionManager', i)
            iface = dbus.Interface(obj, dbus_interface='org.gnome.SessionManager.Inhibitor')
            app_id = iface.GetAppId()
            flags = iface.GetFlags()
            reason = iface.GetReason()
	    if j > 1:
		    inhibitors_str += '\n'
            inhibitors_str += str(j) + ': AppId = ' + app_id + ', Flags = ' + str(flags) + ', Reason = ' + reason
            j = j + 1
            master_flag |= flags

        report['GnomeSessionInhibitors'] = 'None' if inhibitors_str == '' else inhibitors_str
        report['GnomeSessionIdleInhibited'] = 'Yes' if master_flag & 8 else 'No'
    except:
        report['GnomeSessionInhibitors'] = 'Failed to acquire'
        report['GnomeSessionIdleInhibited'] = 'Unknown'

if __name__ == '__main__':
    report = {}
    add_info(report)
    for key in report:
        print '[%s]\n%s' % (key, report[key])
