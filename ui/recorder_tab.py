"""
Voice Recorder / Changer tab.

Layout (matches wireframe):
  ┌─────────────────────────────────┐
  │  Waveform                       │
  ├─────────────────────────────────┤
  │  [Rec] [Pause] [Stop] [Upload] [Save]   icon buttons
  ├─────────────────────────────────┤
  │  Voice Effect Zone (sliders + effect combo)
  ├─────────────────────────────────┤
  │  [Play Orig] [Apply] [Play Proc]   playback row
  ├─────────────────────────────────┤
  │  Preset buttons (Normal / Deep / Chipmunk / Robot / Echo / Reverb / Alien)
  ├─────────────────────────────────┤
  │  Voice Profile section          │
  └─────────────────────────────────┘
"""

import os
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QSizePolicy,
    QGroupBox, QInputDialog, QFrame, QToolTip,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.recorder import Recorder, load_audio_file, SAMPLE_RATE
from core.player import Player
from core.voice_changer import VoiceChanger, PRESETS
from core.voice_profile import analyse_voice, save_profile
from core.icon_utils import get_icon, ACCENT_COLOR, DANGER_COLOR, DEFAULT_COLOR
from ui.effects_panel import EffectsPanel


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------

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


class ProfileWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, audio, sr):
        super().__init__()
        self._audio = audio
        self._sr    = sr

    def run(self):
        try:
            self.finished.emit(analyse_voice(self._audio, self._sr))
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Waveform canvas — light theme
# ---------------------------------------------------------------------------

class WaveformCanvas(FigureCanvas):
    def __init__(self, height_px: int = 130, parent=None):
        self._fig = Figure(figsize=(6, 1.8), facecolor="#f5f5f5")
        super().__init__(self._fig)
        self.setParent(parent)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor("#f5f5f5")
        self._ax.axis("off")
        self._fig.tight_layout(pad=0.2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(height_px)

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
# Icon push button helper
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
# Recorder Tab
# ---------------------------------------------------------------------------

class RecorderTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recorder    = Recorder()
        self._player      = Player()
        self._raw_audio:  np.ndarray | None = None
        self._proc_audio: np.ndarray | None = None
        self._sr          = SAMPLE_RATE
        self._worker:          TransformWorker | None = None
        self._profile_worker:  ProfileWorker  | None = None
        self._live_chunks: list[np.ndarray]   = []

        self._timer = QTimer()
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._refresh_live_waveform)

        self._player.on_finished = self._on_playback_finished
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Waveform ──────────────────────────────────────────────────
        wf_box = QGroupBox("Waveform")
        wf_lay = QVBoxLayout(wf_box)
        self._waveform = WaveformCanvas(height_px=140)
        wf_lay.addWidget(self._waveform)

        self._dur_label = QLabel("Duration: —")
        self._dur_label.setAlignment(Qt.AlignRight)
        self._dur_label.setFont(QFont("Segoe UI", 8))
        self._dur_label.setStyleSheet("color: #888888;")
        wf_lay.addWidget(self._dur_label)
        root.addWidget(wf_box)

        # ── Transport icon buttons ────────────────────────────────────
        transport_group = QGroupBox("Record & Load")
        transport_lay = QHBoxLayout(transport_group)
        transport_lay.setSpacing(10)

        self._btn_record = _icon_btn("record",   "Record",         "RecordBtn")
        self._btn_pause  = _icon_btn("pause",    "Pause / Resume", "IconBtn")
        self._btn_stop   = _icon_btn("stop",     "Stop",           "IconBtn")
        self._btn_upload = _icon_btn("upload",   "Upload File",    "IconBtn")
        self._btn_save   = _icon_btn("download", "Save Audio",     "IconBtn")

        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)

        self._btn_record.clicked.connect(self._on_record)
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_upload.clicked.connect(self._on_upload)
        self._btn_save.clicked.connect(self._save_file)

        for btn in (self._btn_record, self._btn_pause, self._btn_stop,
                    self._btn_upload, self._btn_save):
            transport_lay.addWidget(btn)

        transport_lay.addStretch()
        root.addWidget(transport_group)

        # ── Voice Effect Zone ─────────────────────────────────────────
        self._effects = EffectsPanel()
        root.addWidget(self._effects)

        # ── Playback row ──────────────────────────────────────────────
        pb_group = QGroupBox("Playback")
        pb_lay = QHBoxLayout(pb_group)
        pb_lay.setSpacing(10)

        self._btn_play_raw  = _icon_btn("play",      "Play Original",  "IconBtn")
        self._btn_apply     = _icon_btn("equalizer", "Apply Effects",  "IconBtn")
        self._btn_play_proc = _icon_btn("step_fwd",  "Play Processed", "IconBtn")

        self._btn_play_raw.clicked.connect(self._play_raw)
        self._btn_apply.clicked.connect(self._apply_effects)
        self._btn_play_proc.clicked.connect(self._play_processed)

        for btn in (self._btn_play_raw, self._btn_apply, self._btn_play_proc):
            pb_lay.addWidget(btn)
        pb_lay.addStretch()
        root.addWidget(pb_group)

        # ── Preset buttons ────────────────────────────────────────────
        preset_group = QGroupBox("Presets")
        preset_lay = QHBoxLayout(preset_group)
        preset_lay.setSpacing(8)

        for name in PRESETS:
            btn = QPushButton(name)
            btn.setObjectName("PresetBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._apply_preset(n))
            preset_lay.addWidget(btn)

        root.addWidget(preset_group)

        # ── Voice Profile ─────────────────────────────────────────────
        profile_group = QGroupBox("Voice Profile")
        profile_lay = QVBoxLayout(profile_group)

        profile_info = QLabel(
            "Record your voice, then save a profile so the Text-to-Speech tab "
            "can generate speech that matches your voice pitch."
        )
        profile_info.setFont(QFont("Segoe UI", 9))
        profile_info.setWordWrap(True)
        profile_info.setStyleSheet("color: #888888;")
        profile_lay.addWidget(profile_info)

        prof_btn_row = QHBoxLayout()
        self._btn_save_profile = QPushButton("Analyse & Save Voice Profile")
        self._btn_save_profile.setObjectName("ProfileBtn")
        self._btn_save_profile.setFixedHeight(34)
        self._btn_save_profile.setCursor(Qt.PointingHandCursor)
        self._btn_save_profile.clicked.connect(self._on_save_profile)
        prof_btn_row.addWidget(self._btn_save_profile)
        prof_btn_row.addStretch()
        profile_lay.addLayout(prof_btn_row)

        self._profile_status = QLabel("")
        self._profile_status.setFont(QFont("Segoe UI", 8))
        self._profile_status.setStyleSheet("color: #888888;")
        profile_lay.addWidget(self._profile_status)

        root.addWidget(profile_group)

        # ── Status ────────────────────────────────────────────────────
        self._status = QLabel("Ready — record or upload an audio file.")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setFont(QFont("Segoe UI", 9))
        self._status.setStyleSheet("color: #888888; padding: 4px;")
        root.addWidget(self._status)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _on_record(self) -> None:
        if self._recorder.is_recording:
            return
        self._raw_audio = None
        self._proc_audio = None
        self._live_chunks = []
        self._waveform.clear_plot()
        self._recorder.on_chunk = self._on_audio_chunk
        self._recorder.start()
        self._timer.start()

        self._btn_record.setProperty("recording", "true")
        self._btn_record.style().unpolish(self._btn_record)
        self._btn_record.style().polish(self._btn_record)
        self._btn_record.setEnabled(False)
        self._btn_pause.setEnabled(True)
        self._btn_stop.setEnabled(True)
        self._set_status("Recording...")

    def _on_audio_chunk(self, chunk: np.ndarray) -> None:
        self._live_chunks.append(chunk)

    def _refresh_live_waveform(self) -> None:
        if self._live_chunks:
            audio = np.concatenate(self._live_chunks)
            self._waveform.plot(audio, self._sr, color="#555555")
            self._dur_label.setText(f"Duration: {len(audio)/self._sr:.1f}s")

    def _on_pause(self) -> None:
        if self._recorder.is_paused:
            self._recorder.resume()
            self._btn_pause.setIcon(QIcon(get_icon("pause")))
            self._btn_pause.setToolTip("Pause")
            self._timer.start()
        else:
            self._recorder.pause()
            self._btn_pause.setIcon(QIcon(get_icon("play")))
            self._btn_pause.setToolTip("Resume")
            self._timer.stop()

    def _on_stop(self) -> None:
        self._timer.stop()
        self._raw_audio = self._recorder.stop()
        self._sr = SAMPLE_RATE

        self._btn_record.setProperty("recording", "false")
        self._btn_record.style().unpolish(self._btn_record)
        self._btn_record.style().polish(self._btn_record)
        self._btn_record.setEnabled(True)
        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)
        self._btn_pause.setIcon(QIcon(get_icon("pause")))
        self._btn_pause.setToolTip("Pause")

        if len(self._raw_audio) < 100:
            self._set_status("Nothing recorded.")
            return

        self._waveform.plot(self._raw_audio, self._sr)
        self._dur_label.setText(f"Duration: {len(self._raw_audio)/self._sr:.1f}s")
        self._set_status(f"Recorded {len(self._raw_audio)/self._sr:.1f}s.")

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def _on_upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac);;All Files (*)"
        )
        if not path:
            return
        try:
            self._set_status("Loading...")
            audio, sr = load_audio_file(path, target_sr=SAMPLE_RATE)
            self._raw_audio  = audio
            self._sr         = sr
            self._proc_audio = None
            self._waveform.plot(audio, sr)
            self._dur_label.setText(f"Duration: {len(audio)/sr:.1f}s")
            self._set_status(f"Loaded: {os.path.basename(path)}")
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", str(exc))
            self._set_status("Failed to load file.")

    # ------------------------------------------------------------------
    # Effects & presets
    # ------------------------------------------------------------------

    def _apply_effects(self) -> None:
        if self._raw_audio is None or len(self._raw_audio) == 0:
            QMessageBox.warning(self, "No Audio", "Record or upload audio first.")
            return
        params = self._effects.get_params()
        self._set_status("Applying effects...")
        self._worker = TransformWorker(self._raw_audio, self._sr, params)
        self._worker.finished.connect(self._on_transform_done)
        self._worker.error.connect(self._on_transform_error)
        self._worker.start()

    def _apply_preset(self, name: str) -> None:
        self._effects.apply_preset_by_name(name)

    @pyqtSlot(object)
    def _on_transform_done(self, result: np.ndarray) -> None:
        self._proc_audio = result
        self._waveform.plot(result, self._sr, color="#333333")
        self._set_status("Effects applied — ready to play or save.")

    @pyqtSlot(str)
    def _on_transform_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Transform Error", msg)
        self._set_status("Error applying effects.")

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _play_raw(self) -> None:
        if self._raw_audio is None:
            QMessageBox.warning(self, "No Audio", "Record or upload audio first.")
            return
        self._player.play(self._raw_audio, self._sr)
        self._set_status("Playing original...")

    def _play_processed(self) -> None:
        audio = self._proc_audio if self._proc_audio is not None else self._raw_audio
        if audio is None:
            QMessageBox.warning(self, "No Audio", "Apply effects first.")
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
            self, "Save Audio", "output.wav",
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
    # Voice Profile
    # ------------------------------------------------------------------

    def _on_save_profile(self) -> None:
        if self._raw_audio is None or len(self._raw_audio) < 100:
            QMessageBox.warning(self, "No Audio",
                "Record or upload at least 1 second of your voice first.")
            return
        name, ok = QInputDialog.getText(self, "Profile Name",
                                        "Enter a name for this voice profile:", text="My Voice")
        if not ok or not name.strip():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Voice Profile",
                                              f"{name.strip()}.vgprofile",
                                              "Voice Profile (*.vgprofile)")
        if not path:
            return

        self._btn_save_profile.setEnabled(False)
        self._profile_status.setText("Analysing voice characteristics...")
        self._profile_worker = ProfileWorker(self._raw_audio, self._sr)
        self._profile_worker.finished.connect(lambda p: self._on_profile_done(p, path, name.strip()))
        self._profile_worker.error.connect(self._on_profile_error)
        self._profile_worker.start()

    def _on_profile_done(self, profile: dict, path: str, name: str) -> None:
        try:
            save_profile(path, profile, name=name)
            pitch = profile["pitch_mean"]
            shift = profile["semitone_shift"]
            self._profile_status.setText(
                f"Saved  |  Pitch: {pitch:.0f} Hz  |  Shift: {shift:+.1f} st")
            QMessageBox.information(self, "Voice Profile Saved",
                f"Profile saved: {os.path.basename(path)}\n"
                f"Pitch: {pitch:.0f} Hz  |  Shift: {shift:+.1f} semitones")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            self._profile_status.setText("")
        finally:
            self._btn_save_profile.setEnabled(True)

    def _on_profile_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Analysis Error", msg)
        self._profile_status.setText("")
        self._btn_save_profile.setEnabled(True)

    # ------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        self._status.setText(msg)
        self.status_message.emit(msg)
