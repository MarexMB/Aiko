import pytest

from aiko.config import Settings


def test_defaults_roundtrip():
    assert Settings.from_dict(Settings().to_dict()) == Settings()


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://localhost:11434",
        "http://127.0.0.1.evil",
        "http://127.0.0.1:11434/api",
        "http://user@127.0.0.1",
        "http://127.0.0.1:99999",
    ],
)
def test_remote_or_invalid_url_rejected(url):
    with pytest.raises(ValueError):
        Settings(ollama_url=url).validate()


@pytest.mark.parametrize(
    "changes",
    [
        {"context_size": True},
        {"context_size": 100},
        {"model": "bad name"},
        {"reduced_motion": "false"},
        {"mascot_x": 1.5},
        {"unknown": 1},
    ],
)
def test_invalid_preferences(changes):
    with pytest.raises(ValueError):
        Settings.from_dict(changes)
