"""Shared audio file I/O (no microphone / sounddevice dependency)."""

import numpy as np
import soundfile as sf

SAMPLE_RATE = 44100


def load_audio_file(path: str, target_sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """Load any audio file and return (float32 mono array, sample_rate)."""
    import librosa

    audio, sr = librosa.load(path, sr=target_sr, mono=True)
    return audio.astype(np.float32), sr


def save_audio_file(path: str, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Save a float32 numpy array as a WAV file."""
    audio_clamped = np.clip(audio, -1.0, 1.0)
    sf.write(path, audio_clamped, sample_rate)
