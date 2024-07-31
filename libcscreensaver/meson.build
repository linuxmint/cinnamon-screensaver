gnome = import('gnome')
pkgconfig = import('pkgconfig')

dbus_files = [
  [
    'cs-cinnamon-proxy',
    [
      ['org.Cinnamon', 'org.gtk.GDBus.C.Name', 'Cinnamon']
    ],
    'org.Cinnamon'
  ],
  [
    'cs-session-presence-proxy',
    [
      ['org.gnome.SessionManager.Presence', 'org.gtk.GDBus.C.Name', 'SessionPresence']
    ],
    'org.gnome.SessionManager.Presence'
  ],
  [
    'cs-upower-proxy',
    [
      ['org.freedesktop.UPower', 'org.gtk.GDBus.C.Name', 'UPower'],
      ['org.freedesktop.UPower.EnumerateDevices()[devices]', 'org.gtk.GDBus.C.ForceGVariant', 'true']
    ],
    'org.freedesktop.UPower'
  ],
  [
    'cs-upower-device-proxy',
    [
      ['org.freedesktop.UPower.Device', 'org.gtk.GDBus.C.Name', 'UPowerDevice']
    ],
    'org.freedesktop.UPower.Device'
  ],
  [
    'cs-login-manager-proxy',
    [
      ['org.freedesktop.login1.Manager', 'org.gtk.GDBus.C.Name', 'LogindManager']
    ],
    'org.freedesktop.login1.Manager'
  ],
  [
    'cs-logind-session-proxy',
    [
      ['org.freedesktop.login1.Session', 'org.gtk.GDBus.C.Name', 'LogindSession']
    ],
    'org.freedesktop.login1.Session'
  ],
  [
    'cs-consolekit-manager-proxy',
    [
      ['org.freedesktop.ConsoleKit.Manager', 'org.gtk.GDBus.C.Name', 'ConsoleKitManager']
    ],
    'org.freedesktop.ConsoleKit.Manager'
  ],
  [
    'cs-consolekit-session-proxy',
    [
      ['org.freedesktop.ConsoleKit.Session', 'org.gtk.GDBus.C.Name', 'ConsoleKitSession']
    ],
    'org.freedesktop.ConsoleKit.Session'
  ],
  [
    'cs-screensaver-proxy',
    [
      ['org.cinnamon.ScreenSaver', 'org.gtk.GDBus.C.Name', 'ScreenSaver']
    ],
    'org.cinnamon.ScreenSaver'
  ],
  [
    'cs-keybinding-handler-proxy',
    [
      ['org.cinnamon.SettingsDaemon.KeybindingHandler', 'org.gtk.GDBus.C.Name', 'KeybindingHandler']
    ],
    'org.cinnamon.SettingsDaemon.KeybindingHandler'
  ],
  [
    'cs-media-player-proxy',
    [
      ['org.mpris.MediaPlayer2.Player', 'org.gtk.GDBus.C.Name', 'MediaPlayer']
    ],
    'org.mpris.MediaPlayer2.Player'
  ],
  [
    'cs-muffin-displayconfig-proxy',
    [
      ['org.cinnamon.Muffin.DisplayConfig', 'org.gtk.GDBus.C.Name', 'MuffinDisplayConfig']
    ],
    'org.cinnamon.Muffin.DisplayConfig'
  ],
  [
    'cs-accounts-service-proxy',
    [
      ['org.freedesktop.Accounts', 'org.gtk.GDBus.C.Name', 'AccountsService']
    ],
    'org.freedesktop.Accounts'
  ],
  [
    'cs-accounts-user-proxy',
    [
      ['org.freedesktop.Accounts.User', 'org.gtk.GDBus.C.Name', 'AccountsUser']
    ],
    'org.freedesktop.Accounts.User'
  ],
]

dbus_built = []
foreach dbus: dbus_files
  dbus_built += gnome.gdbus_codegen(dbus[0], '@0@.xml'.format(dbus[2]),
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
  'cs-event-grabber.h',
  'cs-event-grabber.c',
  'cs-gdk-event-filter.h',
  'cs-gdk-event-filter-x11.c',
  'cs-notification-watcher.h',
  'cs-notification-watcher.c',
  'cs-screen.h',
  'cs-screen-x11.c',
  dbus_built
]

libcscreensaver_deps = [gobject, gtk, gdk, x11, xrandr, xext, glib, gio, gio_unix, gthread, pam, m, xdo]
if use_xinerama
  libcscreensaver_deps += xinerama
endif

libcscreensaver = library(
  'cscreensaver',
  cscreensaver_sources + gir_sources,
  include_directories: inc,
  cpp_args: '-DG_LOG_DOMAIN="CScreensaver"',
  dependencies: libcscreensaver_deps,
  install_dir: pkglibdir,
  install: true
)

cscreensaver_gir = gnome.generate_gir(
  libcscreensaver,
  sources: gir_sources,
  namespace: 'CScreensaver',
  nsversion: '1.0',
  identifier_prefix: 'Cs',
  symbol_prefix: 'cs_',
  includes: 'Gtk-3.0',
  install_dir_typelib: typelibdir,
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
