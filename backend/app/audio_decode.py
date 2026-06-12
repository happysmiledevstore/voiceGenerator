"""Decode uploaded audio files — WAV via librosa, WebM/MP3 via pydub when FFmpeg is available."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from core.recorder import SAMPLE_RATE, load_audio_file

_WEB_FORMATS = {".webm", ".ogg", ".mp4", ".m4a", ".aac", ".mp3", ".flac"}


def decode_uploaded_file(path: str, target_sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    suffix = Path(path).suffix.lower()

    if suffix == ".wav":
        return load_audio_file(path, target_sr=target_sr)

    try:
        return load_audio_file(path, target_sr=target_sr)
    except Exception:
        pass

    if suffix in _WEB_FORMATS:
        return _decode_with_pydub(path, target_sr)

    raise ValueError(
        f"Unsupported or unreadable audio format '{suffix or 'unknown'}'. "
        "Try WAV, MP3, or install FFmpeg for WebM support."
    )


def _decode_with_pydub(path: str, target_sr: int) -> tuple[np.ndarray, int]:
    try:
        from pydub import AudioSegment
    except ImportError as exc:
        raise ValueError("pydub is not installed.") from exc

    try:
        segment = AudioSegment.from_file(path)
    except Exception as exc:
        raise ValueError(
            "WebM and other compressed formats require FFmpeg on the server. "
            "Install FFmpeg or record again (browser now saves WAV)."
        ) from exc

    segment = segment.set_channels(1).set_frame_rate(target_sr)
    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
    peak = float(2 ** (8 * segment.sample_width - 1))
    if peak > 0:
        samples /= peak

    return samples.astype(np.float32), target_sr
