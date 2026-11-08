"""Original pixel-art renderer on a 40×50 grid, scaled without smoothing."""

import math
import time

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPolygon
from PySide6.QtWidgets import QWidget

from aiko.characters.profile import CharacterProfile


class MascotWidget(QWidget):
    def __init__(self, profile: CharacterProfile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.state = "idle"
        self.reduced_motion = False
        self.started = time.monotonic()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.timer = QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        self.happy_timer = QTimer(self)
        self.happy_timer.setSingleShot(True)
        self.happy_timer.timeout.connect(lambda: self.set_state("idle"))

    def set_state(self, state: str):
        self.happy_timer.stop()
        self.state = state
        if state == "happy":
            self.happy_timer.start(2400)
        self.update()

    def set_reduced_motion(self, enabled: bool):
        self.reduced_motion = enabled
        if enabled:
            self.timer.stop()
        else:
            self.timer.start()
        self.update()

    def paintEvent(self, event):
        elapsed = time.monotonic() - self.started
        colors = self.profile.appearance
        image = QImage(40, 50, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        sprite = QPainter(image)
        sprite.setPen(Qt.PenStyle.NoPen)
        outline = "#302c47"
        hair = colors["hair"]
        shadow = QColor(hair).darker(125).name()
        highlight = QColor(hair).lighter(125).name()

        def box(x, y, w, h, color):
            sprite.fillRect(x, y, w, h, QColor(color))

        def shape(points, color):
            sprite.setBrush(QColor(color))
            sprite.drawPolygon(QPolygon([QPoint(x, y) for x, y in points]))

        box(10, 47, 20, 1, "#343246")
        # Snap movement to the sprite grid; fractional transforms blur pixel edges.
        bounce = 0
        if not self.reduced_motion:
            bounce = round(math.sin(elapsed * 1.8) * self.profile.animation["bounce_px"] / 5)
        sprite.translate(0, bounce)

        # Stepped hair silhouette and long side locks.
        shape(
            [
                (13, 6),
                (26, 6),
                (26, 7),
                (29, 7),
                (29, 9),
                (31, 9),
                (31, 13),
                (33, 13),
                (33, 30),
                (31, 30),
                (31, 34),
                (26, 34),
                (26, 30),
                (13, 30),
                (13, 34),
                (8, 34),
                (8, 30),
                (6, 30),
                (6, 14),
                (8, 14),
                (8, 10),
                (10, 10),
                (10, 8),
                (13, 8),
            ],
            outline,
        )
        shape(
            [
                (13, 7),
                (25, 7),
                (25, 8),
                (28, 8),
                (28, 10),
                (30, 10),
                (30, 15),
                (32, 15),
                (32, 29),
                (30, 29),
                (30, 33),
                (27, 33),
                (27, 28),
                (12, 28),
                (12, 33),
                (9, 33),
                (9, 29),
                (7, 29),
                (7, 15),
                (9, 15),
                (9, 11),
                (11, 11),
                (11, 9),
                (13, 9),
            ],
            hair,
        )
        box(8, 19, 2, 11, shadow)
        box(29, 18, 2, 13, shadow)
        box(10, 13, 1, 17, highlight)
        box(31, 17, 1, 9, highlight)

        # Stockings and square-toed ankle boots.
        box(14, 39, 5, 7, outline)
        box(22, 39, 5, 7, outline)
        box(15, 40, 3, 5, "#f3edff")
        box(23, 40, 3, 5, "#f3edff")
        box(13, 45, 6, 2, outline)
        box(22, 45, 6, 2, outline)
        box(14, 45, 4, 1, colors["accent"])
        box(23, 45, 4, 1, colors["accent"])

        # Violet dress, puff sleeves, tiny hands and pleated hem.
        shape(
            [
                (15, 28),
                (24, 28),
                (24, 30),
                (27, 30),
                (27, 35),
                (29, 35),
                (29, 40),
                (10, 40),
                (10, 36),
                (12, 36),
                (12, 30),
                (15, 30),
            ],
            outline,
        )
        shape(
            [
                (15, 29),
                (24, 29),
                (24, 34),
                (26, 34),
                (26, 38),
                (28, 38),
                (28, 39),
                (11, 39),
                (11, 37),
                (13, 37),
                (13, 34),
                (15, 34),
            ],
            colors["dress"],
        )
        box(12, 31, 3, 5, colors["accent"])
        box(25, 31, 3, 5, colors["accent"])
        box(10, 35, 4, 4, outline)
        box(27, 35, 4, 4, outline)
        box(11, 35, 2, 3, colors["skin"])
        box(28, 35, 2, 3, colors["skin"])
        box(14, 37, 1, 2, colors["accent"])
        box(19, 35, 1, 4, colors["accent"])
        box(24, 37, 1, 2, colors["accent"])
        box(12, 39, 16, 1, "#e8dcff")
        shape([(15, 29), (19, 31), (24, 29), (23, 32), (20, 33), (17, 32)], "#fff5e9")
        box(18, 32, 4, 2, "#66b9f4")
        box(19, 32, 2, 1, "#d1f1ff")

        # Face and stepped fringe.
        shape(
            [
                (12, 15),
                (27, 15),
                (27, 25),
                (25, 25),
                (25, 27),
                (23, 27),
                (23, 28),
                (16, 28),
                (16, 27),
                (13, 27),
                (13, 25),
                (11, 25),
                (11, 17),
            ],
            outline,
        )
        shape(
            [
                (13, 15),
                (26, 15),
                (26, 24),
                (24, 24),
                (24, 26),
                (22, 26),
                (22, 27),
                (17, 27),
                (17, 26),
                (14, 26),
                (14, 24),
                (12, 24),
                (12, 17),
            ],
            colors["skin"],
        )
        shape(
            [
                (11, 13),
                (13, 10),
                (25, 10),
                (28, 13),
                (28, 19),
                (26, 19),
                (26, 17),
                (23, 17),
                (23, 14),
                (21, 14),
                (21, 18),
                (19, 18),
                (19, 16),
                (17, 16),
                (17, 14),
                (16, 14),
                (16, 18),
                (13, 18),
                (13, 20),
                (11, 20),
            ],
            shadow,
        )
        shape(
            [
                (11, 12),
                (13, 9),
                (25, 9),
                (28, 12),
                (28, 17),
                (26, 17),
                (26, 15),
                (23, 15),
                (23, 12),
                (21, 12),
                (21, 16),
                (19, 16),
                (19, 14),
                (17, 14),
                (17, 12),
                (16, 12),
                (16, 16),
                (13, 16),
                (13, 18),
                (11, 18),
            ],
            hair,
        )
        box(14, 9, 10, 1, highlight)
        box(12, 11, 5, 1, highlight)
        box(23, 11, 3, 1, highlight)

        blink = not self.reduced_motion and elapsed % self.profile.animation["blink_seconds"] < 0.16
        for x in (14, 23):
            if self.state == "happy":
                box(x, 20, 3, 1, outline)
                box(x - 1, 21, 1, 1, outline)
                box(x + 3, 21, 1, 1, outline)
            elif blink:
                box(x, 22, 3, 1, outline)
            else:
                box(x, 19, 3, 1, outline)
                box(x, 20, 3, 4, colors["eyes"])
                box(x, 20, 1, 2, "#ffffff")
                box(x + 1, 20, 1, 2, "#174d89")
                box(x + 1, 23, 2, 1, "#78d9ff")
        box(12, 24, 3, 1, "#ed9ea9")
        box(25, 24, 2, 1, "#ed9ea9")
        box(19, 25, 2, 1, "#aa646e")

        # Blue pixel star: a small accent against the yellow hair.
        shape(
            [
                (28, 11),
                (29, 13),
                (31, 13),
                (30, 15),
                (30, 17),
                (28, 16),
                (26, 17),
                (26, 15),
                (25, 13),
                (27, 13),
            ],
            outline,
        )
        box(28, 12, 1, 4, "#75d1ff")
        box(26, 14, 5, 1, "#75d1ff")
        box(28, 13, 1, 1, "#ffffff")
        if self.state == "thinking":
            for i in range(3):
                offset = 0 if self.reduced_motion else round(math.sin(elapsed * 4 + i))
                box(15 + i * 4, 2 + offset, 2, 2, colors["accent"])
        sprite.end()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        scale = max(1, min(self.width() // 40, self.height() // 50))
        target = QRect(
            (self.width() - 40 * scale) // 2,
            (self.height() - 50 * scale) // 2,
            40 * scale,
            50 * scale,
        )
        p.drawImage(target, image)
        p.end()
