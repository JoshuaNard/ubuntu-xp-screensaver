#!/usr/bin/env python3
"""Launch Mystify after idle timeout, but only while charging with lid open."""

import os
import signal
import subprocess
import time

from gi.repository import Gio, GLib


IDLE_MS = int(os.environ.get("SCREENSAVER_IDLE_SECONDS", "900")) * 1000
HERE = os.path.dirname(os.path.abspath(__file__))
child = None
stopped = False


def quit_monitor(*_args):
    global stopped
    stopped = True
    if child and child.poll() is None:
        child.terminate()


def dbus_proxy(bus, name, path, interface):
    return Gio.DBusProxy.new_for_bus_sync(
        bus, Gio.DBusProxyFlags.NONE, None, name, path, interface, None
    )


def main():
    global child
    signal.signal(signal.SIGTERM, quit_monitor)
    signal.signal(signal.SIGINT, quit_monitor)

    idle = dbus_proxy(
        Gio.BusType.SESSION,
        "org.gnome.Mutter.IdleMonitor",
        "/org/gnome/Mutter/IdleMonitor/Core",
        "org.gnome.Mutter.IdleMonitor",
    )
    power = dbus_proxy(
        Gio.BusType.SYSTEM,
        "org.freedesktop.UPower",
        "/org/freedesktop/UPower",
        "org.freedesktop.UPower",
    )
    dismissed_during_current_idle = False

    while not stopped:
        try:
            idle_ms = idle.call_sync("GetIdletime", None, Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
            on_battery = power.get_cached_property("OnBattery").unpack()
            lid_value = power.get_cached_property("LidIsClosed")
            lid_open = lid_value is None or not lid_value.unpack()
            allowed = not on_battery and lid_open

            if idle_ms < IDLE_MS:
                dismissed_during_current_idle = False
            if child and child.poll() is not None:
                child = None
                dismissed_during_current_idle = True
            if child and not allowed:
                child.terminate()
                child = None
            if allowed and idle_ms >= IDLE_MS and not child and not dismissed_during_current_idle:
                child = subprocess.Popen([os.path.join(HERE, "mystify.py")])
        except GLib.Error as error:
            print(f"screensaver monitor: {error}", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
