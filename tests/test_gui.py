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
    db.close()
