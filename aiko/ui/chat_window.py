import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

STYLE = """
QWidget { background: #191720; color: #e9e3f2; font-family: 'Segoe UI'; font-size: 13px; }
QMainWindow { background: #191720; }
QLabel#title { font-size: 25px; font-weight: 700; color: #e5d6ff; }
QLabel#subtitle { color: #aaa0b9; }
QPushButton { background: #30293e; border: 1px solid #4a3e60; border-radius: 7px; padding: 8px 12px; }
QPushButton:hover { background: #49365f; }
QPushButton:disabled { color: #797183; border-color: #302939; }
QPushButton#send { background: #9c78dd; color: #16111f; font-weight: 700; }
QPlainTextEdit, QTextBrowser, QLineEdit, QSpinBox, QComboBox { background: #211d2b; border: 1px solid #3c334d; border-radius: 8px; padding: 8px; selection-background-color: #7652a8; }
QTextBrowser { border: none; }
QLabel#status { color: #c8b2e9; padding: 4px; }
QMenu { border: 1px solid #5d4877; }
QMenu::item:selected { background: #49365f; }
"""


class MessageInput(QPlainTextEdit):
    submitted = Signal()

    def keyPressEvent(self, event):
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submitted.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class ChatWindow(QMainWindow):
    send_requested = Signal(str)
    stop_requested = Signal()
    new_requested = Signal()
    open_requested = Signal(int)
    delete_requested = Signal()
    clear_requested = Signal()
    settings_requested = Signal()
    check_requested = Signal()
    quit_requested = Signal()
    older_requested = Signal()

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.setWindowTitle(f"{name} · Local companion")
        self.resize(570, 730)
        self.setMinimumSize(450, 480)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)
        title = QLabel(f"✦  {name}")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("A little company. A little curiosity. All local.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        toolbar = QHBoxLayout()
        self.sessions = QComboBox()
        self.sessions.setMinimumWidth(140)
        self.sessions.activated.connect(
            lambda i: self.open_requested.emit(self.sessions.itemData(i))
        )
        toolbar.addWidget(self.sessions, 1)
        self.new = self.button("New chat", self.new_requested, toolbar)
        self.delete = self.button("Delete", self.delete_requested, toolbar)
        layout.addLayout(toolbar)
        self.older = QPushButton("Show older messages")
        self.older.clicked.connect(self.older_requested.emit)
        layout.addWidget(self.older)
        self.transcript = QTextBrowser()
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.document().setMaximumBlockCount(2000)
        layout.addWidget(self.transcript, 1)
        self.status = QLabel("Local connection not checked")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.input = MessageInput()
        self.input.setPlaceholderText("Say hello…  Enter to send · Shift+Enter for a new line")
        self.input.setMaximumHeight(110)
        self.input.submitted.connect(self.submit)
        layout.addWidget(self.input)
        controls = QHBoxLayout()
        self.settings = self.button("Settings", self.settings_requested, controls)
        self.check = self.button("Check connection", self.check_requested, controls)
        controls.addStretch()
        self.stop = self.button("Stop", self.stop_requested, controls)
        self.stop.setEnabled(False)
        self.send = QPushButton("Send ↗")
        self.send.setObjectName("send")
        self.send.clicked.connect(self.submit)
        controls.addWidget(self.send)
        layout.addLayout(controls)
        footer = QHBoxLayout()
        self.clear = self.button("Clear all history", self.clear_requested, footer)
        footer.addStretch()
        self.button("Quit Aiko", self.quit_requested, footer)
        layout.addLayout(footer)

    @staticmethod
    def button(text, signal, layout):
        button = QPushButton(text)
        button.clicked.connect(signal.emit)
        layout.addWidget(button)
        return button

    def submit(self):
        text = self.input.toPlainText().strip()
        if text and self.send.isEnabled():
            self.send_requested.emit(text)

    def set_busy(self, busy: bool):
        for widget in (
            self.send,
            self.new,
            self.delete,
            self.clear,
            self.sessions,
            self.settings,
            self.check,
        ):
            widget.setEnabled(not busy)
        self.stop.setEnabled(busy)
        self.input.setReadOnly(busy)

    def set_sessions(self, sessions: list[dict], selected: int):
        self.sessions.clear()
        for session in sessions:
            self.sessions.addItem(f"{session['title']} · #{session['id']}", session["id"])
        self.sessions.setCurrentIndex(self.sessions.findData(selected))

    def show_messages(self, messages: list[dict]):
        # Plain text escaped into fixed markup; no model HTML, images, links or tools.
        fragments = []
        remaining = 100_000
        for message in reversed(messages):
            content = message["content"][:remaining]
            remaining -= len(content)
            name = "You" if message["role"] == "user" else self.name
            color = "#b8adc8" if message["role"] == "user" else "#d8bbff"
            fragments.append(
                f'<p style="color:{color}; margin-top:18px"><b>{html.escape(name)}</b></p><p style="white-space:pre-wrap">{html.escape(content)}</p>'
            )
            if remaining <= 0:
                fragments.append(
                    "<p>[Display limit reached. Use older messages to browse history.]</p>"
                )
                break
        self.transcript.setHtml(
            "".join(reversed(fragments))
            or "<p style='color:#aaa0b9'>Your conversation starts here. Try: Zdravo, Aiko!</p>"
        )
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)

    def closeEvent(self, event):
        self.hide()
        event.ignore()
