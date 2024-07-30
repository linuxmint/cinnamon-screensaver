#!/usr/bin/python3

import re
import os
import signal
import platform
import sys

from gi.repository import Gio, GObject, GLib, CScreensaver

import config
import status
from util.utils import DEBUG

class AuthClient(GObject.Object):
    """
    The AuthClient manages spawning of our pam helper process, and
    communication with it.
    """
    __gsignals__ = {
        'auth-success': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-failure': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-cancel': (GObject.SignalFlags.RUN_LAST, None, ()),
        'auth-busy': (GObject.SignalFlags.RUN_LAST, None, (bool,)),
        'auth-prompt': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        'auth-info': (GObject.SignalFlags.RUN_LAST, None, (str,))
    }

    def __init__(self):
        super(AuthClient, self).__init__()
        self.reset()

    def initialize(self):
        if self.initialized:
            return True

        DEBUG("authClient: attempting to initialize")

        self.cancellable = Gio.Cancellable()

        try:
            helper_path = None

            full_path = os.path.join(config.pkglibdir, "cinnamon-screensaver-pam-helper")
            if os.path.exists(full_path):
                helper_path = full_path

            if helper_path is None:
                print ("authClient: critical Error: PAM Helper could not be found!")

            if status.Debug:
                argv = (helper_path, "--debug", None)
                self.proc = Gio.Subprocess.new(argv,
                                               Gio.SubprocessFlags.STDIN_PIPE  |
                                               Gio.SubprocessFlags.STDOUT_PIPE)
            else:
                argv = (helper_path, None)
                self.proc = Gio.Subprocess.new(argv,
                                               Gio.SubprocessFlags.STDIN_PIPE  |
                                               Gio.SubprocessFlags.STDOUT_PIPE |
                                               Gio.SubprocessFlags.STDERR_SILENCE)

        except GLib.Error as e:
            print("authClient: error starting cinnamon-screensaver-pam-helper: %s" % e.message)
            return False

        self.proc.wait_check_async(self.cancellable, self.on_proc_completed, None)

        self.out_pipe = self.proc.get_stdout_pipe()
        self.out_pipe.read_bytes_async(1024, GLib.PRIORITY_DEFAULT, self.cancellable, self.message_from_child)

        self.in_pipe = self.proc.get_stdin_pipe()

        self.initialized = True

        DEBUG("authClient: initialized (helper pid %s)" % self.proc.get_identifier ())

        return True

    def reset(self):
        self.initialized = False
        self.cancellable = None
        self.proc = None
        self.in_pipe = None
        self.out_pipe = None

    def cancel(self):
        self.end_proc()

    def end_proc(self):
        if self.cancellable is None:
            return

        self.cancellable.cancel()
        if self.proc is not None:
            DEBUG("authClient: cancel requested, killing helper.")
            self.proc.send_signal(signal.SIGTERM)
        else:
            DEBUG("authClient: cancel requested, but no helper process")

        self.reset()

    def on_proc_completed(self, proc, res, data=None):
        DEBUG("authClient: helper process (pid %s) completed..." % proc.get_identifier())

        try:
            ret = proc.wait_check_finish(res)
        except GLib.Error as e:
            if status.Debug and e.code != Gio.IOErrorEnum.CANCELLED:
                print("helper process did not exit cleanly: %s" % e.message)

        pipe = proc.get_stdin_pipe()

        if pipe is not None:
            pipe.clear_pending()
            try:
                pipe.close(None)
            except GLib.Error as e:
                DEBUG("helper process did not close in_pipe cleanly: %s" % e.message)

        pipe = proc.get_stdout_pipe()

        if pipe is not None:
            pipe.clear_pending()
            try:
                pipe.close(None)
            except GLib.Error as e:
                DEBUG("helper process did not close out_pipe cleanly: %s" % e.message)

        # Don't just reset - if another proc has been started we don't want to interfere.
        if self.proc == proc:
            self.reset()

    def message_to_child(self, string):
        if not self.initialized:
            return

        if self.cancellable is None or self.cancellable.is_cancelled():
            return

        DEBUG("authClient: message to child")

        try:
            b = GLib.Bytes.new(string.encode())

            try:
                s = self.in_pipe.write_bytes(b)
            except GLib.Error as e:
                if e.code != Gio.IOErrorEnum.CANCELLED:
                    print("Error reading message from pam helper")
                return

            self.in_pipe.flush(None)
        except GLib.Error as e:
            if e.code != Gib.IOErrorEnum.CANCELLED:
                print("Error writing to pam helper: %s" % e.message)

    def message_from_child(self, pipe, res):
        if self.cancellable is None or self.cancellable.is_cancelled():
            return

        terminate = False

        try:
            bytes_read = pipe.read_bytes_finish(res)
        except GLib.Error as e:
            if e.code != Gio.IOErrorEnum.CANCELLED:
                print("Error reading message from pam helper: %s" % e.message)
            return

        if bytes_read:
            raw_string = bytes_read.get_data().decode()
            lines = raw_string.split("\n")
            for output in lines:
                DEBUG("Output from pam helper: '%s'" % output)
                if output:
                    if "CS_PAM_AUTH_FAILURE" in output:
                        self.emit_idle_failure()
                    if "CS_PAM_AUTH_SUCCESS" in output:
                        self.emit_idle_success()
                        terminate = True
                    if "CS_PAM_AUTH_CANCELLED" in output:
                        self.emit_idle_cancel()
                        terminate = True
                    if "CS_PAM_AUTH_BUSY_TRUE" in output:
                        self.emit_idle_busy_state(True)
                    if "CS_PAM_AUTH_BUSY_FALSE" in output:
                        self.emit_idle_busy_state(False)
                    if "CS_PAM_AUTH_SET_PROMPT" in output:
                        prompt = re.search('(?<=CS_PAM_AUTH_SET_PROMPT_)(.*)(?=_)', output).group(0)
                        self.emit_idle_auth_prompt(prompt)
                    if "CS_PAM_AUTH_SET_INFO" in output:
                        info = re.search('(?<=CS_PAM_AUTH_SET_INFO_)(.*)(?=_)', output).group(0)
                        self.emit_auth_info(info)

        if terminate:
            self.end_proc()
            return

        pipe.read_bytes_async(1024, GLib.PRIORITY_DEFAULT, None, self.message_from_child)

    def emit_idle_busy_state(self, busy):
        DEBUG("authClient: idle add auth-busy")
        GObject.idle_add(self.emit, "auth-busy", busy)

    def emit_idle_failure(self):
        DEBUG("authClient: idle add failure")
        GObject.idle_add(self.emit, "auth-failure")

    def emit_idle_success(self):
        DEBUG("authClient: idle add success")
        GObject.idle_add(self.emit, "auth-success")

    def emit_idle_cancel(self):
        DEBUG("authClient: idle add cancel")
        GObject.idle_add(self.emit, "auth-cancel")

    def emit_idle_auth_prompt(self, prompt):
        DEBUG("authClient: idle add auth-prompt")
        GObject.idle_add(self.emit, "auth-prompt", prompt)

    def emit_auth_info(self, info):
        DEBUG("authClient: auth-info")
        GObject.idle_add(self.emit, "auth-info", info)
