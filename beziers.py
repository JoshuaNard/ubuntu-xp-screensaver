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

DIGIT_SEGMENTS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abdeg",
    "3": "abcdg",
    "4": "bcfg",
    "5": "acdfg",
    "6": "acdefg",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
}
SEGMENT_LINES = {
    "a": (4, 0, 20, 0),
    "b": (24, 4, 24, 18),
    "c": (24, 24, 24, 38),
    "d": (4, 42, 20, 42),
    "e": (0, 24, 0, 38),
    "f": (0, 4, 0, 18),
    "g": (4, 21, 20, 21),
}


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
        time_text = now.strftime("%I:%M").lstrip("0")
        period_text = now.strftime("%p")
        date_text = now.strftime("%A, %B %-d, %Y")
        left = 32
        top = height - 104

        end_x = BeziersWindow.draw_led_time(cr, time_text, left, top)

        cr.select_font_face("Quicksand", 0, 1)
        cr.set_source_rgb(0.82, 0.0, 0.0)
        cr.set_font_size(12)
        cr.move_to(end_x + 4, top + 42)
        cr.show_text(period_text)

        cr.select_font_face("Quicksand", 0, 0)
        cr.set_source_rgb(0.82, 0.0, 0.0)
        cr.set_font_size(17)
        cr.move_to(left, height - 26)
        cr.show_text(date_text)

    @staticmethod
    def draw_led_time(cr, text, left, top):
        x = left
        cr.set_line_cap(1)
        for character in text:
            if character == ":":
                cr.set_source_rgb(1.0, 0.0, 0.0)
                for dot_y in (14, 30):
                    cr.arc(x + 5, top + dot_y, 3, 0, 6.2832)
                    cr.fill()
                x += 16
                continue

            active = DIGIT_SEGMENTS[character]
            for segment, (x1, y1, x2, y2) in SEGMENT_LINES.items():
                color = (1.0, 0.0, 0.0) if segment in active else (0.16, 0.0, 0.0)
                cr.set_source_rgb(*color)
                cr.set_line_width(5)
                cr.move_to(x + x1, top + y1)
                cr.line_to(x + x2, top + y2)
                cr.stroke()
            x += 34
        return x

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
