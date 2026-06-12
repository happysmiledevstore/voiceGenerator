"""In-memory index + filesystem storage for audio blobs."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

from .config import settings


@dataclass
class AudioRecord:
    id: str
    path: Path
    sample_rate: int
    duration_s: float
    source: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sample_rate": self.sample_rate,
            "duration_s": round(self.duration_s, 3),
            "source": self.source,
            "created_at": self.created_at,
        }


class AudioStore:
    def __init__(self) -> None:
        self._records: dict[str, AudioRecord] = {}

    def save_array(
        self,
        audio: np.ndarray,
        sample_rate: int,
        source: str = "upload",
        subdir: str = "uploads",
    ) -> AudioRecord:
        audio_id = str(uuid.uuid4())
        folder = settings.data_dir / subdir
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{audio_id}.wav"
        clipped = np.clip(audio.astype(np.float32), -1.0, 1.0)
        sf.write(path, clipped, sample_rate)

        duration = len(audio) / sample_rate if sample_rate else 0.0
        record = AudioRecord(
            id=audio_id,
            path=path,
            sample_rate=sample_rate,
            duration_s=duration,
            source=source,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._records[audio_id] = record
        self._persist_index(record)
        return record

    def get(self, audio_id: str) -> AudioRecord | None:
        if audio_id in self._records:
            return self._records[audio_id]
        return self._load_from_disk(audio_id)

    def load_audio(self, audio_id: str) -> tuple[np.ndarray, int]:
        record = self.get(audio_id)
        if record is None or not record.path.is_file():
            raise FileNotFoundError(f"Audio '{audio_id}' not found.")
        audio, sr = sf.read(record.path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio.astype(np.float32), sr

    def _persist_index(self, record: AudioRecord) -> None:
        meta_path = record.path.with_suffix(".json")
        meta_path.write_text(json.dumps(asdict(record), default=str), encoding="utf-8")

    def _load_from_disk(self, audio_id: str) -> AudioRecord | None:
        for subdir in ("uploads", "processed"):
            folder = settings.data_dir / subdir
            wav = folder / f"{audio_id}.wav"
            meta = folder / f"{audio_id}.json"
            if wav.is_file():
                sr = settings.sample_rate
                duration = 0.0
                source = subdir
                created_at = datetime.now(timezone.utc).isoformat()
                if meta.is_file():
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    sr = int(data.get("sample_rate", sr))
                    duration = float(data.get("duration_s", 0.0))
                    source = data.get("source", source)
                    created_at = data.get("created_at", created_at)
                    if data.get("path"):
                        wav = Path(data["path"])
                else:
                    audio, sr = sf.read(wav, dtype="float32")
                    if audio.ndim > 1:
                        audio = audio.mean(axis=1)
                    duration = len(audio) / sr
                record = AudioRecord(
                    id=audio_id,
                    path=wav,
                    sample_rate=sr,
                    duration_s=duration,
                    source=source,
                    created_at=created_at,
                )
                self._records[audio_id] = record
                return record
        return None


audio_store = AudioStore()
