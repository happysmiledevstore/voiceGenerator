"""
Text-to-Speech tab — light theme, icon buttons, voice profile support.

Layout:
  ┌──────────────────────────────────┐
  │  Text Input                      │
  │  Engine / Language options       │
  ├──────────────────────────────────┤
  │  Voice Profile row               │
  ├──────────────────────────────────┤
  │  [Generate Speech]  big button   │
  ├──────────────────────────────────┤
  │  Generated Waveform              │
  ├──────────────────────────────────┤
  │  Voice Effect Zone               │
  ├──────────────────────────────────┤
  │  [PlayOrig][Apply][ApplyProf][PlayProc][Save]   icon buttons
  ├──────────────────────────────────┤
  │  Preset buttons                  │
  └──────────────────────────────────┘
"""

import os
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QGroupBox,
    QCheckBox, QFileDialog, QMessageBox, QSizePolicy,
    QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.tts_engine import TTSEngine, LANGUAGES
from core.player import Player
from core.voice_changer import VoiceChanger, PRESETS
from core.voice_profile import load_profile, profile_to_transform_params
from core.icon_utils import get_icon, ACCENT_COLOR, DEFAULT_COLOR
from ui.effects_panel import EffectsPanel


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

class TTSWorker(QThread):
    finished = pyqtSignal(object, int)
    error    = pyqtSignal(str)

    def __init__(self, engine_name, text, language, slow, voice_id, rate):
        super().__init__()
        self._engine_name = engine_name
        self._text        = text
        self._language    = language
        self._slow        = slow
        self._voice_id    = voice_id
        self._rate        = rate

    def run(self):
        try:
            tts = TTSEngine()
            audio, sr = tts.synthesize(
                self._text, engine=self._engine_name, language=self._language,
                slow=self._slow, voice_id=self._voice_id, rate=self._rate,
            )
            self.finished.emit(audio, sr)
        except Exception as exc:
            self.error.emit(str(exc))


class TransformWorker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, audio, sr, params):
        super().__init__()
        self._audio  = audio
        self._sr     = sr
        self._params = params

    def run(self):
        try:
            result = VoiceChanger().transform(self._audio, self._sr, **self._params)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Waveform canvas — light theme
# ---------------------------------------------------------------------------

class WaveformCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self._fig = Figure(figsize=(6, 1.5), facecolor="#f5f5f5")
        super().__init__(self._fig)
        self.setParent(parent)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor("#f5f5f5")
        self._ax.axis("off")
        self._fig.tight_layout(pad=0.2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(110)

    def plot(self, audio: np.ndarray, sr: int, color: str = "#555555") -> None:
        self._ax.clear()
        self._ax.set_facecolor("#f5f5f5")
        self._ax.axis("off")
        if len(audio) == 0:
            self.draw()
            return
        t = np.linspace(0, len(audio) / sr, len(audio))
        if len(audio) > 10000:
            step = len(audio) // 10000
            t, audio = t[::step], audio[::step]
        self._ax.plot(t, audio, color=color, linewidth=0.7)
        self._ax.fill_between(t, audio, alpha=0.18, color=color)
        self._fig.tight_layout(pad=0.2)
        self.draw()

    def clear_plot(self) -> None:
        self._ax.clear()
        self._ax.set_facecolor("#f5f5f5")
        self._ax.axis("off")
        self.draw()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _icon_btn(icon_name: str, tooltip: str, obj_name: str = "IconBtn",
              color=DEFAULT_COLOR, icon_size: int = 26) -> QPushButton:
    btn = QPushButton()
    btn.setObjectName(obj_name)
    btn.setIcon(QIcon(get_icon(icon_name, size=icon_size, color=color)))
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


# ---------------------------------------------------------------------------
# TTS Tab
# ---------------------------------------------------------------------------

class TTSTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tts_engine       = TTSEngine()
        self._player           = Player()
        self._raw_audio:  np.ndarray | None = None
        self._proc_audio: np.ndarray | None = None
        self._sr               = 44100
        self._tts_worker:       TTSWorker       | None = None
        self._transform_worker: TransformWorker | None = None
        self._offline_voices:   list[dict]      = []
        self._loaded_profile:   dict            | None = None

        self._player.on_finished = self._on_playback_finished
        self._build_ui()
        self._load_offline_voices()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Text Input ────────────────────────────────────────────────
        text_group = QGroupBox("Text Input")
        text_lay   = QVBoxLayout(text_group)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText(
            "Type or paste the text you want to convert to speech...")
        self._text_edit.setFont(QFont("Segoe UI", 11))
        self._text_edit.setFixedHeight(110)
        text_lay.addWidget(self._text_edit)

        char_row = QHBoxLayout()
        self._char_label = QLabel("0 characters")
        self._char_label.setFont(QFont("Segoe UI", 8))
        self._char_label.setStyleSheet("color: #aaaaaa;")
        self._text_edit.textChanged.connect(self._on_text_changed)
        char_row.addWidget(self._char_label)
        char_row.addStretch()
        text_lay.addLayout(char_row)
        root.addWidget(text_group)

        # ── Engine + Language ─────────────────────────────────────────
        opts_group = QGroupBox("Engine & Language")
        opts_lay   = QHBoxLayout(opts_group)

        self._radio_gtts    = QRadioButton("gTTS (online)")
        self._radio_offline = QRadioButton("Offline (pyttsx3)")
        self._radio_gtts.setChecked(True)

        self._engine_grp = QButtonGroup()
        self._engine_grp.addButton(self._radio_gtts, 0)
        self._engine_grp.addButton(self._radio_offline, 1)
        self._engine_grp.buttonClicked.connect(self._on_engine_changed)

        opts_lay.addWidget(self._radio_gtts)
        opts_lay.addWidget(self._radio_offline)
        opts_lay.addSpacing(20)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(list(LANGUAGES.keys()))
        self._lang_combo.setCurrentText("English")
        self._lang_combo.setFixedWidth(140)
        opts_lay.addWidget(QLabel("Language:"))
        opts_lay.addWidget(self._lang_combo)
        opts_lay.addSpacing(16)

        self._slow_check = QCheckBox("Slow")
        opts_lay.addWidget(self._slow_check)

        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(160)
        self._voice_combo.setVisible(False)
        self._voice_lbl = QLabel("Voice:")
        self._voice_lbl.setVisible(False)
        opts_lay.addWidget(self._voice_lbl)
        opts_lay.addWidget(self._voice_combo)

        opts_lay.addStretch()
        root.addWidget(opts_group)

        # ── Voice Profile ─────────────────────────────────────────────
        profile_group = QGroupBox("Voice Profile")
        profile_lay   = QHBoxLayout(profile_group)

        self._btn_load_profile  = QPushButton("Load Voice Profile")
        self._btn_load_profile.setObjectName("ProfileBtn")
        self._btn_load_profile.setFixedHeight(34)
        self._btn_load_profile.setCursor(Qt.PointingHandCursor)
        self._btn_load_profile.clicked.connect(self._on_load_profile)

        self._btn_clear_profile = QPushButton("Clear")
        self._btn_clear_profile.setObjectName("ProfileBtn")
        self._btn_clear_profile.setFixedHeight(34)
        self._btn_clear_profile.setCursor(Qt.PointingHandCursor)
        self._btn_clear_profile.clicked.connect(self._on_clear_profile)
        self._btn_clear_profile.setEnabled(False)

        self._profile_label = QLabel("No profile loaded.")
        self._profile_label.setFont(QFont("Segoe UI", 9))
        self._profile_label.setStyleSheet("color: #888888;")

        profile_lay.addWidget(self._btn_load_profile)
        profile_lay.addWidget(self._btn_clear_profile)
        profile_lay.addSpacing(12)
        profile_lay.addWidget(self._profile_label)
        profile_lay.addStretch()
        root.addWidget(profile_group)

        # ── Generate button ───────────────────────────────────────────
        self._btn_generate = QPushButton("Generate Speech")
        self._btn_generate.setObjectName("GenerateBtn")
        self._btn_generate.setFixedHeight(44)
        self._btn_generate.setCursor(Qt.PointingHandCursor)
        self._btn_generate.clicked.connect(self._on_generate)
        root.addWidget(self._btn_generate)

        # ── Waveform ──────────────────────────────────────────────────
        wf_group = QGroupBox("Generated Waveform")
        wf_lay   = QVBoxLayout(wf_group)
        self._waveform = WaveformCanvas()
        wf_lay.addWidget(self._waveform)
        root.addWidget(wf_group)

        # ── Effects panel ─────────────────────────────────────────────
        self._effects = EffectsPanel()
        root.addWidget(self._effects)

        # ── Action icon buttons ───────────────────────────────────────
        action_group = QGroupBox("Playback & Export")
        action_lay   = QHBoxLayout(action_group)
        action_lay.setSpacing(10)

        self._btn_play_raw      = _icon_btn("play",       "Play Original",       "IconBtn")
        self._btn_apply         = _icon_btn("equalizer",  "Apply Effects",      "IconBtn")
        self._btn_apply_profile = _icon_btn("microphone", "Apply Voice Profile", "IconBtn")
        self._btn_play_proc     = _icon_btn("step_fwd",   "Play Processed",     "IconBtn")
        self._btn_save          = _icon_btn("download",   "Save Audio",         "IconBtn")

        self._btn_apply_profile.setEnabled(False)

        self._btn_play_raw.clicked.connect(self._play_raw)
        self._btn_apply.clicked.connect(self._apply_effects)
        self._btn_apply_profile.clicked.connect(self._apply_voice_profile)
        self._btn_play_proc.clicked.connect(self._play_processed)
        self._btn_save.clicked.connect(self._save_file)

        for btn in (self._btn_play_raw, self._btn_apply, self._btn_apply_profile,
                    self._btn_play_proc, self._btn_save):
            action_lay.addWidget(btn)
        action_lay.addStretch()
        root.addWidget(action_group)

        # ── Preset buttons ────────────────────────────────────────────
        preset_group = QGroupBox("Presets")
        preset_lay   = QHBoxLayout(preset_group)
        preset_lay.setSpacing(8)

        for name in PRESETS:
            btn = QPushButton(name)
            btn.setObjectName("PresetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            preset_lay.addWidget(btn)

        root.addWidget(preset_group)

        # ── Status ────────────────────────────────────────────────────
        self._status = QLabel("Enter text and click Generate Speech.")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setFont(QFont("Segoe UI", 9))
        self._status.setStyleSheet("color: #888888; padding: 4px;")
        root.addWidget(self._status)

    # ------------------------------------------------------------------
    # Engine toggle
    # ------------------------------------------------------------------

    def _on_engine_changed(self) -> None:
        gtts = self._radio_gtts.isChecked()
        self._lang_combo.setVisible(gtts)
        self._slow_check.setVisible(gtts)
        self._voice_combo.setVisible(not gtts)
        self._voice_lbl.setVisible(not gtts)

    def _on_text_changed(self) -> None:
        n = len(self._text_edit.toPlainText())
        self._char_label.setText(f"{n} character{'s' if n != 1 else ''}")

    def _load_offline_voices(self) -> None:
        try:
            voices = self._tts_engine.get_offline_voices()
            for v in voices:
                self._voice_combo.addItem(v["name"], v["id"])
        except Exception:
            self._voice_combo.addItem("Default voice", None)

    # ------------------------------------------------------------------
    # Voice Profile
    # ------------------------------------------------------------------

    def _on_load_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Voice Profile", "",
            "Voice Profile (*.vgprofile);;All Files (*)"
        )
        if not path:
            return
        try:
            profile = load_profile(path)
            self._loaded_profile = profile
            name  = profile.get("name", os.path.basename(path))
            pitch = profile.get("pitch_mean", 0)
            shift = profile.get("semitone_shift", 0)
            self._profile_label.setText(
                f"{name}  |  Pitch: {pitch:.0f} Hz  |  Shift: {shift:+.1f} st")
            self._profile_label.setStyleSheet("color: #111111; font-weight: bold;")
            self._btn_clear_profile.setEnabled(True)
            self._btn_apply_profile.setEnabled(True)
            self._set_status(f"Voice profile loaded: {name}")
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", str(exc))

    def _on_clear_profile(self) -> None:
        self._loaded_profile = None
        self._profile_label.setText("No profile loaded.")
        self._profile_label.setStyleSheet("color: #888888;")
        self._btn_clear_profile.setEnabled(False)
        self._btn_apply_profile.setEnabled(False)

    def _apply_voice_profile(self) -> None:
        if self._raw_audio is None:
            QMessageBox.warning(self, "No Audio", "Generate speech first.")
            return
        if self._loaded_profile is None:
            QMessageBox.warning(self, "No Profile", "Load a voice profile first.")
            return
        params = profile_to_transform_params(self._loaded_profile)
        self._set_status("Applying voice profile...")
        self._transform_worker = TransformWorker(self._raw_audio, self._sr, params)
        self._transform_worker.finished.connect(self._on_transform_done)
        self._transform_worker.error.connect(self._on_transform_error)
        self._transform_worker.start()

    # ------------------------------------------------------------------
    # TTS generation
    # ------------------------------------------------------------------

    def _on_generate(self) -> None:
        text = self._text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty Text", "Please type some text first.")
            return
        self._btn_generate.setEnabled(False)
        self._set_status("Generating speech...")
        self._waveform.clear_plot()

        engine   = "gtts" if self._radio_gtts.isChecked() else "offline"
        language = self._lang_combo.currentText()
        slow     = self._slow_check.isChecked()
        voice_id = self._voice_combo.currentData()

        self._tts_worker = TTSWorker(engine, text, language, slow, voice_id, 175)
        self._tts_worker.finished.connect(self._on_tts_done)
        self._tts_worker.error.connect(self._on_tts_error)
        self._tts_worker.start()

    @pyqtSlot(object, int)
    def _on_tts_done(self, audio: np.ndarray, sr: int) -> None:
        self._raw_audio  = audio
        self._proc_audio = None
        self._sr         = sr
        self._waveform.plot(audio, sr)
        self._btn_generate.setEnabled(True)
        self._set_status(f"Generated {len(audio)/sr:.1f}s — apply effects or play.")

    @pyqtSlot(str)
    def _on_tts_error(self, msg: str) -> None:
        self._btn_generate.setEnabled(True)
        QMessageBox.critical(self, "TTS Error", msg)
        self._set_status("TTS generation failed.")

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def _apply_effects(self) -> None:
        if self._raw_audio is None:
            QMessageBox.warning(self, "No Audio", "Generate speech first.")
            return
        params = self._effects.get_params()
        self._set_status("Applying effects...")
        self._transform_worker = TransformWorker(self._raw_audio, self._sr, params)
        self._transform_worker.finished.connect(self._on_transform_done)
        self._transform_worker.error.connect(self._on_transform_error)
        self._transform_worker.start()

    def _apply_preset(self, name: str) -> None:
        self._effects.apply_preset_by_name(name)

    @pyqtSlot(object)
    def _on_transform_done(self, result: np.ndarray) -> None:
        self._proc_audio = result
        self._waveform.plot(result, self._sr, color="#333333")
        self._set_status("Applied — ready to play or save.")

    @pyqtSlot(str)
    def _on_transform_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Transform Error", msg)
        self._set_status("Error applying effects.")

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _play_raw(self) -> None:
        if self._raw_audio is None:
            QMessageBox.warning(self, "No Audio", "Generate speech first.")
            return
        self._player.play(self._raw_audio, self._sr)
        self._set_status("Playing original...")

    def _play_processed(self) -> None:
        audio = self._proc_audio if self._proc_audio is not None else self._raw_audio
        if audio is None:
            QMessageBox.warning(self, "No Audio", "Generate speech first.")
            return
        self._player.play(audio, self._sr)
        self._set_status("Playing processed...")

    def _on_playback_finished(self) -> None:
        self._set_status("Playback finished.")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save_file(self) -> None:
        audio = self._proc_audio if self._proc_audio is not None else self._raw_audio
        if audio is None:
            QMessageBox.warning(self, "No Audio", "Nothing to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Audio", "speech_output.wav",
            "WAV Files (*.wav);;MP3 Files (*.mp3)"
        )
        if not path:
            return
        try:
            VoiceChanger().export(path, audio, self._sr)
            self._set_status(f"Saved: {os.path.basename(path)}")
        except RuntimeError as exc:
            QMessageBox.warning(self, "Save Warning", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    # ------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        self._status.setText(msg)
        self.status_message.emit(msg)
