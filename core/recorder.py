"""
Microphone recording using sounddevice.
Captures audio in a background thread; callers poll or connect to signals.
"""

import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable

from core.audio_io import SAMPLE_RATE, load_audio_file, save_audio_file

__all__ = ["Recorder", "SAMPLE_RATE", "load_audio_file", "save_audio_file"]
CHANNELS = 1
DTYPE = "float32"


class Recorder:
    """Thread-safe microphone recorder."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self._recording = False
        self._paused = False
        self.on_chunk: Optional[Callable[[np.ndarray], None]] = None  # live callback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._recording:
            return
        with self._lock:
            self._frames = []
        self._recording = True
        self._paused = False
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=DTYPE,
            callback=self._callback,
            blocksize=1024,
        )
        self._stream.start()

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> np.ndarray:
        """Stop recording and return the full audio as a 1-D float32 array."""
        self._recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            if self._frames:
                audio = np.concatenate(self._frames, axis=0).flatten()
            else:
                audio = np.zeros(0, dtype=np.float32)
        return audio

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_paused(self) -> bool:
        return self._paused

    def get_devices(self) -> list[dict]:
        """Return available input devices."""
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if not self._recording or self._paused:
            return
        chunk = indata.copy()
        with self._lock:
            self._frames.append(chunk)
        if self.on_chunk is not None:
            self.on_chunk(chunk.flatten())
