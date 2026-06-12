"""
Shared effects control panel — used by both RecorderTab and TTSTab.
Light-theme compatible. Emits params_changed signal on any change.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QGroupBox, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.voice_changer import PRESETS


# ---------------------------------------------------------------------------
# Labeled slider widget
# ---------------------------------------------------------------------------

class LabeledSlider(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, label: str, minimum: float, maximum: float,
                 default: float, step: float = 0.1, fmt: str = "{:.1f}", parent=None):
        super().__init__(parent)
        self._min  = minimum
        self._max  = maximum
        self._step = step
        self._fmt  = fmt

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title = QLabel(label)
        title.setFont(QFont("Segoe UI", 9))
        title.setStyleSheet("color: #333333; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        row = QHBoxLayout()
        self._int_range = int((maximum - minimum) / step)
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, self._int_range)
        self._slider.setValue(self._to_int(default))
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.setTickInterval(max(1, self._int_range // 8))

        self._val_label = QLabel(fmt.format(default))
        self._val_label.setFixedWidth(46)
        self._val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._val_label.setFont(QFont("Consolas", 9))
        self._val_label.setStyleSheet("color: #111111; font-weight: bold;")

        row.addWidget(self._slider)
        row.addWidget(self._val_label)
        layout.addLayout(row)

        self._slider.valueChanged.connect(self._on_change)

    def _to_int(self, val: float) -> int:
        return int(round((val - self._min) / self._step))

    def _to_float(self, i: int) -> float:
        return round(self._min + i * self._step, 6)

    def _on_change(self, i: int) -> None:
        v = self._to_float(i)
        self._val_label.setText(self._fmt.format(v))
        self.valueChanged.emit(v)

    def value(self) -> float:
        return self._to_float(self._slider.value())

    def setValue(self, val: float) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(self._to_int(val))
        self._val_label.setText(self._fmt.format(val))
        self._slider.blockSignals(False)


# ---------------------------------------------------------------------------
# Effects panel
# ---------------------------------------------------------------------------

class EffectsPanel(QGroupBox):
    """
    Shared effects group box.
    Consumers call `.get_params()` and `.apply_preset_by_name(name)`.
    """

    params_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Voice Effect Zone", parent)
        self._effect: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 14, 12, 12)

        # ── Sliders ───────────────────────────────────────────────────
        self._pitch_slider = LabeledSlider(
            "Pitch (semitones)", -12.0, 12.0, 0.0, step=0.5, fmt="{:+.1f}"
        )
        self._speed_slider = LabeledSlider(
            "Speed", 0.5, 2.0, 1.0, step=0.05, fmt="{:.2f}x"
        )

        self._pitch_slider.valueChanged.connect(lambda _: self.params_changed.emit())
        self._speed_slider.valueChanged.connect(lambda _: self.params_changed.emit())

        root.addWidget(self._pitch_slider)
        root.addWidget(self._speed_slider)

        # ── Effect selector ───────────────────────────────────────────
        effect_row = QHBoxLayout()
        effect_lbl = QLabel("Effect:")
        effect_lbl.setFont(QFont("Segoe UI", 9))
        effect_lbl.setStyleSheet("color: #333333;")
        self._effect_combo = QComboBox()
        self._effect_combo.addItems(["None", "Robot", "Echo", "Reverb", "Alien"])
        self._effect_combo.currentTextChanged.connect(self._on_effect_change)

        effect_row.addWidget(effect_lbl)
        effect_row.addWidget(self._effect_combo, 1)
        root.addLayout(effect_row)

    # ------------------------------------------------------------------

    def _on_effect_change(self, text: str) -> None:
        self._effect = None if text == "None" else text.lower()
        self.params_changed.emit()

    def get_params(self) -> dict:
        return {
            "pitch_semitones": self._pitch_slider.value(),
            "speed_rate":      self._speed_slider.value(),
            "effect":          self._effect,
        }

    def apply_preset_by_name(self, name: str) -> None:
        p = PRESETS.get(name, PRESETS["Normal"])
        self._pitch_slider.setValue(p["pitch"])
        self._speed_slider.setValue(p["speed"])

        effect_text = "None" if p["effect"] is None else p["effect"].capitalize()
        idx = self._effect_combo.findText(effect_text)
        if idx >= 0:
            self._effect_combo.setCurrentIndex(idx)

        self.params_changed.emit()

    def reset(self) -> None:
        self.apply_preset_by_name("Normal")
