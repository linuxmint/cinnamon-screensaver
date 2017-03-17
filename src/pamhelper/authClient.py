#!/usr/bin/python3

from gi.repository import Gio, GObject, GLib, CScreensaver

import re
import os
import signal
import platform
import status
import sys

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
        'auth-prompt': (GObject.SignalFlags.RUN_LAST, None, (str,))
    }

    def __init__(self):
        super(AuthClient, self).__init__()
        self.initialized = False

        self.proc = None
        self.out_pipe = None
        self.in_pipe = None

    def initialize(self):
        if status.Debug:
            print("authClient initialize... initialized already: %s" % str(self.initialized))

        if self.initialized:
            return True

        try:
            helper_path = None
            architecture = platform.machine()
            paths = ["/usr/lib", "/usr/lib/cinnamon-screensaver", "/usr/libexec", "/usr/libexec/cinnamon-screensaver"]

            # On x86 archs, iterate through multiple paths
            # For instance, on a Mint i686 box, the path is actually /usr/lib/i386-linux-gnu
            x86archs = ["i386", "i486", "i586", "i686"]
            if architecture in x86archs:
                for arch in x86archs:
                    paths += ["/usr/lib/%s" % arch, "/usr/lib/%s-linux-gnu" % arch]
            elif architecture == "x86_64":
                paths += ["/usr/lib/x86_64", "/usr/lib/x86_64-linux-gnu", "/usr/lib64"]
            else:
                paths += ["/usr/lib/%s" % architecture, "/usr/lib/%s-linux-gnu" % architecture]

            for path in paths:
                full_path = os.path.join(path, "cinnamon-screensaver-pam-helper")
                if os.path.exists(full_path):
                    helper_path = full_path
                    break

            if helper_path is None:
                print ("Critical Error: PAM Helper could not be found!")

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
            print("error starting cinnamon-screensaver-pam-helper: %s" % e.message)
            return False

        self.proc.wait_check_async(None, self.on_proc_completed, None)

        self.out_pipe = self.proc.get_stdout_pipe()
        self.out_pipe.read_bytes_async(1024, GLib.PRIORITY_DEFAULT, None, self.message_from_child)

        self.in_pipe = self.proc.get_stdin_pipe()

        self.initialized = True

        return True

    def cancel(self):
        if self.proc != None:
            self.message_to_child("CS_PAM_AUTH_REQUEST_SUBPROCESS_EXIT\n");
        else:
            if status.Debug:
                print("authClient cancel requested, but no helper process")

    def on_proc_completed(self, proc, res, data=None):
        if status.Debug:
            print("authClient helper process completed...")
        try:
            ret = proc.wait_check_finish(res)
        except GLib.Error as e:
            if status.Debug:
                print("helper process did not exit cleanly: %s" % e.message)

        if self.in_pipe != None:
            self.in_pipe.clear_pending()
            try:
                self.in_pipe.close(None)
            except GLib.Error as e:
                if status.Debug:
                    print("helper process did not close in_pipe cleanly: %s" % e.message)
            self.in_pipe = None

        if self.out_pipe != None:
            self.out_pipe.clear_pending()
            try:
                self.out_pipe.close(None)
            except GLib.Error as e:
                if status.Debug:
                    print("helper process did not close out_pipe cleanly: %s" % e.message)
            self.out_pipe = None

        self.initialized = False
        self.proc = None

    def message_to_child(self, string):
        if not self.initialized:
            return

        if status.Debug:
            print("authClient message to child")

        try:
            b = GLib.Bytes.new(string.encode())
            s = self.in_pipe.write_bytes(b)

            self.in_pipe.flush(None)
        except GLib.Error as e:
            print("Error writing to child - %s" % e.message)

    def message_from_child(self, pipe, res):
        if pipe.is_closed():
            return

        finished = False
        bytes_read = pipe.read_bytes_finish(res)

        if bytes_read:
            raw_string = bytes_read.get_data().decode()
            lines = raw_string.split("\n")
            for output in lines:
                if status.Debug:
                    print("Output from pam helper: '%s'" % output)
                if output:
                    if "CS_PAM_AUTH_FAILURE" in output:
                        self.emit_idle_failure()
                    if "CS_PAM_AUTH_SUCCESS" in output:
                        self.emit_idle_success()
                        finished = True
                    if "CS_PAM_AUTH_CANCELLED" in output:
                        self.emit_idle_cancel()
                        finished = True
                    if "CS_PAM_AUTH_BUSY_TRUE" in output:
                        self.emit_idle_busy_state(True)
                    if "CS_PAM_AUTH_BUSY_FALSE" in output:
                        self.emit_idle_busy_state(False)
                    if "CS_PAM_AUTH_SET_PROMPT" in output:
                        prompt = re.search('(?<=CS_PAM_AUTH_SET_PROMPT_)(.*)(?=_)', output).group(0)
                        self.emit_idle_auth_prompt(prompt)
        if not finished:
            pipe.read_bytes_async(1024, GLib.PRIORITY_DEFAULT, None, self.message_from_child)

    def emit_idle_busy_state(self, busy):
        if status.Debug:
            print("authClient idle add auth-busy")
        GObject.idle_add(self.emit, "auth-busy", busy)

    def emit_idle_failure(self):
        if status.Debug:
            print("authClient idle add failure")
        GObject.idle_add(self.emit, "auth-failure")

    def emit_idle_success(self):
        if status.Debug:
            print("authClient idle add success")
        GObject.idle_add(self.emit, "auth-success")

    def emit_idle_cancel(self):
        if status.Debug:
            print("authClient idle add cancel")
        GObject.idle_add(self.emit, "auth-cancel")

    def emit_idle_auth_prompt(self, prompt):
        if status.Debug:
            print("authClient idle add auth-prompt")
        GObject.idle_add(self.emit, "auth-prompt", prompt)
