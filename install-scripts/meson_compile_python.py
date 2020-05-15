#!/usr/bin/python3

import os
import subprocess

pythondir = os.path.join(os.environ['MESON_INSTALL_PREFIX'], 'share', 'cinnamon-screensaver')

if not os.environ.get('DESTDIR'):
    print('Generating python bytecode...')
    subprocess.call(['sh', '-c', 'python3 -m compileall "%s"' % pythondir])
