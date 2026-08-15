#!/usr/bin/env python3
"""A small, dependency-light tribute to the Windows XP Mystify screensaver."""

import math
import random
import signal
import time
from collections import deque

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


COLORS = (
    (0.10, 0.85, 1.0),
    (1.0, 0.12, 0.65),
    (0.35, 1.0, 0.15),
    (1.0, 0.70, 0.05),
    (0.65, 0.25, 1.0),
)


class Shape:
    def __init__(self, width, height, sides, color):
        self.color = color
        self.radius = random.uniform(55, 125)
        self.x = random.uniform(self.radius, max(self.radius, width - self.radius))
        self.y = random.uniform(self.radius, max(self.radius, height - self.radius))
        self.dx = random.choice((-1, 1)) * random.uniform(1.4, 2.8)
        self.dy = random.choice((-1, 1)) * random.uniform(1.4, 2.8)
        self.angle = random.random() * math.tau
        self.spin = random.uniform(-0.018, 0.018)
        self.sides = sides
        self.trail = deque(maxlen=18)

    def vertices(self):
        return [
            (
                self.x + math.cos(self.angle + i * math.tau / self.sides) * self.radius,
                self.y + math.sin(self.angle + i * math.tau / self.sides) * self.radius,
            )
            for i in range(self.sides)
        ]

    def update(self, width, height):
        self.x += self.dx
        self.y += self.dy
        self.angle += self.spin
        if self.x - self.radius <= 0 or self.x + self.radius >= width:
            self.dx *= -1
            self.x = min(max(self.x, self.radius), width - self.radius)
        if self.y - self.radius <= 0 or self.y + self.radius >= height:
            self.dy *= -1
            self.y = min(max(self.y, self.radius), height - self.radius)
        self.trail.append(self.vertices())

    def draw(self, cr):
        r, g, b = self.color
        frames = list(self.trail) or [self.vertices()]
        for index, vertices in enumerate(frames, start=1):
            strength = index / len(frames)
            cr.set_source_rgba(r, g, b, 0.08 + 0.92 * strength * strength)
            cr.set_line_width(1.0 + 3.0 * strength)
            for point_index, (x, y) in enumerate(vertices + vertices[:1]):
                (cr.move_to if point_index == 0 else cr.line_to)(x, y)
            cr.stroke()


class Screensaver(Gtk.Window):
    def __init__(self, monitor_index):
        super().__init__(title="Mystify Screensaver")
        self.set_app_paintable(True)
        self.set_keep_above(True)
        self.set_decorated(False)
        self.fullscreen_on_monitor(Gdk.Screen.get_default(), monitor_index)
        self.area = Gtk.DrawingArea()
        self.add(self.area)
        self.shapes = []
        self.started = time.monotonic()
        self.area.connect("draw", self.draw)
        self.connect("realize", self.hide_cursor)
        self.connect("key-press-event", lambda *_: Gtk.main_quit())
        self.connect("button-press-event", lambda *_: Gtk.main_quit())
        self.connect("motion-notify-event", self.on_motion)
        self.add_events(
            Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )
        GLib.timeout_add(16, self.tick)

    def hide_cursor(self, *_):
        cursor = Gdk.Cursor.new_for_display(
            self.get_display(), Gdk.CursorType.BLANK_CURSOR
        )
        self.get_window().set_cursor(cursor)

    def ensure_shapes(self, width, height):
        if not self.shapes and width > 1 and height > 1:
            self.shapes = [
                Shape(width, height, sides, color)
                for sides, color in zip((3, 4, 5, 6, 7), COLORS)
            ]

    def draw(self, widget, cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        self.ensure_shapes(width, height)
        for shape in self.shapes:
            shape.draw(cr)
        return False

    def tick(self):
        width, height = self.area.get_allocated_width(), self.area.get_allocated_height()
        for shape in self.shapes:
            shape.update(width, height)
        self.area.queue_draw()
        return True

    def on_motion(self, *_):
        if time.monotonic() - self.started > 0.75:
            Gtk.main_quit()


def main():
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("No graphical display is available")
    windows = [Screensaver(index) for index in range(display.get_n_monitors())]
    for window in windows:
        window.connect("destroy", Gtk.main_quit)
        window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
