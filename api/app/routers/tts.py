from fastapi import APIRouter, HTTPException

from core.tts_engine import LANGUAGES, TTSEngine

from ..schemas import AudioMeta, TTSRequest, TTSResponse
from ..storage import audio_store

router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/languages")
def list_languages() -> dict[str, str]:
    return LANGUAGES


@router.get("/voices")
def list_offline_voices() -> list[dict]:
    engine = TTSEngine()
    return engine.get_offline_voices()


@router.post("/generate", response_model=TTSResponse)
def generate_speech(body: TTSRequest) -> TTSResponse:
    engine = TTSEngine()
    try:
        audio, sr = engine.synthesize(
            text=body.text,
            engine=body.engine,
            language=body.language,
            slow=body.slow,
            voice_id=body.voice_id,
            rate=body.rate,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"TTS failed: {exc}") from exc

    record = audio_store.save_array(audio, sr, source="tts")
    meta = AudioMeta(**record.to_dict())
    return TTSResponse(audio_id=record.id, meta=meta)
