"""Conservative UTF-8 budget; not a model-specific tokenizer."""

from aiko.characters.profile import CharacterProfile


def build_context(profile: CharacterProfile, messages: list[dict], context_size: int) -> list[dict]:
    # One UTF-8 byte per estimated token is deliberately conservative, including Serbian/code.
    # Leave 768 output tokens and 256 tokens of chat-template overhead.
    system = {"role": "system", "content": profile.system_prompt}
    budget = context_size - 1024 - len(profile.system_prompt.encode("utf-8")) - 16
    selected = []
    for message in reversed(messages[-40:]):
        cost = len(message["content"].encode("utf-8")) + 16
        if cost > budget:
            if not selected:
                raise ValueError(
                    "This message is too long for the selected context. Shorten it or increase context in Settings."
                )
            break
        selected.append({"role": message["role"], "content": message["content"]})
        budget -= cost
    selected.reverse()
    while selected and selected[0]["role"] != "user":
        selected.pop(0)
    return [system, *selected]
