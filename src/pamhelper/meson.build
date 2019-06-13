app_py = [
  'authClient.py',
]

install_data(app_py,
  install_dir: join_paths(pkgdatadir, 'pamhelper'))

executable('cinnamon-screensaver-pam-helper',
  'cinnamon-screensaver-pam-helper.c',
  dependencies: [gtk, glib],
  include_directories: inc,
  link_with: libcscreensaver,
  install: true,
  install_dir: libexecdir
)
