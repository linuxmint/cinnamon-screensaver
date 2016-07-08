#! /usr/bin/python3

import PAM

from gi.repository import Gio, GObject
import threading
import dbus
import constants as c

class PAMServiceProxy:
    def __init__(self):
        self.callback = None
        self.proxy = None

        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.PAM_SERVICE, c.PAM_PATH, c.PAM_SERVICE,
                                      None, self._onProxyReady, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None

    def _onProxyReady(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)

    def check_password(self, username, password, callback):
        self.callback = callback

        if self.proxy:
            thread = threading.Thread(target=self.check_password_thread, args=(username, password, callback))
            thread.start()
        else:
            success, msg = self.check_password_fallback(username, password)
            GObject.idle_add(self.idle_callback_and_clear, success, msg)

    def check_password_thread(self, username, password, callback):
        if self.proxy:
            try:
                success, msg = self.proxy.authenticate('(ss)', username, password)
            except Exception as e:
                print(str(e))
                success, msg = self.check_password_fallback(username, password)
        else:
            success, msg = self.check_password_fallback(username, password)

        GObject.idle_add(self.idle_callback_and_clear, success, msg)

    def check_password_fallback(self, username, password):
        print("PAM Helper service unavailable, using sync method")
        success, msg = real_check_password(username, password)

        return (success, msg)

    def idle_callback_and_clear(self, success, msg):
        self.callback(success, msg)
        self.callback = None

        return False

def real_check_password(username, password):
    ret = None

    pam_auth = PAM.pam()

    pam_auth.start("cinnamon-screensaver")
    pam_auth.set_item(PAM.PAM_USER, username)

    def _pam_conv(auth, query_list, user_data = None):
        resp = []
        for i in range(len(query_list)):
            query, qtype = query_list[i]
            if qtype == PAM.PAM_PROMPT_ECHO_ON:
                resp.append((username, 0))
            elif qtype == PAM.PAM_PROMPT_ECHO_OFF:
                resp.append((password, 0))
            else:
                return None
        return resp

    pam_auth.set_item(PAM.PAM_CONV, _pam_conv)
    
    try:
        pam_auth.authenticate()
        pam_auth.acct_mgmt()
    except PAM.error as res:
        ret = (False, res.args[0])
    except Exception as e:
        log.warn("Error with PAM: %s" % str(e))
        ret = (False, e)
    else:
        ret = (True, "")

    return ret


