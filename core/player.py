"""
Non-blocking audio playback using sounddevice.
Supports play, pause, stop and a completion callback.
"""

import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable


class Player:
    """Play a numpy audio array asynchronously."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused by default
        self._playing = False
        self.on_finished: Optional[Callable[[], None]] = None
        self._current_audio: Optional[np.ndarray] = None
        self._current_sr: int = 44100

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, audio: np.ndarray, sample_rate: int = 44100) -> None:
        """Start playback in a background thread. Stops any current playback first."""
        self.stop()
        self._current_audio = audio.astype(np.float32)
        self._current_sr = sample_rate
        self._stop_event.clear()
        self._pause_event.set()
        self._playing = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        if self._playing:
            self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._playing = False

    @property
    def is_playing(self) -> bool:
        return self._playing

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        audio = self._current_audio
        sr = self._current_sr
        chunk_size = 1024
        pos = 0

        try:
            with sd.OutputStream(samplerate=sr, channels=1, dtype="float32") as stream:
                while pos < len(audio) and not self._stop_event.is_set():
                    self._pause_event.wait()  # block while paused
                    if self._stop_event.is_set():
                        break
                    end = min(pos + chunk_size, len(audio))
                    stream.write(audio[pos:end])
                    pos = end
        finally:
            self._playing = False
            if self.on_finished is not None:
                self.on_finished()
