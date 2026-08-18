#!/usr/bin/env python3
"""A Windows XP Beziers-inspired screensaver for GNOME/Wayland."""

import random
import signal
import sys
import time
from collections import deque
from datetime import datetime

import gi

try:
    gi.require_foreign("cairo")
except ImportError:
    sys.exit("Missing drawing support. Run: sudo apt install python3-gi-cairo")

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

BEZIER_SEGMENTS = 4
TRAIL_LENGTH = 30


class MovingPoint:
    def __init__(self, width, height):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.dx = random.choice((-1, 1)) * random.uniform(65, 145)
        self.dy = random.choice((-1, 1)) * random.uniform(65, 145)

    def update(self, width, height, elapsed):
        self.x += self.dx * elapsed
        self.y += self.dy * elapsed
        if self.x <= 0 or self.x >= width:
            self.dx *= -1
            self.x = min(max(self.x, 0), width)
        if self.y <= 0 or self.y >= height:
            self.dy *= -1
            self.y = min(max(self.y, 0), height)


class BezierLoop:
    def __init__(self, width, height):
        self.points = [MovingPoint(width, height) for _ in range(BEZIER_SEGMENTS * 3)]
        self.history = deque(maxlen=TRAIL_LENGTH)

    def update(self, width, height, elapsed):
        for point in self.points:
            point.update(width, height, elapsed)
        self.history.append(tuple((point.x, point.y) for point in self.points))

    def draw(self, cr):
        history = list(self.history)
        total = max(1, len(history))
        for index, points in enumerate(history):
            age = (index + 1) / total
            cr.set_source_rgb(0.16 + 0.84 * age, 0.0, 0.0)
            cr.set_line_width(1.25)
            cr.move_to(*points[0])
            for segment in range(BEZIER_SEGMENTS):
                first = segment * 3
                cr.curve_to(
                    *points[(first + 1) % len(points)],
                    *points[(first + 2) % len(points)],
                    *points[(first + 3) % len(points)],
                )
            cr.stroke()


class BeziersWindow(Gtk.Window):
    def __init__(self, monitor_index):
        super().__init__(title="Beziers Screensaver")
        self.set_app_paintable(True)
        self.set_keep_above(True)
        self.set_decorated(False)
        self.fullscreen_on_monitor(Gdk.Screen.get_default(), monitor_index)

        self.area = Gtk.DrawingArea()
        self.add(self.area)
        self.loop = None
        self.started = time.monotonic()
        self.last_frame_time = None

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
        self.area.add_tick_callback(self.tick)

    def hide_cursor(self, *_):
        cursor = Gdk.Cursor.new_for_display(self.get_display(), Gdk.CursorType.BLANK_CURSOR)
        self.get_window().set_cursor(cursor)

    def ensure_loop(self, width, height):
        if self.loop is None and width > 1 and height > 1:
            self.loop = BezierLoop(width, height)
            self.loop.update(width, height, 0)

    def draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        self.ensure_loop(width, height)
        if self.loop:
            self.loop.draw(cr)
        self.draw_clock(cr, height)
        return False

    @staticmethod
    def draw_clock(cr, height):
        now = datetime.now()
        time_text = now.strftime("%I:%M %p").lstrip("0")
        date_text = now.strftime("%A, %B %-d, %Y")
        left = 32

        cr.select_font_face("Sans", 0, 1)
        cr.set_source_rgb(1.0, 0.0, 0.0)
        cr.set_font_size(32)
        cr.move_to(left, height - 54)
        cr.show_text(time_text)

        cr.select_font_face("Sans", 0, 0)
        cr.set_source_rgb(0.82, 0.0, 0.0)
        cr.set_font_size(17)
        cr.move_to(left, height - 26)
        cr.show_text(date_text)

    def tick(self, _widget, frame_clock):
        frame_time = frame_clock.get_frame_time()
        if self.last_frame_time is None:
            self.last_frame_time = frame_time
            return True
        elapsed = min((frame_time - self.last_frame_time) / 1_000_000, 0.05)
        self.last_frame_time = frame_time
        width = self.area.get_allocated_width()
        height = self.area.get_allocated_height()
        self.ensure_loop(width, height)
        if self.loop:
            self.loop.update(width, height, elapsed)
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
    windows = [BeziersWindow(index) for index in range(display.get_n_monitors())]
    for window in windows:
        window.connect("destroy", Gtk.main_quit)
        window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
