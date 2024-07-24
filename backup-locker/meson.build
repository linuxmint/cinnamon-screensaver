backup_locker_data = configuration_data()
backup_locker_data.set_quoted('GETTEXT_PACKAGE', 'cinnamon-screensaver')
backup_locker_data.set_quoted('LOCALEDIR',   join_paths(get_option('prefix'), get_option('localedir')))
backup_locker_data.set_quoted('VERSION', meson.project_version())

bl_config = configure_file(output : 'config.h',
    configuration : backup_locker_data
)

bl_sources = [
'cs-backup-locker.c',
]

backup_locker = executable('cs-backup-locker',
  bl_sources,
  include_directories: inc,
  dependencies: [x11, gtk, glib],
  link_with: libcscreensaver,
  install_rpath: pkglibdir,
  install_dir: pkglibdir,
  install: true
)

install_data('cinnamon-unlock-desktop',
    install_dir: bindir,
    install_mode: 'rwxr-xr-x'
)
