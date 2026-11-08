import logging
import sqlite3
import sys
from dataclasses import replace
from datetime import datetime
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from aiko.ai.conversation_service import build_context
from aiko.characters.profile import CharacterManager
from aiko.config import Settings, data_dir
from aiko.memory.database import Database
from aiko.ui.chat_window import STYLE, ChatWindow
from aiko.ui.mascot_window import MascotWindow
from aiko.ui.settings_dialog import SettingsDialog
from aiko.ui.worker import InferenceWorker

log = logging.getLogger(__name__)


class Controller(QObject):
    def __init__(self, app: QApplication, db: Database):
        super().__init__()
        self.app = app
        self.db = db
        self.profile = CharacterManager().current()
        self.chat = ChatWindow(self.profile.display_name)
        self.worker: InferenceWorker | None = None
        self.quitting = False
        self.page_before = None
        self.page_first = None
        try:
            self.settings = db.load_settings()
        except (ValueError, TypeError):
            self.settings = Settings()
            QMessageBox.warning(
                self.chat,
                "Invalid saved preferences",
                "Using safe defaults. Open Settings and Save to replace invalid preferences.",
            )
        sessions = db.sessions(self.profile.id)
        self.session_id = sessions[0]["id"] if sessions else db.new_session(self.profile.id)
        self.chat.send_requested.connect(self.send)
        self.chat.stop_requested.connect(self.stop)
        self.chat.check_requested.connect(self.check)
        self.chat.new_requested.connect(self.new_chat)
        self.chat.open_requested.connect(self.open_chat)
        self.chat.delete_requested.connect(self.delete_chat)
        self.chat.clear_requested.connect(self.clear_history)
        self.chat.settings_requested.connect(self.edit_settings)
        self.chat.quit_requested.connect(self.quit)
        self.chat.older_requested.connect(self.older)
        self.mascot = MascotWindow(self.profile, self.settings)
        self.mascot.toggle_chat.connect(self.toggle_chat)
        self.mascot.open_chat.connect(self.show_chat)
        self.mascot.settings_requested.connect(self.edit_settings)
        self.mascot.quit_requested.connect(self.quit)
        self.mascot.position_changed.connect(self.save_position)
        self.refresh()

    def show_chat(self):
        self.chat.showNormal()
        self.chat.raise_()
        self.chat.activateWindow()
        self.chat.input.setFocus()

    def toggle_chat(self):
        if self.chat.isVisible():
            self.chat.hide()
        else:
            self.show_chat()

    def save_position(self, x: int, y: int):
        self.settings = replace(self.settings, mascot_x=x, mascot_y=y)
        self.db.save_settings(self.settings)

    def refresh(self):
        self.chat.set_sessions(self.db.sessions(self.profile.id), self.session_id)
        rows = self.db.messages(self.session_id, 20, self.page_before)
        # Page by both count and size so every stored message remains accessible.
        size = 0
        visible = []
        for row in reversed(rows):
            if size + len(row["content"]) > 100_000:
                break
            visible.append(row)
            size += len(row["content"])
        rows = list(reversed(visible))
        self.page_first = rows[0]["id"] if rows else None
        has_older = bool(rows and self.db.messages(self.session_id, 1, self.page_first))
        self.chat.older.setText("Show older messages" if has_older else "Back to latest messages")
        self.chat.older.setEnabled(has_older or self.page_before is not None)
        self.chat.show_messages(rows)

    def older(self):
        if self.page_first and self.db.messages(self.session_id, 1, self.page_first):
            self.page_before = self.page_first
        else:
            self.page_before = None
        self.refresh()

    @Slot(str)
    def send(self, text: str):
        if self.worker or self.quitting:
            return
        try:
            messages = self.db.messages(self.session_id, 40)
            messages.append({"role": "user", "content": text})
            context = build_context(self.profile, messages, self.settings.context_size)
            self.db.add_message(self.session_id, "user", text)
        except (ValueError, sqlite3.Error) as exc:
            message = (
                str(exc)
                if isinstance(exc, ValueError)
                else "Cannot save your message. Check disk space and database access."
            )
            self.chat.status.setText(message)
            return
        self.chat.input.clear()
        self.page_before = None
        self.refresh()
        self.start_worker(context)

    def start_worker(self, messages):
        if self.worker or self.quitting:
            return
        self.chat.set_busy(True)
        self.mascot.character.set_state("thinking")
        self.chat.status.setText(
            "Thinking locally…" if messages is not None else "Checking local Ollama…"
        )
        self.worker = InferenceWorker(self.settings, messages, self)
        self.worker.result.connect(self.receive)
        self.worker.error.connect(self.failed)
        self.worker.cancelled.connect(self.cancelled)
        self.worker.finished.connect(self.finished)
        self.worker.start()

    @Slot(str)
    def receive(self, text):
        if self.quitting or not self.worker:
            return
        if self.worker.messages is None:
            self.chat.status.setText(text)
            return
        self.mascot.character.set_state("happy")
        try:
            self.db.add_message(self.session_id, "assistant", text)
            self.page_before = None
            self.refresh()
            received = datetime.now().strftime("%H:%M:%S")
            self.chat.status.setText(f"Reply received locally · last response {received}")
        except sqlite3.Error:
            self.chat.show_messages(
                [*self.db.messages(self.session_id, 19), {"role": "assistant", "content": text}]
            )
            self.chat.status.setText(
                "Reply shown but could not be saved. Copy it before closing; check disk space."
            )

    @Slot(str)
    def failed(self, message):
        self.chat.status.setText(message)

    @Slot()
    def cancelled(self):
        self.chat.status.setText(
            "Stopped. Your sent message remains in history; no partial answer was saved."
        )

    @Slot()
    def finished(self):
        worker = self.worker
        if worker:
            worker.wait()
            worker.deleteLater()
        self.worker = None
        self.chat.set_busy(False)
        if self.mascot.character.state == "thinking":
            self.mascot.character.set_state("idle")
        if self.quitting:
            self.finish_quit()

    @Slot()
    def stop(self):
        if self.worker:
            self.chat.status.setText("Stopping local request…")
            self.chat.stop.setEnabled(False)
            self.worker.cancel()

    @Slot()
    def check(self):
        self.start_worker(None)

    def new_chat(self):
        if self.worker:
            return
        self.session_id = self.db.new_session(self.profile.id)
        self.page_before = None
        self.refresh()
        self.chat.status.setText("New chat · earlier conversations remain in history")

    def open_chat(self, session_id):
        if not self.worker:
            self.session_id = session_id
            self.page_before = None
            self.refresh()

    def confirm(self, text):
        return (
            QMessageBox.question(
                self.chat,
                "Delete history?",
                text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def delete_chat(self):
        if not self.worker and self.confirm("Permanently delete this conversation from Aiko?"):
            self.db.delete_session(self.session_id)
            sessions = self.db.sessions(self.profile.id)
            if sessions:
                self.open_chat(sessions[0]["id"])
            else:
                self.new_chat()

    def clear_history(self):
        if not self.worker and self.confirm(
            "Permanently delete ALL conversations? Preferences will be kept."
        ):
            self.db.delete_all()
            self.new_chat()

    def edit_settings(self):
        if self.worker:
            return
        dialog = SettingsDialog(self.settings, self.chat)
        if dialog.exec():
            self.db.save_settings(dialog.value)
            self.settings = dialog.value
            self.mascot.apply_settings(self.settings)
            self.chat.status.setText("Settings saved · connection not checked with these settings")

    def quit(self):
        if self.quitting:
            return
        self.quitting = True
        if self.worker:
            self.chat.status.setText("Closing connection before exiting…")
            self.worker.cancel()
        else:
            self.finish_quit()

    def finish_quit(self):
        self.mascot.character.timer.stop()
        self.mascot.character.happy_timer.stop()
        self.mascot.hide()
        self.chat.hide()
        self.db.close()
        self.app.quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Aiko")
    app.setOrganizationName("Aiko")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLE)
    directory = data_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            directory / "aiko.log", maxBytes=200_000, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s level=%(levelname)s component=%(name)s %(message)s")
        )
        logging.getLogger("aiko").addHandler(handler)
        logging.getLogger("aiko").setLevel(logging.INFO)
        controller = Controller(app, Database(directory / "aiko.sqlite3"))
    except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
        QMessageBox.critical(
            None,
            "Aiko cannot start",
            f"Cannot load local data/profile ({type(exc).__name__}).\nStorage: {directory}\nCheck write access and the character JSON. Back up data before attempting repairs.",
        )
        return 1

    def report_error(exc_type, exc, traceback):
        log.error("ui_failed exception_type=%s", exc_type.__name__)
        QMessageBox.critical(
            controller.chat,
            "Aiko error",
            "A local operation failed. Check disk space and data access. Restart Aiko if the problem persists.",
        )

    sys.excepthook = report_error
    controller.mascot.show()
    QTimer.singleShot(100, controller.check)
    return app.exec()
