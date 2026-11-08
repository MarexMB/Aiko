import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aiko.app import Controller
from aiko.memory.database import Database
from aiko.ui.chat_window import ChatWindow


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def test_input_and_inert_transcript(app):
    chat = ChatWindow("Aiko")
    sent = []
    chat.send_requested.connect(sent.append)
    chat.input.setPlainText("Hello")
    QTest.keyClick(chat.input, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert "\n" in chat.input.toPlainText()
    QTest.keyClick(chat.input, Qt.Key.Key_Return)
    assert sent == ["Hello"]
    chat.set_busy(True)
    chat.submit()
    assert len(sent) == 1
    chat.show_messages([{"role": "assistant", "content": '<img src="http://example.com">'}])
    assert '<img src="http://example.com">' in chat.transcript.toPlainText()
    chat.deleteLater()


def test_controller_history_and_settings(app, tmp_path):
    db = Database(tmp_path / "test.sqlite3")
    controller = Controller(app, db)
    first = controller.session_id
    db.add_message(first, "user", "Zdravo")
    controller.new_chat()
    assert controller.session_id != first
    controller.open_chat(first)
    assert "Zdravo" in controller.chat.transcript.toPlainText()
    controller.chat.deleteLater()
    controller.mascot.deleteLater()
    db.close()


def test_mascot_bounds_motion_and_click(app):
    from PySide6.QtCore import QPoint, QRect, QSize

    from aiko.characters.profile import CharacterManager
    from aiko.config import Settings
    from aiko.ui.mascot_window import MascotWindow, clamp_position

    assert clamp_position(QPoint(9000, -500), QSize(200, 250), [QRect(0, 0, 1920, 1080)]) == QPoint(
        1720, 0
    )
    mascot = MascotWindow(CharacterManager().current(), Settings(reduced_motion=True))
    assert not mascot.character.timer.isActive()
    clicked = []
    mascot.toggle_chat.connect(lambda: clicked.append(True))
    QTest.mouseClick(mascot, Qt.MouseButton.LeftButton)
    assert clicked == [True]
    mascot.character.set_state("thinking")
    assert not mascot.grab().isNull()
    mascot.character.set_state("happy")
    assert not mascot.grab().isNull()
    mascot.deleteLater()
