import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App & Environment
    APP_NAME: str = "VOIDORA Video Production Core"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    TZ: str = "Africa/Casablanca"

    # Persistent Storage Paths
    MEDIA_DIR: str = Field(default="/media", env="MEDIA_DIR")

    # Database Configuration
    DB_HOST: str = Field(default="postgres", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="n8n_production", env="DB_NAME")
    DB_USER: str = Field(default="n8n_dbuser", env="DB_USER")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    DB_SCHEMA: str = "voidora_prod"

    # API Keys & Third-Party
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    PEXELS_API_KEY: str = Field(default="", env="PEXELS_API_KEY")
    PIXABAY_API_KEY: str = Field(default="", env="PIXABAY_API_KEY")

    # AI Video Generation Engine (Kling, Runway, Fal.ai, Luma)
    AI_VIDEO_PROVIDER: str = Field(default="auto", env="AI_VIDEO_PROVIDER")  # "auto", "fal", "runway", "kling", "luma"
    FAL_KEY: str = Field(default="", env="FAL_KEY")
    RUNWAY_API_KEY: str = Field(default="", env="RUNWAY_API_KEY")
    KLING_API_KEY: str = Field(default="", env="KLING_API_KEY")
    LUMA_API_KEY: str = Field(default="", env="LUMA_API_KEY")
    MINIMAX_API_KEY: str = Field(default="", env="MINIMAX_API_KEY")
    AI_VIDEO_ENABLED: bool = Field(default=True, env="AI_VIDEO_ENABLED")
    AI_VIDEO_DEFAULT_DURATION: int = Field(default=5, env="AI_VIDEO_DEFAULT_DURATION")

    # FFmpeg Throttling & Quality Defaults
    FFMPEG_MAX_THREADS: int = 3
    FFMPEG_PRESET: str = "veryfast"
    FFMPEG_CRF: int = 22
    AUDIO_DUCK_DB: float = -18.0

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def raw_inbox(self) -> Path:
        p = Path(self.MEDIA_DIR) / "01_raw_inbox"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def audio_narrations(self) -> Path:
        p = Path(self.MEDIA_DIR) / "02_audio_narrations"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def music_sfx(self) -> Path:
        p = Path(self.MEDIA_DIR) / "03_music_sfx"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def visual_assets(self) -> Path:
        p = Path(self.MEDIA_DIR) / "04_visual_assets"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def subtitles(self) -> Path:
        p = Path(self.MEDIA_DIR) / "05_subtitles"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def rendered_output(self) -> Path:
        p = Path(self.MEDIA_DIR) / "06_rendered_output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumbnails(self) -> Path:
        p = Path(self.MEDIA_DIR) / "07_thumbnails"
        p.mkdir(parents=True, exist_ok=True)
        return p

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
