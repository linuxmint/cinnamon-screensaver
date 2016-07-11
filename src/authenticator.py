#! /usr/bin/python3

import PAM

from gi.repository import Gio, GObject, GLib
import threading
import dbus
import constants as c

class PAMServiceProxy:
    def __init__(self):
        self.proxy = None

        try:
            Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                      c.PAM_SERVICE, c.PAM_PATH, c.PAM_SERVICE,
                                      None, self.on_proxy_ready, None)
        except dbus.exceptions.DBusException as e:
            print(e)
            self.proxy = None

    def on_proxy_ready(self, object, result, data=None):
        self.proxy = Gio.DBusProxy.new_for_bus_finish(result)

    def check_password(self, username, password, client_callback):
        if self.proxy:
            try:
                # FIXME: There is a way to call self.proxy.authenticate() with callbacks
                #        I couldn't get it to work though
                self.proxy.call("authenticate",
                                GLib.Variant("(ss)", (username, password)),
                                Gio.DBusCallFlags.NONE, -1, None,
                                self.async_callback_handler, client_callback)
            except Exception as e:
                print("PAM Helper method failed, go to fallback")
                self.do_fallback_password_check(username, password, client_callback)
        else:
            self.do_fallback_password_check(username, password, client_callback)

    def async_callback_handler(self, proxy, res, client_callback):
        ret = proxy.call_finish(res)

        success, msg = ret

        client_callback(success, msg)

    def do_fallback_password_check(self, username, password, callback):
            success, msg = self.check_password_fallback(username, password)

            callback(success, msg)

    def check_password_fallback(self, username, password):
        print("PAM Helper service unavailable, using sync method")
        success, msg = real_check_password(username, password)

        return (success, msg)

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


