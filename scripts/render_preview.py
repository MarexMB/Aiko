"""Render real Qt widgets with clearly labeled sample text, without desktop capture."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from aiko.characters.profile import CharacterManager
from aiko.config import Settings
from aiko.ui.chat_window import STYLE, ChatWindow
from aiko.ui.mascot_window import MascotWindow

app = QApplication([])
# Windows' offscreen Qt backend does not always discover system fonts itself.
font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
for font_name in ("segoeui.ttf", "segoeuib.ttf", "seguisym.ttf"):
    font_file = font_dir / font_name
    if font_file.exists():
        QFontDatabase.addApplicationFont(str(font_file))
app.setStyleSheet(STYLE)
out = Path(__file__).resolve().parents[1] / "docs" / "images"
out.mkdir(parents=True, exist_ok=True)
chat = ChatWindow("Aiko")
chat.set_sessions([{"id": 1, "title": "A little curiosity"}], 1)
chat.older.setEnabled(False)
chat.status.setText("Preview · sample conversation, no inference performed")
chat.show_messages(
    [
        {"role": "user", "content": "Zdravo, Aiko! Učim Python. Odakle da počnem?"},
        {
            "role": "assistant",
            "content": "Zdravo! ✨ Hajde da počnemo malim koracima.\n\nPrvo upoznaj promenljive, uslove i petlje. Zatim napravi mali projekat — recimo listu zadataka.\n\nŽeliš da zajedno napišemo prvi primer?",
        },
        {"role": "user", "content": "Yes! Can we switch to English?"},
        {
            "role": "assistant",
            "content": 'Of course. Let\'s start with a tiny greeting:\n\nname = "Aiko"\nprint(f"Hello, {name}!")\n\nThe variable stores a name; the f-string places it inside the greeting. Try changing the name and running it again.',
        },
    ]
)
chat.show()
mascot = MascotWindow(CharacterManager().current(), Settings(reduced_motion=True))
mascot.show()
app.processEvents()
assert chat.grab().save(str(out / "chat-preview.png"))
assert mascot.grab().save(str(out / "mascot-preview.png"))
print("Rendered Qt widget previews in docs/images")
mascot.character.timer.stop()
