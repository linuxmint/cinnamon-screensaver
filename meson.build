project('cinnamon-screensaver', 'c', version: '5.0.4', meson_version: '>=0.46.0')

cc = meson.get_compiler('c')

conf = configuration_data()
conf.set_quoted('PACKAGE', meson.project_name())
conf.set_quoted('GETTEXT_PACKAGE', meson.project_name())

# project options

# commandline options
prefix = get_option('prefix')
bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
pkgdatadir = join_paths(datadir, meson.project_name())
libexecdir = join_paths(prefix, get_option('libexecdir'))
libdir = join_paths(prefix, get_option('libdir'))
#needed?
sysconfdir = join_paths(prefix, get_option('sysconfdir'))
localstatedir = join_paths(prefix, get_option('localstatedir'))
localedir = join_paths(prefix, get_option('localedir'))

# object used for configure_file because meson 0.47 is needed for dicts
# and 0.49 for using them in configure_file
misc_conf = configuration_data()
misc_conf.set('prefix', prefix)
misc_conf.set('EXPANDED_BINDIR', bindir)
misc_conf.set('datadir', datadir)
misc_conf.set('pkgdatadir', pkgdatadir)
misc_conf.set('libexecdir', libexecdir)
misc_conf.set('libdir', libdir)
misc_conf.set('PACKAGE', meson.project_name())
misc_conf.set('VERSION', meson.project_version())
misc_conf.set('GETTEXT_PACKAGE', meson.project_name())

gtk = dependency('gtk+-3.0')
glib = dependency('glib-2.0')
gio = dependency('gio-2.0')
gthread = dependency('gthread-2.0')
gobject = dependency('gobject-2.0')
gdk = dependency('gdk-x11-3.0')
x11 = dependency('x11')
xext = dependency('xext')
xrandr = dependency('xrandr', required: false)
m = cc.find_library('m')
dbus_services_dir = dependency('dbus-1').get_pkgconfig_variable('session_bus_services_dir', define_variable: ['datadir', datadir])

# check for symbols and headers
foreach header : [
  'unistd.h'
  ]
  if cc.has_header(header)
    conf.set('HAVE_' + header.underscorify().to_upper(), true)
  endif
endforeach
foreach sym : [
  'sigaction'
  ]
  if cc.has_function(sym, args : '-D_GNU_SOURCE')
    conf.set('HAVE_' + sym.to_upper(), true)
  endif
endforeach

use_xinerama = get_option('xinerama')
if use_xinerama
  if host_machine.system() == 'solaris'
    xinerama = cc.find_library('Xext')
    xinerama_h = cc.has_header('X11/extensions/xinerama.h')
    if not xinerama.found() or xinerama_h
      error('could not find usable xinerama library')
    endif
    conf.set('HAVE_SOLARIS_XINERAMA', 1)
  else
    xinerama = dependency('xinerama')
    conf.set('HAVE_XFREE_XINERAMA', 1)
  endif
  conf.set('HAVE_XINERAMA', 1)
endif

pam_compile = '''#include <stdio.h>
                 #include <stdlib.h>
                 #include <security/pam_appl.h>
                 int main ()
                 {
                     pam_handle_t *pamh = 0;
                     char *s = pam_strerror(pamh, PAM_SUCCESS);
                     return 0;
                 }'''

pam = cc.find_library('pam')
if not cc.has_function('sigtimedwait')
  pam = [pam, cc.find_library('rt')]
endif
if cc.compiles(pam_compile)
  conf.set('PAM_STRERROR_TWO_ARGS', 1)
endif
# this check is not used anywhere
if cc.has_function('pam_syslog', dependencies: pam)
  conf.set('HAVE_PAM_SYSLOG', 1)
endif
# Sun-type pam, this check is not used anywhere
if not cc.has_header_symbol('security/pam_appl.h', 'const struct pam_message')
  conf.set('PAM_MESSAGE_NONCONST', 1)
endif

# do we care if the header exists? Just use pkg-config
if cc.has_header('X11/extensions/Xrandr.h')
  xrandr = 'Xrandr'
else
  xrandr = ''
endif
xrandr = cc.find_library(xrandr, required: false)

if xrandr.found()
  conf.set('HAVE_RANDR', 1)
endif
if cc.has_header('X11/extensions/shape.h')
  conf.set('HAVE_SHAPE_EXT', 1)
endif

conf_h = configure_file(
  output : 'config.h',
  configuration : conf)

inc = include_directories('.')

if not get_option('deprecated-warnings')
  add_global_arguments([
      '-Wno-deprecated-declarations',
      '-Wno-deprecated',
      '-Wno-declaration-after-statement',
      '-DGLIB_DISABLE_DEPRECATION_WARNINGS',
    ],
    language: 'c',
  )
endif

subdir('install-scripts')
subdir('libcscreensaver')
subdir('data')
subdir('src')
subdir('backup-locker')
