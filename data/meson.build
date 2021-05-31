subdir('icons')

pamdir = get_option('pam-prefix')
if pamdir == ''
  pamdir = sysconfdir
endif

dbus_service = configure_file(
  output: 'org.cinnamon.ScreenSaver.service',
  input: 'org.cinnamon.ScreenSaver.service.in',
  # meson 0.49
  # configuration: { 'EXPANDED_BINDIR': bindir }
  configuration: misc_conf
)

if get_option('use-debian-pam')
  install_data(
    'cinnamon-screensaver.pam.debian',
    rename: 'cinnamon-screensaver',
    install_dir: join_paths(pamdir, 'pam.d')
  )
else
  install_data(
    'cinnamon-screensaver',
    install_dir: join_paths(pamdir, 'pam.d')
  )
endif

install_data('org.cinnamon.ScreenSaver.desktop', install_dir: join_paths(datadir, 'applications'))
install_data(dbus_service, install_dir: dbus_services_dir)
