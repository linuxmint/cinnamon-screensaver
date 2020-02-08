#!/usr/bin/env python3

'''
FIXME

This script is used only to call gdbus-codegen and simulate the
generation of the source code and header as different targets.

Both are generated implicitly, so meson is not able to know how
many files are generated, so it does generate only one opaque
target that represents the two files.

originally from:
https://gitlab.gnome.org/GNOME/gnome-settings-daemon/commit/5924d72931a030b24554116a48140a661a99652b

Please see:
   https://bugzilla.gnome.org/show_bug.cgi?id=791015
   https://github.com/mesonbuild/meson/pull/2930
   https://github.com/linuxmint/xapps/commit/539ed7377cff41643608cf61ed1a8430a367e283#diff-5800aaf205d98232d967a359f4657a06R4
'''

import subprocess
import sys
import os

subprocess.call([
  'gdbus-codegen',
  '--interface-prefix=' + sys.argv[1],
  '--generate-c-code=' + os.path.join(sys.argv[4], sys.argv[2]),
  '--c-namespace=Cs'] +
  sys.argv[3].split() + [sys.argv[5]]
)
