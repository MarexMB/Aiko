from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMenu, QVBoxLayout, QWidget

from aiko.characters.profile import CharacterProfile
from aiko.config import Settings
from aiko.ui.mascot_widget import MascotWidget


def clamp_position(point: QPoint, size, screens) -> QPoint:
    """Choose the closest actual screen; don't clamp to the union's empty gaps."""
    if not screens:
        return point
    candidates = []
    for rect in screens:
        x = max(rect.left(), min(point.x(), rect.right() - size.width() + 1))
        y = max(rect.top(), min(point.y(), rect.bottom() - size.height() + 1))
        candidate = QPoint(x, y)
        candidates.append(((candidate - point).manhattanLength(), candidate))
    return min(candidates, key=lambda item: item[0])[1]


class MascotWindow(QWidget):
    toggle_chat = Signal()
    open_chat = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    position_changed = Signal(int, int)

    def __init__(self, profile: CharacterProfile, settings: Settings):
        super().__init__()
        self.setWindowTitle("Aiko mascot")
        self.setFixedSize(200, 250)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.character = MascotWidget(profile, self)
        layout.addWidget(self.character)
        self.press = None
        self.origin = QPoint()
        self.dragging = False
        self.apply_settings(settings)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        position = (
            QPoint(settings.mascot_x, settings.mascot_y)
            if settings.mascot_x is not None and settings.mascot_y is not None
            else QPoint(screen.right() - 240, screen.bottom() - 290)
        )
        self.move(self.clamp(position))
        app = QGuiApplication.instance()
        app.screenAdded.connect(self.screen_added)
        app.screenRemoved.connect(lambda screen: self.reclamp())
        for screen in app.screens():
            self.screen_added(screen)
        self.setToolTip("Click to chat · Drag to move · Right-click for menu")

    def screen_added(self, screen):
        screen.availableGeometryChanged.connect(lambda rect: self.reclamp())
        self.reclamp()

    def clamp(self, position):
        return clamp_position(
            position, self.size(), [s.availableGeometry() for s in QGuiApplication.screens()]
        )

    def reclamp(self):
        self.move(self.clamp(self.pos()))
        self.position_changed.emit(self.x(), self.y())

    def apply_settings(self, settings):
        visible = self.isVisible()
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        if settings.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.character.set_reduced_motion(settings.reduced_motion)
        if visible:
            self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press = event.globalPosition().toPoint()
            self.origin = self.pos()
            self.dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self.press is not None:
            delta = event.globalPosition().toPoint() - self.press
            if delta.manhattanLength() >= QApplication.startDragDistance():
                self.dragging = True
            if self.dragging:
                self.move(self.clamp(self.origin + delta))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.press is not None:
            if self.dragging:
                self.position_changed.emit(self.x(), self.y())
            else:
                self.toggle_chat.emit()
            self.press = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Open Chat", self.open_chat.emit)
        menu.addAction("Settings", self.settings_requested.emit)
        menu.addSeparator()
        menu.addAction("Quit", self.quit_requested.emit)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        event.ignore()
        self.quit_requested.emit()
