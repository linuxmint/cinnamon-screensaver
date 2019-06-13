subdir('icons')

pamdir = get_option('pam-prefix')
if pamdir == ''
  pamdir = sysconfdir
endif

desktop = configure_file(
  output: 'cinnamon-screensaver.desktop',
  input: 'cinnamon-screensaver.desktop.in',
  configuration: { 'VERSION': meson.project_version() }
)

dbus_service = configure_file(
  output: 'org.cinnamon.ScreenSaver.service',
  input: 'org.cinnamon.ScreenSaver.service.in',
  configuration: { 'EXPANDED_BINDIR': bindir }
)

install_data('cinnamon-screensaver', install_dir: join_paths(pamdir, 'pam.d'))
install_data(desktop, install_dir: join_paths(datadir, 'applications'))
install_data(dbus_service, install_dir: dbus_services_dir)
