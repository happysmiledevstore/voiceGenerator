"""Persist voice profiles as JSON files under data/profiles/."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


@dataclass
class SavedProfile:
    id: str
    name: str
    pitch_mean: float
    pitch_std: float
    speaking_rate: float
    semitone_shift: float
    duration_s: float
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_voice_profile(self) -> dict:
        return {
            "name": self.name,
            "pitch_mean": self.pitch_mean,
            "pitch_std": self.pitch_std,
            "speaking_rate": self.speaking_rate,
            "semitone_shift": self.semitone_shift,
            "duration_s": self.duration_s,
        }


class ProfileStore:
    def __init__(self) -> None:
        self._dir = settings.data_dir / "profiles"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, profile_id: str) -> Path:
        return self._dir / f"{profile_id}.json"

    def list_all(self) -> list[SavedProfile]:
        profiles: list[SavedProfile] = []
        for path in sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                profiles.append(self._load_file(path))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return profiles

    def get(self, profile_id: str) -> SavedProfile | None:
        path = self._path(profile_id)
        if not path.is_file():
            return None
        try:
            return self._load_file(path)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save(
        self,
        name: str,
        pitch_mean: float,
        pitch_std: float,
        speaking_rate: float,
        semitone_shift: float,
        duration_s: float,
        profile_id: str | None = None,
    ) -> SavedProfile:
        now = datetime.now(timezone.utc).isoformat()
        pid = profile_id or str(uuid.uuid4())
        existing = self.get(pid)
        created = existing.created_at if existing else now

        profile = SavedProfile(
            id=pid,
            name=name.strip() or "My Voice",
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            speaking_rate=speaking_rate,
            semitone_shift=semitone_shift,
            duration_s=duration_s,
            created_at=created,
            updated_at=now,
        )
        self._path(pid).write_text(
            json.dumps(profile.to_dict(), indent=2),
            encoding="utf-8",
        )
        return profile

    def update_name(self, profile_id: str, name: str) -> SavedProfile | None:
        existing = self.get(profile_id)
        if existing is None:
            return None
        return self.save(
            name=name,
            pitch_mean=existing.pitch_mean,
            pitch_std=existing.pitch_std,
            speaking_rate=existing.speaking_rate,
            semitone_shift=existing.semitone_shift,
            duration_s=existing.duration_s,
            profile_id=profile_id,
        )

    def delete(self, profile_id: str) -> bool:
        path = self._path(profile_id)
        if path.is_file():
            path.unlink()
            return True
        return False

    def _load_file(self, path: Path) -> SavedProfile:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SavedProfile(
            id=data["id"],
            name=data["name"],
            pitch_mean=float(data["pitch_mean"]),
            pitch_std=float(data["pitch_std"]),
            speaking_rate=float(data["speaking_rate"]),
            semitone_shift=float(data["semitone_shift"]),
            duration_s=float(data["duration_s"]),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


profile_store = ProfileStore()
