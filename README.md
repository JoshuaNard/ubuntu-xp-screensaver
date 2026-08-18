# Ubuntu Beziers screensaver

A recreation of the classic Windows XP Beziers screensaver for GNOME/Wayland,
with a matching red clock and date in the lower-left corner. It starts after 15
minutes without input, but only when the laptop is on AC power and its lid is
open. Any key press, click, or mouse movement closes it.

## Requirements

Install GTK's Python Cairo adapter, which Ubuntu packages separately:

```bash
sudo apt install python3-gi-cairo
```

## Install

Run this from the project directory in a terminal:

```bash
chmod +x install.sh uninstall.sh beziers.py monitor.py
./install.sh
```

GNOME's built-in idle blanking is disabled so it cannot cover the animation.
This screensaver is visual only and does **not** lock the computer.

To preview it immediately:

```bash
make
```

The named target does the same thing:

```bash
make screensaver
```

To inspect the background service:

```bash
systemctl --user status ubuntu-xp-screensaver.service
journalctl --user -u ubuntu-xp-screensaver.service
```

To remove it and restore the prior GNOME idle setting:

```bash
./uninstall.sh
```
