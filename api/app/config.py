from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Voice Generator API"
    api_prefix: str = "/api"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    sample_rate: int = 44100
    max_upload_mb: int = 50

    class Config:
        env_prefix = "VG_"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
(settings.data_dir / "uploads").mkdir(exist_ok=True)
(settings.data_dir / "processed").mkdir(exist_ok=True)
(settings.data_dir / "profiles").mkdir(exist_ok=True)
