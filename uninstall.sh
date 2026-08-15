#!/usr/bin/env bash
set -euo pipefail

app_dir="${HOME}/.local/lib/ubuntu-xp-screensaver"
systemctl --user disable --now ubuntu-xp-screensaver.service 2>/dev/null || true
rm -f "${HOME}/.config/systemd/user/ubuntu-xp-screensaver.service"
if [[ -f "$app_dir/previous-idle-delay" ]]; then
    previous_idle="$(<"$app_dir/previous-idle-delay")"
    gsettings set org.gnome.desktop.session idle-delay "$previous_idle"
fi
rm -rf "$app_dir"
systemctl --user daemon-reload
echo "Removed and restored the previous GNOME idle-delay setting."
