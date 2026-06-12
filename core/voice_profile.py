"""
Voice Profile — analyse a recorded voice sample, save the characteristics
as a JSON file, and apply them to any TTS audio to make it sound closer
to the recorded voice.

Stored parameters
-----------------
pitch_mean  : mean fundamental frequency (Hz) of the recorded voice
pitch_std   : standard deviation of F0
speaking_rate : approximate syllables-per-second (used for speed adjustment)
semitone_shift: pre-computed shift (relative to a reference 165 Hz neutral)
"""

import json
import os
import numpy as np
from typing import Optional


# Neutral reference pitch for a generic TTS voice (Hz)
_REFERENCE_PITCH_HZ = 165.0


def _hz_to_semitones(target_hz: float, reference_hz: float) -> float:
    """Convert a frequency ratio to semitones."""
    if reference_hz <= 0 or target_hz <= 0:
        return 0.0
    return 12.0 * np.log2(target_hz / reference_hz)


def analyse_voice(audio: np.ndarray, sr: int) -> dict:
    """
    Analyse a voice recording and return a dict of characteristics.

    Parameters
    ----------
    audio : float32 mono numpy array
    sr    : sample rate

    Returns
    -------
    dict with keys: pitch_mean, pitch_std, speaking_rate, semitone_shift
    """
    import librosa

    if len(audio) == 0:
        raise ValueError("Audio is empty — cannot analyse voice profile.")

    duration = len(audio) / sr
    if duration < 1.0:
        raise ValueError(
            f"Recording is too short ({duration:.1f}s). "
            "Please record at least 1 second of speech."
        )

    # --- Pitch extraction (F0) via pyin ---
    f0, voiced_flag, _ = librosa.pyin(
        audio,
        fmin=librosa.note_to_hz("C2"),   # ~65 Hz
        fmax=librosa.note_to_hz("C7"),   # ~2093 Hz
        sr=sr,
    )

    voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]

    if len(voiced_f0) < 10:
        raise ValueError(
            "Could not detect enough voiced speech. "
            "Please record yourself speaking clearly."
        )

    pitch_mean = float(np.mean(voiced_f0))
    pitch_std  = float(np.std(voiced_f0))
    semitone_shift = _hz_to_semitones(pitch_mean, _REFERENCE_PITCH_HZ)

    # --- Approximate speaking rate via zero-crossing bursts ---
    # Count voiced frames as a proxy for syllable rate
    voiced_count = int(np.sum(voiced_flag))
    hop_length = 512
    voiced_duration = (voiced_count * hop_length) / sr
    speaking_rate = round(voiced_count / max(duration, 0.1), 2)

    return {
        "pitch_mean":     round(pitch_mean, 2),
        "pitch_std":      round(pitch_std, 2),
        "speaking_rate":  speaking_rate,
        "semitone_shift": round(semitone_shift, 2),
        "duration_s":     round(duration, 2),
    }


def save_profile(path: str, profile: dict, name: str = "") -> None:
    """Save a voice profile dict as JSON to `path`."""
    data = {"name": name or os.path.splitext(os.path.basename(path))[0]}
    data.update(profile)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_profile(path: str) -> dict:
    """Load and return a voice profile dict from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def profile_to_transform_params(profile: dict) -> dict:
    """
    Convert a voice profile into VoiceChanger.transform() keyword arguments.

    The TTS output will be pitch-shifted to match the recorded voice's
    fundamental frequency, giving a rough approximation of the user's voice.
    """
    return {
        "pitch_semitones": profile.get("semitone_shift", 0.0),
        "speed_rate":      1.0,   # preserve natural TTS pacing
        "effect":          None,
    }
