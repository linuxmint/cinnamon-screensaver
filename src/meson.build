subdir('dbusdepot')
subdir('pamhelper')
subdir('util')
subdir('widgets')

# will not subdir the binfiles directory as it only contains symlinked scripts

config_py = configure_file(
  output: 'config.py',
  input: 'config.py.in',
  # meson 0.49
  #configuration: {
  #  'prefix': prefix,
  #  'datadir': datadir,
  #  'pkgdatadir': pkgdatadir,
  #  'libexecdir': libexecdir,
  #  'libdir': libdir,
  #  'PACKAGE': meson.project_name(),
  #  'VERSION': meson.project_version(),
  #  'GETTEXT_PACKAGE': meson.project_name()
  #}
  configuration: misc_conf
)

app_py = [
  '__init__.py',
  'albumArt.py',
  'audioPanel.py',
  'baseWindow.py',
  'clock.py',
  config_py,
  'constants.py',
  'floating.py',
  'infoPanel.py',
  'manager.py',
  'monitorView.py',
  'osk.py',
  'passwordEntry.py',
  'playerControl.py',
  'service.py',
  'singletons.py',
  'stage.py',
  'status.py',
  'unlock.py',
  'volumeControl.py',
]

app_css = [
  'cinnamon-screensaver.css',
]

app_scripts = [
  ['cinnamon-screensaver-main.py', 'cinnamon-screensaver'],
  ['cinnamon-screensaver-command.py', 'cinnamon-screensaver-command']
]

install_data(app_py + app_css,
  install_dir: pkgdatadir
)

foreach script : app_scripts
  install_data(script[0], install_dir: pkgdatadir)
  meson.add_install_script('sh', '-c', 'mkdir -p "$DESTDIR/@0@"'.format(bindir))
  meson.add_install_script('sh', '-c',
    'ln -sf "@0@" "$DESTDIR/@1@"'.format(join_paths(pkgdatadir, script[0]), join_paths(bindir, script[1])))
endforeach
