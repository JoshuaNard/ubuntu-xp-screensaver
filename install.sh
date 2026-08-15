#!/usr/bin/env bash
set -euo pipefail

if ! python3 -c 'import gi; gi.require_foreign("cairo")' >/dev/null 2>&1; then
    echo "Missing GTK Cairo adapter. Install it first:" >&2
    echo "  sudo apt install python3-gi-cairo" >&2
    exit 1
fi

app_dir="${HOME}/.local/lib/ubuntu-xp-screensaver"
unit_dir="${HOME}/.config/systemd/user"
mkdir -p "$app_dir" "$unit_dir"
install -m 755 beziers.py monitor.py "$app_dir/"
install -m 644 ubuntu-xp-screensaver.service "$unit_dir/"

# GNOME's own idle blanking would cover the animation before it starts.
if [[ ! -f "$app_dir/previous-idle-delay" ]]; then
    previous_idle="$(gsettings get org.gnome.desktop.session idle-delay)"
    printf '%s\n' "$previous_idle" > "$app_dir/previous-idle-delay"
fi
gsettings set org.gnome.desktop.session idle-delay 0

systemctl --user daemon-reload
systemctl --user enable --now ubuntu-xp-screensaver.service
echo "Installed. The Beziers screensaver will start after 15 idle minutes on AC power."
