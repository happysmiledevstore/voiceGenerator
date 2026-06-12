from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.voice_changer import VoiceChanger
from core.voice_profile import analyse_voice, profile_to_transform_params

from ..profile_store import profile_store
from ..schemas import (
    ApplyProfileRequest,
    AudioMeta,
    ProfileAnalyzeRequest,
    SaveProfileRequest,
    SavedVoiceProfile,
    TransformResponse,
    UpdateProfileRequest,
    VoiceProfile,
)
from ..storage import audio_store

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _to_saved(profile) -> SavedVoiceProfile:
    return SavedVoiceProfile(**profile.to_dict())


def _resolve_profile(body: ApplyProfileRequest) -> VoiceProfile:
    if body.profile_id:
        saved = profile_store.get(body.profile_id)
        if saved is None:
            raise HTTPException(404, f"Profile '{body.profile_id}' not found.")
        return VoiceProfile(**saved.to_voice_profile())
    if body.profile:
        return body.profile
    raise HTTPException(400, "Provide profile_id or profile.")


@router.get("", response_model=list[SavedVoiceProfile])
def list_profiles() -> list[SavedVoiceProfile]:
    return [_to_saved(p) for p in profile_store.list_all()]


@router.get("/{profile_id}", response_model=SavedVoiceProfile)
def get_profile(profile_id: str) -> SavedVoiceProfile:
    saved = profile_store.get(profile_id)
    if saved is None:
        raise HTTPException(404, "Profile not found.")
    return _to_saved(saved)


@router.get("/{profile_id}/export")
def export_profile(profile_id: str):
    saved = profile_store.get(profile_id)
    if saved is None:
        raise HTTPException(404, "Profile not found.")
    filename = f"{saved.name.replace(' ', '_')}.vgprofile.json"
    return JSONResponse(
        content=saved.to_voice_profile() | {"id": saved.id, "created_at": saved.created_at},
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/save", response_model=SavedVoiceProfile)
def save_profile(body: SaveProfileRequest) -> SavedVoiceProfile:
    if body.audio_id:
        try:
            audio, sr = audio_store.load_audio(body.audio_id)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        try:
            analyzed = analyse_voice(audio, sr)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        saved = profile_store.save(name=body.name, **analyzed)
        return _to_saved(saved)

    if body.profile:
        p = body.profile
        saved = profile_store.save(
            name=body.name or p.name,
            pitch_mean=p.pitch_mean,
            pitch_std=p.pitch_std,
            speaking_rate=p.speaking_rate,
            semitone_shift=p.semitone_shift,
            duration_s=p.duration_s,
        )
        return _to_saved(saved)

    raise HTTPException(400, "Provide audio_id to analyse or profile to import.")


@router.patch("/{profile_id}", response_model=SavedVoiceProfile)
def update_profile(profile_id: str, body: UpdateProfileRequest) -> SavedVoiceProfile:
    updated = profile_store.update_name(profile_id, body.name)
    if updated is None:
        raise HTTPException(404, "Profile not found.")
    return _to_saved(updated)


@router.delete("/{profile_id}")
def delete_profile(profile_id: str) -> dict:
    if not profile_store.delete(profile_id):
        raise HTTPException(404, "Profile not found.")
    return {"deleted": profile_id}


@router.post("/analyze", response_model=VoiceProfile)
def analyze_profile(body: ProfileAnalyzeRequest) -> VoiceProfile:
    try:
        audio, sr = audio_store.load_audio(body.audio_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        profile = analyse_voice(audio, sr)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return VoiceProfile(name="My Voice", **profile)


@router.post("/apply", response_model=TransformResponse)
def apply_profile(body: ApplyProfileRequest) -> TransformResponse:
    try:
        audio, sr = audio_store.load_audio(body.audio_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    profile = _resolve_profile(body)
    params = profile_to_transform_params(profile.model_dump())
    changer = VoiceChanger()
    processed = changer.transform(audio, sr, **params)
    record = audio_store.save_array(processed, sr, source="processed", subdir="processed")

    meta = AudioMeta(**record.to_dict())
    return TransformResponse(audio_id=record.id, meta=meta)
