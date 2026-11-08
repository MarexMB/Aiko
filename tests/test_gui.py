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


def wait_until(app, predicate, timeout=3000):
    import time

    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert predicate()


def test_async_response_and_stop(app, tmp_path, monkeypatch):
    import asyncio

    from aiko.ai.ollama_client import OllamaClient

    async def delayed_reply(self, messages):
        await asyncio.sleep(0.1)
        return "Zdravo!"

    monkeypatch.setattr(OllamaClient, "chat", delayed_reply)
    db = Database(tmp_path / "async.sqlite3")
    controller = Controller(app, db)
    controller.send("Hi")
    assert controller.worker is not None
    assert not controller.chat.send.isEnabled()
    controller.send("duplicate")
    assert len(db.messages(controller.session_id)) == 1
    wait_until(app, lambda: controller.worker is None)
    assert db.messages(controller.session_id)[-1]["content"] == "Zdravo!"
    assert controller.mascot.character.state == "happy"

    async def stall(self, messages):
        await asyncio.sleep(60)
        return "must not save"

    monkeypatch.setattr(OllamaClient, "chat", stall)
    controller.send("Cancel this")
    QTest.qWait(50)
    controller.stop()
    wait_until(app, lambda: controller.worker is None)
    assert len(db.messages(controller.session_id)) == 3
    assert "Stopped" in controller.chat.status.text()
    assert controller.mascot.character.state == "idle"
    controller.send("Exit during generation")
    controller.quit()
    wait_until(app, lambda: controller.worker is None)
    assert not controller.mascot.character.timer.isActive()
    controller.chat.deleteLater()
    controller.mascot.deleteLater()
