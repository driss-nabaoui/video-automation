from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# Topic Schemas
class TopicCreate(BaseModel):
    niche: str = Field(..., example="Space and Astronomy")
    title_concept: str = Field(..., example="The Great Attractor: What Is Pulling Our Galaxy?")
    angle: str = Field(..., example="A cinematic documentary investigating gravitational anomalies in deep space.")
    source_references: Optional[List[Dict[str, Any]]] = []


class TopicResponse(TopicCreate):
    id: UUID
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Job Schemas
class JobCreate(BaseModel):
    topic_id: Optional[UUID] = None
    mode: str = Field(default="AUTOMATIC", pattern="^(AUTOMATIC|LOCAL_IMPORT)$")
    format: str = Field(default="LONG_FORM", pattern="^(LONG_FORM|SHORTS)$")


class JobResponse(BaseModel):
    id: UUID
    topic_id: Optional[UUID]
    mode: str
    format: str
    status: str
    progress_percentage: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Voice Synthesis Schemas
class VoiceSynthesizeRequest(BaseModel):
    job_id: UUID
    text: str
    voice: str = "en-US-ChristopherNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


class WordTimestamp(BaseModel):
    word: str
    start_time_ms: int
    end_time_ms: int


class VoiceSynthesizeResponse(BaseModel):
    audio_path: str
    duration_seconds: float
    word_count: int
    word_timestamps: List[WordTimestamp]


# Subtitle Schemas
class SubtitleBuildRequest(BaseModel):
    job_id: UUID
    word_timestamps: List[WordTimestamp]
    format: str = "LONG_FORM"  # LONG_FORM (16:9 bottom), SHORTS (9:16 center highlighted)
    font_name: str = "DejaVu Sans"
    font_size: int = 22


class SubtitleBuildResponse(BaseModel):
    ass_path: str
    srt_path: str


# Scene & Asset Schemas
class SceneSpec(BaseModel):
    scene_index: int
    narration_segment: str
    visual_description: str
    search_keywords: List[str]
    duration_seconds: float
    asset_path: Optional[str] = None
    asset_type: Optional[str] = "IMAGE"  # "IMAGE" or "VIDEO"
    transition_type: Optional[str] = "fade"
    motion_type: Optional[str] = "zoom_in"  # "zoom_in", "zoom_out", "pan_left", "pan_right"
    creator: Optional[str] = None
    license_name: Optional[str] = None
    source_url: Optional[str] = None
    attribution: Optional[str] = None
    # Hollywood Director & AI Video Extensions
    shot_type: Optional[str] = "AI_CINEMATIC"  # "AI_CINEMATIC", "ARCHIVAL_AUTHENTIC", "NASA_SCIENTIFIC", "STOCK"
    ai_prompt: Optional[str] = None
    camera_motion: Optional[str] = "slow_push_in"  # "slow_push_in", "wide_aerial", "orbital_arc", "dolly_tracking", "macro_close_up"
    sfx_cue: Optional[str] = None
    visual_lighting: Optional[str] = None


class AssetVerificationResult(BaseModel):
    is_approved: bool
    license_name: str
    is_commercial_safe: bool
    attribution_required: bool
    attribution_text: Optional[str]
    rejection_reason: Optional[str] = None


class AssetRecord(BaseModel):
    source: str  # NASA, WIKIMEDIA, PEXELS, PIXABAY, LOCAL_WINDOWS, AI_VIDEO
    external_id: Optional[str] = None
    asset_type: str  # IMAGE, VIDEO
    file_path: str
    source_url: Optional[str] = None
    creator: Optional[str] = None
    license_name: str
    license_url: Optional[str] = None
    attribution_text: Optional[str] = None
    is_commercial_safe: bool = True
    sha256_hash: str
    resolution: Optional[str] = None
    duration_seconds: Optional[float] = None


class AssetFetchRequest(BaseModel):
    job_id: UUID
    scenes: List[SceneSpec]
    format: str = "LONG_FORM"  # "LONG_FORM" (16:9) or "SHORTS" (9:16)


class AssetFetchResponse(BaseModel):
    matched_scenes: int
    scenes: List[SceneSpec] = []
    assets: List[AssetRecord]
    attributions_summary: List[str]


class AIVideoGenerateRequest(BaseModel):
    prompt: str
    camera_motion: Optional[str] = "slow_push_in"
    duration_seconds: Optional[float] = 5.0
    aspect_ratio: Optional[str] = "16:9"  # "16:9" or "9:16"
    filename_prefix: Optional[str] = "cinematic_test"


class AIVideoGenerateResponse(BaseModel):
    success: bool
    video_path: Optional[str] = None
    provider: str
    duration_seconds: float
    resolution: str
    error: Optional[str] = None


# Composition & Render Schemas
class RenderCompositeRequest(BaseModel):
    job_id: UUID
    voice_audio_path: str
    scenes: List[SceneSpec]
    subtitles_ass_path: Optional[str] = None
    background_music_path: Optional[str] = None
    format: str = "LONG_FORM"  # LONG_FORM (1920x1080), SHORTS (1080x1920)


class RenderCompositeResponse(BaseModel):
    video_path: str
    resolution: str
    duration_seconds: float
    file_size_mb: float
    qc_passed: bool
    qc_log: Dict[str, Any]
