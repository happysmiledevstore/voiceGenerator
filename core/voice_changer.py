"""
Voice transformation engine.
All functions accept and return float32 numpy arrays at the same sample rate.
No librosa I/O here — that lives in recorder.py.
"""

import numpy as np
from scipy import signal as sp_signal
from typing import Optional
import soundfile as sf


# ---------------------------------------------------------------------------
# Low-level DSP helpers
# ---------------------------------------------------------------------------

def _normalize(audio: np.ndarray) -> np.ndarray:
    """Peak-normalise to ±1 without changing silence."""
    peak = np.max(np.abs(audio))
    if peak < 1e-6:
        return audio
    return audio / peak


def pitch_shift(audio: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    """Shift pitch by ±semitones without changing duration."""
    import librosa
    if semitones == 0:
        return audio
    shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=semitones)
    return shifted.astype(np.float32)


def time_stretch(audio: np.ndarray, rate: float) -> np.ndarray:
    """
    Stretch/compress duration by `rate` without changing pitch.
    rate > 1 → faster (shorter), rate < 1 → slower (longer).
    """
    import librosa
    if rate == 1.0:
        return audio
    stretched = librosa.effects.time_stretch(audio, rate=rate)
    return stretched.astype(np.float32)


def add_echo(audio: np.ndarray, sr: int, delay_ms: float = 250, decay: float = 0.5) -> np.ndarray:
    """Simple single-tap echo / delay effect."""
    delay_samples = int(sr * delay_ms / 1000)
    output = audio.copy()
    if delay_samples < len(audio):
        output[delay_samples:] += audio[: len(audio) - delay_samples] * decay
    return np.clip(output, -1.0, 1.0).astype(np.float32)


def add_reverb(audio: np.ndarray, sr: int, room_size: float = 0.5) -> np.ndarray:
    """
    Plate-reverb approximation using a series of all-pass and comb filters.
    room_size in [0, 1].
    """
    # Build a simple FIR reverb kernel
    n_taps = int(sr * room_size * 0.4)
    n_taps = max(100, min(n_taps, sr))
    t = np.linspace(0, room_size, n_taps)
    kernel = np.exp(-6 * t) * (np.random.randn(n_taps) * 0.3 + 0.7)
    kernel /= np.sum(np.abs(kernel))

    reverbed = sp_signal.fftconvolve(audio, kernel, mode="full")[: len(audio)]
    wet_mix = 0.35
    output = (1 - wet_mix) * audio + wet_mix * reverbed.astype(np.float32)
    return np.clip(output, -1.0, 1.0).astype(np.float32)


def robot_effect(audio: np.ndarray, sr: int, carrier_freq: float = 100.0) -> np.ndarray:
    """
    Vocoder-style robot voice: multiply by a carrier sine wave then
    apply bandpass filtering to keep harmonics.
    """
    t = np.arange(len(audio)) / sr
    carrier = np.sin(2 * np.pi * carrier_freq * t).astype(np.float32)

    # Amplitude-modulate the signal
    modulated = audio * carrier

    # Low-pass to smooth out the buzz
    b, a = sp_signal.butter(4, 3000 / (sr / 2), btype="low")
    filtered = sp_signal.lfilter(b, a, modulated).astype(np.float32)

    return _normalize(filtered)


def alien_effect(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Pitch-shift up 7 semitones + ring-modulate with a fast carrier,
    then add light echo.
    """
    shifted = pitch_shift(audio, sr, semitones=7)
    t = np.arange(len(shifted)) / sr
    carrier = np.sin(2 * np.pi * 700 * t).astype(np.float32)
    modulated = np.clip(shifted * (0.7 + 0.3 * carrier), -1.0, 1.0)
    return add_echo(modulated, sr, delay_ms=120, decay=0.4)


# ---------------------------------------------------------------------------
# Preset factory
# ---------------------------------------------------------------------------

PRESETS = {
    "Normal":     {"pitch": 0.0,   "speed": 1.0,  "effect": None},
    "Deep Voice": {"pitch": -5.0,  "speed": 0.92, "effect": None},
    "Chipmunk":   {"pitch": 8.0,   "speed": 1.2,  "effect": None},
    "Robot":      {"pitch": 0.0,   "speed": 1.0,  "effect": "robot"},
    "Echo":       {"pitch": 0.0,   "speed": 1.0,  "effect": "echo"},
    "Reverb":     {"pitch": 0.0,   "speed": 1.0,  "effect": "reverb"},
    "Alien":      {"pitch": 7.0,   "speed": 1.1,  "effect": "alien"},
}


# ---------------------------------------------------------------------------
# Main transform pipeline
# ---------------------------------------------------------------------------

class VoiceChanger:
    """Apply a chain of transforms to an audio array."""

    def __init__(self) -> None:
        self.sample_rate: int = 44100

    def transform(
        self,
        audio: np.ndarray,
        sr: int,
        pitch_semitones: float = 0.0,
        speed_rate: float = 1.0,
        effect: Optional[str] = None,
    ) -> np.ndarray:
        """
        Full transform pipeline.

        Parameters
        ----------
        audio           : float32 mono numpy array
        sr              : sample rate of the audio
        pitch_semitones : semitones to shift pitch (-12 to +12)
        speed_rate      : playback speed multiplier (0.5 to 2.0)
        effect          : one of 'robot', 'echo', 'reverb', 'alien', or None
        """
        self.sample_rate = sr
        out = audio.astype(np.float32)

        # 1. Pitch shift (keeps duration)
        if pitch_semitones != 0.0:
            out = pitch_shift(out, sr, pitch_semitones)

        # 2. Speed / time-stretch (keeps pitch after step 1)
        if speed_rate != 1.0:
            out = time_stretch(out, speed_rate)

        # 3. Special effect
        effect_map = {
            "robot":  lambda a: robot_effect(a, sr),
            "echo":   lambda a: add_echo(a, sr),
            "reverb": lambda a: add_reverb(a, sr),
            "alien":  lambda a: alien_effect(a, sr),
        }
        if effect and effect in effect_map:
            out = effect_map[effect](out)

        return _normalize(out)

    def apply_preset(self, audio: np.ndarray, sr: int, preset_name: str) -> np.ndarray:
        p = PRESETS.get(preset_name, PRESETS["Normal"])
        return self.transform(
            audio, sr,
            pitch_semitones=p["pitch"],
            speed_rate=p["speed"],
            effect=p["effect"],
        )

    def export(self, path: str, audio: np.ndarray, sr: int) -> None:
        """Save transformed audio. Supports .wav and .mp3 (mp3 requires ffmpeg)."""
        if path.lower().endswith(".mp3"):
            try:
                from pydub import AudioSegment
                import io
                buf = io.BytesIO()
                sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
                buf.seek(0)
                seg = AudioSegment.from_wav(buf)
                seg.export(path, format="mp3")
            except Exception:
                wav_path = path.replace(".mp3", ".wav")
                sf.write(wav_path, audio, sr)
                raise RuntimeError(
                    f"MP3 export requires ffmpeg. Saved as WAV instead: {wav_path}"
                )
        else:
            sf.write(path, np.clip(audio, -1.0, 1.0), sr)
