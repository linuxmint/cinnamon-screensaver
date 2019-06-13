icondir = join_paths(datadir, 'icons', 'hicolor', 'scalable')

icons = [
  'hicolor_actions_scalable_screensaver-unlock-symbolic.svg',
  'hicolor_actions_scalable_screensaver-switch-users-symbolic.svg',
  'hicolor_status_scalable_screensaver-blank.svg',
  'hicolor_status_scalable_screensaver-notification-symbolic.svg',
]

foreach icon: icons
  tokens = icon.split('_')
  install_data(
    icon,
    install_dir: join_paths(icondir, tokens[1]),
    # install_dir: join_paths(datadir, 'icons', tokens[0], tokens[2], tokens[1]),
    rename: tokens[3])
endforeach
