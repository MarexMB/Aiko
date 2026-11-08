import json

import pytest

from aiko.characters.profile import CharacterManager, CharacterProfile


def test_aiko_profile():
    p = CharacterManager().current()
    assert p.id == "aiko"
    assert "Serbian or English" in p.system_prompt
    assert p.animation["bounce_px"] <= 8


def test_profile_editing_is_independent_of_ai(tmp_path):
    p = CharacterManager().current()
    data = dict(p.__dict__)
    data["appearance"] = {**p.appearance, "hair": "#123456"}
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert CharacterManager(path).current().appearance["hair"] == "#123456"
    data["animation"] = {"bounce_px": 100, "blink_seconds": 4}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        CharacterProfile.load(path)
