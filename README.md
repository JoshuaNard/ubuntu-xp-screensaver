# Ubuntu XP-style screensaver

An animated Mystify-style screensaver for GNOME/Wayland. It starts after 15
minutes without input, but only when the laptop is on AC power and its lid is
open. Any key press, click, or mouse movement closes it.

## Install

Run this from the project directory in a graphical terminal:

```bash
chmod +x install.sh uninstall.sh mystify.py monitor.py
./install.sh
```

GNOME's built-in idle blanking is disabled so it cannot cover the animation.
This screensaver is visual only and does **not** lock the computer.

To preview it immediately:

```bash
./mystify.py
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
