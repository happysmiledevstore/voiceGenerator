"""Read-only celebrity voice samples — stylized approximations for demo use."""

from __future__ import annotations

from dataclasses import dataclass

SAMPLE_PREFIX = "sample-"


@dataclass(frozen=True)
class SampleProfile:
    id: str
    name: str
    description: str
    pitch_mean: float
    pitch_std: float
    speaking_rate: float
    semitone_shift: float
    duration_s: float


def _sample(
    slug: str,
    name: str,
    description: str,
    pitch_mean: float,
    pitch_std: float,
    speaking_rate: float,
    semitone_shift: float,
) -> SampleProfile:
    return SampleProfile(
        id=f"{SAMPLE_PREFIX}{slug}",
        name=name,
        description=description,
        pitch_mean=pitch_mean,
        pitch_std=pitch_std,
        speaking_rate=speaking_rate,
        semitone_shift=semitone_shift,
        duration_s=3.0,
    )


# Approximate pitch / pacing characteristics — not recordings of real people.
CELEBRITY_SAMPLES: tuple[SampleProfile, ...] = (
    _sample(
        "morgan-freeman",
        "Morgan Freeman",
        "Deep, warm narrator tone with unhurried delivery.",
        pitch_mean=118.0,
        pitch_std=14.0,
        speaking_rate=92.0,
        semitone_shift=-5.2,
    ),
    _sample(
        "james-earl-jones",
        "James Earl Jones",
        "Very low, commanding baritone with steady pacing.",
        pitch_mean=108.0,
        pitch_std=11.0,
        speaking_rate=88.0,
        semitone_shift=-6.5,
    ),
    _sample(
        "david-attenborough",
        "David Attenborough",
        "Calm British documentary voice — measured and clear.",
        pitch_mean=128.0,
        pitch_std=13.0,
        speaking_rate=95.0,
        semitone_shift=-4.4,
    ),
    _sample(
        "barack-obama",
        "Barack Obama",
        "Mid-baritone political speaker with deliberate rhythm.",
        pitch_mean=138.0,
        pitch_std=16.0,
        speaking_rate=102.0,
        semitone_shift=-3.1,
    ),
    _sample(
        "arnold-schwarzenegger",
        "Arnold Schwarzenegger",
        "Deep action-hero voice with a slower, heavier cadence.",
        pitch_mean=122.0,
        pitch_std=18.0,
        speaking_rate=78.0,
        semitone_shift=-5.0,
    ),
    _sample(
        "scarlett-johansson",
        "Scarlett Johansson",
        "Low, smoky alto with a relaxed conversational pace.",
        pitch_mean=196.0,
        pitch_std=22.0,
        speaking_rate=98.0,
        semitone_shift=2.9,
    ),
    _sample(
        "emma-watson",
        "Emma Watson",
        "Bright, articulate soprano with crisp enunciation.",
        pitch_mean=212.0,
        pitch_std=24.0,
        speaking_rate=110.0,
        semitone_shift=4.4,
    ),
    _sample(
        "oprah-winfrey",
        "Oprah Winfrey",
        "Rich, expressive mezzo with emphatic delivery.",
        pitch_mean=182.0,
        pitch_std=26.0,
        speaking_rate=105.0,
        semitone_shift=1.6,
    ),
    _sample(
        "taylor-swift",
        "Taylor Swift",
        "Light, youthful soprano with upbeat pacing.",
        pitch_mean=220.0,
        pitch_std=28.0,
        speaking_rate=115.0,
        semitone_shift=5.2,
    ),
    _sample(
        "adele",
        "Adele",
        "Warm, soulful mezzo with a slightly slower drawl.",
        pitch_mean=186.0,
        pitch_std=21.0,
        speaking_rate=90.0,
        semitone_shift=2.0,
    ),
)

_SAMPLES_BY_ID = {p.id: p for p in CELEBRITY_SAMPLES}


def is_sample_profile_id(profile_id: str) -> bool:
    return profile_id.startswith(SAMPLE_PREFIX)


def get_sample(profile_id: str) -> SampleProfile | None:
    return _SAMPLES_BY_ID.get(profile_id)


def list_samples() -> list[SampleProfile]:
    return list(CELEBRITY_SAMPLES)


def sample_to_saved_dict(sample: SampleProfile) -> dict:
    return {
        "id": sample.id,
        "name": sample.name,
        "pitch_mean": sample.pitch_mean,
        "pitch_std": sample.pitch_std,
        "speaking_rate": sample.speaking_rate,
        "semitone_shift": sample.semitone_shift,
        "duration_s": sample.duration_s,
        "created_at": "",
        "updated_at": "",
        "is_sample": True,
        "description": sample.description,
    }
