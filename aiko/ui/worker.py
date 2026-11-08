import asyncio
import logging
import threading

from PySide6.QtCore import QThread, Signal

from aiko.ai.ollama_client import OllamaClient, OllamaError
from aiko.config import Settings

log = logging.getLogger(__name__)


class InferenceWorker(QThread):
    result = Signal(str)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, settings: Settings, messages: list[dict] | None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.messages = messages
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._loop = None
        self._task = None

    def cancel(self) -> None:
        self._stop.set()
        with self._lock:
            if self._loop is not None and self._task is not None:
                self._loop.call_soon_threadsafe(self._task.cancel)

    def run(self) -> None:
        async def perform():
            with self._lock:
                self._loop = asyncio.get_running_loop()
                self._task = asyncio.current_task()
            try:
                if self._stop.is_set():
                    raise asyncio.CancelledError
                client = OllamaClient(self.settings)
                result = (
                    await client.check()
                    if self.messages is None
                    else await client.chat(self.messages)
                )
                if self._stop.is_set():
                    raise asyncio.CancelledError
                self.result.emit(result)
            except asyncio.CancelledError:
                self.cancelled.emit()
            except OllamaError as exc:
                self.error.emit(str(exc))
            except Exception as exc:
                # No exception body, traceback or prompts in logs.
                log.error("worker_failed exception_type=%s", type(exc).__name__)
                self.error.emit(
                    "Unexpected inference failure. Check the local log and restart Aiko."
                )
            finally:
                with self._lock:
                    self._task = None
                    self._loop = None

        asyncio.run(perform())
