from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..audio_decode import decode_uploaded_file
from core.voice_changer import PRESETS, VoiceChanger

from ..schemas import ApplyPresetRequest, AudioMeta, PresetInfo, TransformRequest, TransformResponse
from ..storage import audio_store

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/presets", response_model=list[PresetInfo])
def list_presets() -> list[PresetInfo]:
    return [
        PresetInfo(
            name=name,
            pitch=p["pitch"],
            speed=p["speed"],
            effect=p["effect"],
        )
        for name, p in PRESETS.items()
    ]


@router.post("/upload", response_model=AudioMeta)
async def upload_audio(file: UploadFile = File(...)) -> AudioMeta:
    if not file.filename:
        raise HTTPException(400, "Missing filename.")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file.")

    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ".wav"
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        audio, sr = decode_uploaded_file(tmp_path)
    except Exception as exc:
        raise HTTPException(400, f"Could not decode audio: {exc}") from exc
    finally:
        os.unlink(tmp_path)

    record = audio_store.save_array(audio, sr, source="upload")
    return AudioMeta(**record.to_dict())


@router.get("/{audio_id}", response_model=AudioMeta)
def get_audio_meta(audio_id: str) -> AudioMeta:
    record = audio_store.get(audio_id)
    if record is None:
        raise HTTPException(404, "Audio not found.")
    return AudioMeta(**record.to_dict())


@router.get("/{audio_id}/file")
def download_audio(audio_id: str):
    record = audio_store.get(audio_id)
    if record is None or not record.path.is_file():
        raise HTTPException(404, "Audio not found.")
    return FileResponse(
        record.path,
        media_type="audio/wav",
        filename=f"{audio_id}.wav",
    )


@router.post("/transform", response_model=TransformResponse)
def transform_audio(body: TransformRequest) -> TransformResponse:
    try:
        audio, sr = audio_store.load_audio(body.audio_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    changer = VoiceChanger()
    processed = changer.transform(
        audio,
        sr,
        pitch_semitones=body.pitch_semitones,
        speed_rate=body.speed_rate,
        effect=body.effect,
    )
    record = audio_store.save_array(processed, sr, source="processed", subdir="processed")
    meta = AudioMeta(**record.to_dict())
    return TransformResponse(audio_id=record.id, meta=meta)


@router.post("/apply-preset", response_model=TransformResponse)
def apply_preset(body: ApplyPresetRequest) -> TransformResponse:
    preset = PRESETS.get(body.preset_name)
    if preset is None:
        raise HTTPException(404, f"Preset '{body.preset_name}' not found.")

    try:
        audio, sr = audio_store.load_audio(body.audio_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    changer = VoiceChanger()
    processed = changer.apply_preset(audio, sr, body.preset_name)
    record = audio_store.save_array(processed, sr, source="processed", subdir="processed")
    meta = AudioMeta(**record.to_dict())
    return TransformResponse(audio_id=record.id, meta=meta)
