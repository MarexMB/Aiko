import sqlite3

import pytest

from aiko.config import Settings
from aiko.memory.database import Database


def test_persistence_and_parameterized_text(tmp_path):
    path = tmp_path / "chat.sqlite3"
    db = Database(path)
    sid = db.new_session("aiko")
    text = "'); DROP TABLE sessions; -- Zdravo!"
    db.add_message(sid, "user", text)
    db.save_settings(Settings(reduced_motion=True))
    db.close()
    db = Database(path)
    assert db.messages(sid)[0]["content"] == text
    assert db.load_settings().reduced_motion
    assert len(db.sessions("aiko")) == 1
    db.delete_session(sid)
    assert db.messages(sid) == []
    assert db.load_settings().reduced_motion
    db.close()


def test_pagination_and_delete_all(tmp_path):
    db = Database(tmp_path / "chat.sqlite3")
    sid = db.new_session("aiko")
    for i in range(6):
        db.add_message(sid, "user", str(i))
    page = db.messages(sid, 2)
    assert [m["content"] for m in page] == ["4", "5"]
    assert [m["content"] for m in db.messages(sid, 2, page[0]["id"])] == ["2", "3"]
    with pytest.raises(sqlite3.IntegrityError):
        db.add_message(999, "user", "orphan")
    db.delete_all()
    assert db.sessions("aiko") == []
    assert db.messages(sid) == []
    db.close()
