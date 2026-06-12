"""
Text-to-Speech engine with two backends:
  - gTTS  : Google TTS (requires internet, natural quality)
  - pyttsx3: Offline system TTS (no internet needed, robotic)

Returns float32 numpy audio arrays for downstream processing.
"""

import io
import os
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional


# ---------------------------------------------------------------------------
# Language map (display name → gTTS language code)
# ---------------------------------------------------------------------------

LANGUAGES = {
    "English":    "en",
    "Spanish":    "es",
    "French":     "fr",
    "German":     "de",
    "Italian":    "it",
    "Portuguese": "pt",
    "Russian":    "ru",
    "Japanese":   "ja",
    "Chinese":    "zh",
    "Arabic":     "ar",
    "Hindi":      "hi",
    "Korean":     "ko",
}


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

class GTTSBackend:
    """Online Google TTS via the gTTS library."""

    def synthesize(self, text: str, lang: str = "en", slow: bool = False) -> tuple[np.ndarray, int]:
        from gtts import gTTS
        import librosa

        tts = gTTS(text=text, lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(buf.read())
            tmp_path = tmp.name

        try:
            audio, sr = librosa.load(tmp_path, sr=44100, mono=True)
        finally:
            os.unlink(tmp_path)

        return audio.astype(np.float32), sr


class Pyttsx3Backend:
    """Offline TTS using the system's speech engine via pyttsx3."""

    def __init__(self) -> None:
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            import pyttsx3
            self._engine = pyttsx3.init()
        return self._engine

    def get_voices(self) -> list[dict]:
        engine = self._get_engine()
        return [
            {"id": v.id, "name": v.name, "lang": getattr(v, "languages", [""])[0]}
            for v in engine.getProperty("voices")
        ]

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        rate: int = 175,
    ) -> tuple[np.ndarray, int]:
        import librosa

        engine = self._get_engine()
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", rate)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            audio, sr = librosa.load(tmp_path, sr=44100, mono=True)
        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

        return audio.astype(np.float32), sr


# ---------------------------------------------------------------------------
# Unified TTS Engine
# ---------------------------------------------------------------------------

class TTSEngine:
    """
    High-level TTS interface.
    Tries gTTS first; falls back to pyttsx3 if network is unavailable.
    """

    def __init__(self) -> None:
        self._gtts = GTTSBackend()
        self._pyttsx3 = Pyttsx3Backend()

    def synthesize_gtts(
        self,
        text: str,
        language: str = "English",
        slow: bool = False,
    ) -> tuple[np.ndarray, int]:
        lang_code = LANGUAGES.get(language, "en")
        return self._gtts.synthesize(text, lang=lang_code, slow=slow)

    def synthesize_offline(
        self,
        text: str,
        voice_id: Optional[str] = None,
        rate: int = 175,
    ) -> tuple[np.ndarray, int]:
        return self._pyttsx3.synthesize(text, voice_id=voice_id, rate=rate)

    def get_offline_voices(self) -> list[dict]:
        try:
            return self._pyttsx3.get_voices()
        except Exception:
            return []

    def synthesize(
        self,
        text: str,
        engine: str = "gtts",
        language: str = "English",
        slow: bool = False,
        voice_id: Optional[str] = None,
        rate: int = 175,
    ) -> tuple[np.ndarray, int]:
        """
        Unified entry point.

        Parameters
        ----------
        engine   : 'gtts' or 'offline'
        language : Display name from LANGUAGES dict (for gTTS)
        slow     : Slow down speech (gTTS only)
        voice_id : System voice ID (offline only)
        rate     : Words-per-minute (offline only)
        """
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        if engine == "gtts":
            try:
                return self.synthesize_gtts(text, language=language, slow=slow)
            except Exception as exc:
                # Fall back to offline engine
                print(f"[TTSEngine] gTTS failed ({exc}), falling back to offline engine.")
                return self.synthesize_offline(text, voice_id=voice_id, rate=rate)
        else:
            return self.synthesize_offline(text, voice_id=voice_id, rate=rate)
