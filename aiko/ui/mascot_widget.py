"""Original QPainter character renderer. Replace this widget for future renderers."""

import math
import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
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
        self.timer.setInterval(80)  # 12.5 fps, small vector drawing, no GPU animation engine.
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
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.width() / 200, self.height() / 250)
        elapsed = time.monotonic() - self.started
        motion = 0 if self.reduced_motion else math.sin(elapsed * 1.8)
        colors = self.profile.appearance
        outline = QColor("#30243e")

        def ellipse(x, y, w, h, color):
            p.setBrush(QColor(color))
            p.drawEllipse(QRectF(x, y, w, h))

        def path(points, color):
            shape = QPainterPath()
            shape.moveTo(*points[0])
            for point in points[1:]:
                shape.lineTo(*point)
            shape.closeSubpath()
            p.setBrush(QColor(color))
            p.drawPath(shape)

        p.setPen(Qt.PenStyle.NoPen)
        ellipse(44, 230, 112, 12, "#30303d")
        p.translate(0, motion * self.profile.animation["bounce_px"])
        p.setPen(QPen(outline, 2.4))
        # Hair silhouette and two soft side locks.
        ellipse(39, 33, 122, 151, colors["hair"])
        ellipse(26, 71, 37, 112, colors["hair"])
        ellipse(137, 71, 37, 112, colors["hair"])
        # Boots, stockings, dress, sleeves.
        ellipse(69, 194, 24, 38, "#eee4fb")
        ellipse(107, 194, 24, 38, "#eee4fb")
        ellipse(63, 221, 32, 15, colors["dress"])
        ellipse(105, 221, 32, 15, colors["dress"])
        path([(73, 141), (127, 141), (145, 203), (55, 203)], colors["dress"])
        path([(75, 144), (57, 148), (44, 181), (62, 188), (84, 164)], colors["accent"])
        path([(125, 144), (143, 148), (156, 181), (138, 188), (116, 164)], colors["accent"])
        ellipse(44, 176, 18, 22, colors["skin"])
        ellipse(138, 176, 18, 22, colors["skin"])
        path(
            [(79, 147), (100, 160), (121, 147), (115, 171), (100, 163), (85, 171)], colors["accent"]
        )
        ellipse(95, 158, 10, 12, "#f5d689")
        p.setPen(QPen(QColor(colors["accent"]), 3))
        p.drawLine(65, 196, 135, 196)
        # A slight head tilt is purely cosmetic.
        p.translate(100, 102)
        p.rotate(motion * 1.5)
        p.translate(-100, -102)
        p.setPen(QPen(outline, 2.4))
        ellipse(49, 58, 102, 91, colors["skin"])
        # Swept bangs.
        path(
            [
                (44, 86),
                (46, 60),
                (66, 39),
                (111, 34),
                (146, 57),
                (154, 92),
                (130, 79),
                (114, 55),
                (108, 86),
                (90, 65),
                (76, 89),
                (70, 65),
                (59, 91),
            ],
            colors["hair"],
        )
        blink = not self.reduced_motion and elapsed % self.profile.animation["blink_seconds"] < 0.16
        p.setPen(QPen(outline, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if blink or self.state == "happy":
            p.drawArc(QRectF(65, 99, 21, 14), 0, 180 * 16)
            p.drawArc(QRectF(114, 99, 21, 14), 0, 180 * 16)
        else:
            ellipse(67, 96, 18, 25, "#615087")
            ellipse(115, 96, 18, 25, "#615087")
            p.setPen(Qt.PenStyle.NoPen)
            ellipse(71, 98, 7, 9, "#ffffff")
            ellipse(119, 98, 7, 9, "#ffffff")
        p.setPen(Qt.PenStyle.NoPen)
        ellipse(57, 119, 18, 8, "#f2b2c2")
        ellipse(125, 119, 18, 8, "#f2b2c2")
        p.setPen(QPen(outline, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(91, 120, 18, 13), 180 * 16, 180 * 16)
        # Original five-point star hair pin.
        star = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = 12 if i % 2 == 0 else 5
            star.append((143 + math.cos(angle) * radius, 68 + math.sin(angle) * radius))
        path(star, "#ffe2a1")
        if self.state == "thinking":
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(3):
                ellipse(
                    80 + i * 16,
                    17 + (0 if self.reduced_motion else math.sin(elapsed * 4 + i) * 2),
                    8,
                    8,
                    colors["accent"],
                )
        p.end()
