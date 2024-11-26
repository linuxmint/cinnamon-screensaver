subdir('dbusdepot')
subdir('pamhelper')
subdir('util')
subdir('widgets')

# will not subdir the binfiles directory as it only contains symlinked scripts

config_py = configure_file(
  output: 'config.py',
  input: 'config.py.in',
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
  'weather.py'
]

app_css = [
  'cinnamon-screensaver.css',
]

install_data(app_py + app_css,
  install_dir: pkgdatadir
)

app_scripts = [
  ['cinnamon-screensaver-main.py', 'cinnamon-screensaver'],
  ['cinnamon-screensaver-command.py', 'cinnamon-screensaver-command']
]

foreach script : app_scripts
  prefix_info = configuration_data()
  prefix_info.set('install_dir', pkgdatadir)
  prefix_info.set('target', script[0])
  prefix_info.set('pkglibdir', pkglibdir)
  prefix_info.set('typelibdir', typelibdir)

  bin_file = configure_file(
    input : 'binfile.in',
    output: script[1],
    configuration: prefix_info,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x'
  )

  install_data(
      script[0],
      install_dir: pkgdatadir,
      install_mode: 'rwxr-xr-x'
  )
endforeach
