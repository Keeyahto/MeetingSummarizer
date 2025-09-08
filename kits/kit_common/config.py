from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv
import os


load_dotenv(override=False)


class Settings(BaseSettings):
    # General
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    DATA_DIR: str = "./data"
    MODELS_CACHE_DIR: str = "./models"
    PROCESS_MODE: str = "async"  # async | sync

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    RQ_JOB_TIMEOUT: int = 1800  # 30 минут timeout для задач

    # ASR
    ASR_MODEL: str = "base"  # Изменено с large-v3 на base для скорости
    ASR_LANGUAGE: str = "auto"
    ASR_BATCH_SIZE: int = 32  # Увеличено для скорости
    ASR_BEAM_SIZE: int = 1  # Уменьшено для скорости
    ASR_COMPUTE: str = "int8_float16"  # Более быстрый режим
    ASR_VAD: str = "whisperx"  # whisperx | webrtc
    MAX_AUDIO_MIN: int = 90

    # Diarization
    DIARIZATION: str = "on"  # on | off
    HF_TOKEN: str | None = None

    # LLM
    LLM_BACKEND: str = "openai"
    OPENAI_BASE_URL: str = "http://localhost:1234/v1"
    OPENAI_API_KEY: str = "dummy"
    LLM_MODEL: str = "qwen/qwen3-4b-thinking-2507"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 8096

    # Export / flags
    FAST_MODE: bool = True  # Включен быстрый режим по умолчанию
    EXPORT_MD_MAX_CHARS: int = 30000

    # CORS
    CORS_ORIGINS: str = "*"

    model_config = ConfigDict(env_file=".env")


settings = Settings()  # load once

# Ensure base directories exist
Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.MODELS_CACHE_DIR).mkdir(parents=True, exist_ok=True)

