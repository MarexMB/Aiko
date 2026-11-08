"""Validated preferences. Chat data never belongs in this configuration."""

import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit


def data_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Aiko"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "aiko"


@dataclass(frozen=True)
class Settings:
    model: str = "qwen3:8b"
    ollama_url: str = "http://127.0.0.1:11434"
    context_size: int = 4096
    always_on_top: bool = True
    reduced_motion: bool = False
    mascot_x: int | None = None
    mascot_y: int | None = None

    def validate(self) -> "Settings":
        if not isinstance(self.model, str) or not re.fullmatch(r"[\w./:-]{1,120}", self.model):
            raise ValueError("Use a model name such as qwen3:8b (no spaces).")
        if "cloud" in self.model.lower():
            raise ValueError("Cloud model names are disabled. Choose an installed local model.")
        # Numeric loopback addresses avoid DNS resolution and remote/cloud endpoints.
        try:
            url = urlsplit(self.ollama_url)
            valid = (
                url.scheme == "http"
                and url.hostname in {"127.0.0.1", "::1"}
                and not url.username
                and not url.password
                and url.path in {"", "/"}
                and not url.query
                and not url.fragment
                and (url.port or 11434) > 0
            )
        except (ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise ValueError("Use a local HTTP URL, e.g. http://127.0.0.1:11434.")
        if type(self.context_size) is not int or not 2048 <= self.context_size <= 16384:
            raise ValueError("Context size must be an integer from 2048 to 16384.")
        if type(self.always_on_top) is not bool or type(self.reduced_motion) is not bool:
            raise ValueError("Animation and window preferences must be true or false.")
        for value in (self.mascot_x, self.mascot_y):
            if value is not None and (type(value) is not int or abs(value) > 1_000_000):
                raise ValueError("Invalid saved mascot position.")
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict) -> "Settings":
        if not isinstance(values, dict):
            raise ValueError("Settings must be a JSON object.")
        if set(values) - set(cls.__dataclass_fields__):
            raise ValueError("Unknown settings keys.")
        return cls(**values).validate()
