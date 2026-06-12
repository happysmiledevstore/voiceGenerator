from typing import Literal

from pydantic import BaseModel, Field


EffectName = Literal["robot", "echo", "reverb", "alien"] | None


class AudioMeta(BaseModel):
    id: str
    sample_rate: int
    duration_s: float
    source: str
    created_at: str


class TransformRequest(BaseModel):
    audio_id: str
    pitch_semitones: float = Field(0.0, ge=-12.0, le=12.0)
    speed_rate: float = Field(1.0, ge=0.5, le=2.0)
    effect: EffectName = None


class TransformResponse(BaseModel):
    audio_id: str
    meta: AudioMeta


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    engine: Literal["gtts", "offline"] = "gtts"
    language: str = "English"
    slow: bool = False
    voice_id: str | None = None
    rate: int = Field(175, ge=50, le=400)


class TTSResponse(BaseModel):
    audio_id: str
    meta: AudioMeta


class ProfileAnalyzeRequest(BaseModel):
    audio_id: str


class VoiceProfile(BaseModel):
    name: str = "My Voice"
    pitch_mean: float
    pitch_std: float
    speaking_rate: float
    semitone_shift: float
    duration_s: float


class SavedVoiceProfile(VoiceProfile):
    id: str
    created_at: str
    updated_at: str


class SaveProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    audio_id: str | None = None
    profile: VoiceProfile | None = None


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ApplyProfileRequest(BaseModel):
    audio_id: str
    profile: VoiceProfile | None = None
    profile_id: str | None = None


class ApplyPresetRequest(BaseModel):
    audio_id: str
    preset_name: str


class PresetInfo(BaseModel):
    name: str
    pitch: float
    speed: float
    effect: str | None
