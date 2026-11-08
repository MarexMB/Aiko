import json
from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from aiko.config import Settings, data_dir


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aiko · Settings")
        self.setMinimumWidth(440)
        self.original = settings
        self.value = settings
        form = QFormLayout(self)
        self.model = QLineEdit(settings.model)
        self.url = QLineEdit(settings.ollama_url)
        self.context = QSpinBox()
        self.context.setRange(2048, 16384)
        self.context.setSingleStep(512)
        self.context.setValue(settings.context_size)
        self.top = QCheckBox("Keep mascot above other windows")
        self.top.setChecked(settings.always_on_top)
        self.motion = QCheckBox("Disable autonomous movement and blinking")
        self.motion.setChecked(settings.reduced_motion)
        for name, widget in (
            ("Model", self.model),
            ("Local Ollama URL", self.url),
            ("Context tokens", self.context),
            ("", self.top),
            ("Reduced motion", self.motion),
        ):
            form.addRow(name, widget)
        note = QLabel(
            "4096 is the default; higher contexts use more memory.\nOnly numeric loopback HTTP addresses are allowed.\nHistory is stored locally, without automatic fact extraction.\n\nStorage: "
            + str(data_dir() / "aiko.sqlite3")
        )
        note.setWordWrap(True)
        form.addRow(note)
        export = QPushButton("Export settings JSON…")
        export.clicked.connect(self.export_settings)
        load = QPushButton("Import settings JSON…")
        load.clicked.connect(self.import_settings)
        form.addRow(export, load)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def collect(self) -> Settings:
        return replace(
            self.original,
            model=self.model.text().strip(),
            ollama_url=self.url.text().strip(),
            context_size=self.context.value(),
            always_on_top=self.top.isChecked(),
            reduced_motion=self.motion.isChecked(),
        ).validate()

    def save(self):
        try:
            self.value = self.collect()
            self.accept()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid settings", str(exc))

    def export_settings(self):
        try:
            settings = self.collect()
            path, _ = QFileDialog.getSaveFileName(
                self, "Export preferences", "aiko-settings.json", "JSON (*.json)"
            )
            if path:
                from pathlib import Path

                Path(path).write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Cannot export", str(exc))

    def import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import preferences", "", "JSON (*.json)")
        if not path:
            return
        try:
            from pathlib import Path

            settings = Settings.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
            self.model.setText(settings.model)
            self.url.setText(settings.ollama_url)
            self.context.setValue(settings.context_size)
            self.top.setChecked(settings.always_on_top)
            self.motion.setChecked(settings.reduced_motion)
        except (ValueError, TypeError, OSError) as exc:
            QMessageBox.warning(self, "Cannot import", str(exc))
