import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CharacterProfile:
    id: str
    display_name: str
    description: str
    system_prompt: str
    appearance: dict[str, str]
    animation: dict[str, float]

    @classmethod
    def load(cls, path: Path) -> "CharacterProfile":
        profile = cls(**json.loads(path.read_text(encoding="utf-8")))
        for value in (profile.id, profile.display_name, profile.description, profile.system_prompt):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Character text fields must be nonempty strings.")
        if not re.fullmatch(r"[a-z0-9_-]+", profile.id):
            raise ValueError("Character ID must be a stable lowercase identifier.")
        for key in ("hair", "eyes", "accent", "dress", "skin"):
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", profile.appearance.get(key, "")):
                raise ValueError(f"Invalid character color: {key}")
        for key, low, high in (("bounce_px", 0, 8), ("blink_seconds", 2, 12)):
            value = profile.animation.get(key)
            if type(value) not in (float, int) or not low <= value <= high:
                raise ValueError(f"Invalid animation setting: {key}")
        return profile


class CharacterManager:
    """One bundled character; renderers consume its profile, never the AI client."""

    def __init__(self, profile_path: Path | None = None):
        self.profile = CharacterProfile.load(profile_path or Path(__file__).with_name("aiko.json"))

    def current(self) -> CharacterProfile:
        return self.profile
