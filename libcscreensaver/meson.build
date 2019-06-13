gnome = import('gnome')
pkgconfig = import('pkgconfig')

dbus_files = [
  [
    'cs-cinnamon-proxy',
    [
      ['org.Cinnamon', 'org.gtk.GDBus.C.Name', 'Cinnamon']
    ],
    'org.Cinnamon.xml'
  ],
  [
    'cs-session-presence-proxy',
    [
      ['org.gnome.SessionManager.Presence', 'org.gtk.GDBus.C.Name', 'SessionPresence']
    ],
    'org.gnome.SessionManager.Presence.xml'
  ],
  [
    'cs-upower-proxy',
    [
      ['org.freedesktop.UPower', 'org.gtk.GDBus.C.Name', 'UPower'],
      ['org.freedesktop.UPower.EnumerateDevices()[devices]', 'org.gtk.GDBus.C.ForceGVariant', 'true']
    ],
    'org.freedesktop.UPower.xml'
  ],
  [
    'cs-upower-device-proxy',
    [
      ['org.freedesktop.UPower.Device', 'org.gtk.GDBus.C.Name', 'UPowerDevice']
    ],
    'org.freedesktop.UPower.Device.xml'
  ],
  [
    'cs-login-manager-proxy',
    [
      ['org.freedesktop.login1.Manager', 'org.gtk.GDBus.C.Name', 'LogindManager']
    ],
    'org.freedesktop.login1.Manager.xml'
  ],
  [
    'cs-logind-session-proxy',
    [
      ['org.freedesktop.login1.Session', 'org.gtk.GDBus.C.Name', 'LogindSession']
    ],
    'org.freedesktop.login1.Session.xml'
  ],
  [
    'cs-consolekit-manager-proxy',
    [
      ['org.freedesktop.ConsoleKit.Manager', 'org.gtk.GDBus.C.Name', 'ConsoleKitManager']
    ],
    'org.freedesktop.ConsoleKit.Manager.xml'
  ],
  [
    'cs-consolekit-session-proxy',
    [
      ['org.freedesktop.ConsoleKit.Session', 'org.gtk.GDBus.C.Name', 'ConsoleKitSession']
    ],
    'org.freedesktop.ConsoleKit.Session.xml'
  ],
  [
    'cs-screensaver-proxy',
    [
      ['org.cinnamon.ScreenSaver', 'org.gtk.GDBus.C.Name', 'ScreenSaver']
    ],
    'org.cinnamon.ScreenSaver.xml'
  ],
  [
    'cs-keybinding-handler-proxy',
    [
      ['org.cinnamon.SettingsDaemon.KeybindingHandler', 'org.gtk.GDBus.C.Name', 'KeybindingHandler']
    ],
    'org.cinnamon.SettingsDaemon.KeybindingHandler.xml'
  ],
  [
    'cs-media-player-proxy',
    [
      ['org.mpris.MediaPlayer2.Player', 'org.gtk.GDBus.C.Name', 'MediaPlayer']
    ],
    'org.mpris.MediaPlayer2.Player.xml'
  ],
]

dbus_built = []
foreach dbus: dbus_files
  dbus_built += gnome.gdbus_codegen(dbus[0], dbus[2],
    namespace: 'Cs',
    annotations: dbus[1]
  )
endforeach

# non-pam auth implementations are not implemented at this time
auth_impl = 'pam'
cscreensaver_sources = [
  'cs-auth-@0@.c'.format(auth_impl),
  'subprocs.c',
  'subprocs.h',
  'setuid.c'
]

gir_sources = [
  'cs-gdk-event-filter.h',
  'cs-gdk-event-filter-x11.c',
  'cs-notification-watcher.h',
  'cs-notification-watcher.c',
  'cs-screen.h',
  'cs-screen-x11.c',
  dbus_built
]

libcscreensaver = library(
  'cscreensaver',
  cscreensaver_sources + gir_sources,
  version: '0.0.0',
  include_directories: inc,
  cpp_args: '-DG_LOG_DOMAIN="CScreensaver"',
  dependencies: [gobject, gtk, gdk, x11, xinerama, xrandr, xext, glib, gio, gthread, pam, m],
  install: true
)

install_headers('cs-auth.h', 'setuid.h', subdir: 'cinnamon-screensaver/libcscreensaver')

pkgconfig.generate(
  # TODO meson 0.46 replace libraries, name, version with positional library argument
  libraries: libcscreensaver,
  name: 'cscreensaver',
  version: meson.project_version(),
  description: 'Small utility lib used by cinnamon-screensaver v3.1+ to provide a GdkWindow filter (not currently introspectable)',
  subdirs: 'cscreensaver',
  # these should be their variables, but meson < 0.46 strikes again
  requires: ['gobject-2.0', 'gtk+-3.0', 'gdk-3.0']
)

cscreensaver_gir = gnome.generate_gir(
  libcscreensaver,
  sources: gir_sources,
  namespace: 'CScreensaver',
  nsversion: '1.0',
  identifier_prefix: 'Cs',
  symbol_prefix: 'cs_',
  includes: 'Gtk-3.0',
  install: true

)

test_passwd = executable(
  'test-passwd',
  'test-passwd.c',
  include_directories: inc,
  link_with: libcscreensaver,
  dependencies: [gobject, gtk, gdk],
  build_by_default: false
)
