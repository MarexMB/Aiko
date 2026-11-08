# Original mascot artwork

Aiko v0.1 is drawn from geometric paths by `aiko/ui/mascot_widget.py`.
The artwork is original to this project and distributed under the repository's MIT license.
No downloaded character art, fonts, Live2D assets, or proprietary Capri assets are used.
Qt uses the system font. PySide6/Qt and httpx retain their respective upstream licenses.

Renderer boundary: accept a `CharacterProfile`, implement `set_state("idle" | "thinking" | "happy")`
and `set_reduced_motion(bool)`. The desktop window handles input/placement; the renderer
does not access Ollama, SQLite, files, or the desktop. Future renderers can replace it here.
