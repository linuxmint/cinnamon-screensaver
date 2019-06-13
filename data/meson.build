subdir('icons')

pamdir = get_option('pam-prefix')
if pamdir == ''
  pamdir = sysconfdir
endif

desktop = configure_file(
  output: 'cinnamon-screensaver.desktop',
  input: 'cinnamon-screensaver.desktop.in',
  # meson 0.49
  # configuration: { 'VERSION': meson.project_version() }
  configuration: misc_conf
)

dbus_service = configure_file(
  output: 'org.cinnamon.ScreenSaver.service',
  input: 'org.cinnamon.ScreenSaver.service.in',
  # meson 0.49
  # configuration: { 'EXPANDED_BINDIR': bindir }
  configuration: misc_conf
)

install_data('cinnamon-screensaver', install_dir: join_paths(pamdir, 'pam.d'))
install_data(desktop, install_dir: join_paths(datadir, 'applications'))
install_data(dbus_service, install_dir: dbus_services_dir)
