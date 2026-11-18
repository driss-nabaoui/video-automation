import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, BigInteger, Numeric,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche = Column(String(64), nullable=False)
    title_concept = Column(String(255), nullable=False)
    angle = Column(Text, nullable=False)
    source_references = Column(JSONB, default=list)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    jobs = relationship("ProductionJob", back_populates="topic")


class ProductionJob(Base):
    __tablename__ = "production_jobs"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.topics.id", ondelete="SET NULL"), nullable=True)
    mode = Column(String(16), nullable=False)  # AUTOMATIC, LOCAL_IMPORT
    format = Column(String(16), nullable=False)  # LONG_FORM, SHORTS
    status = Column(String(32), nullable=False, default="PENDING")
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    lock_token = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    topic = relationship("Topic", back_populates="jobs")
    script = relationship("Script", back_populates="job", uselist=False, cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="job", cascade="all, delete-orphan", order_by="Scene.scene_index")
    rendered_video = relationship("RenderedVideo", back_populates="job", uselist=False, cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="job", cascade="all, delete-orphan")
    youtube_upload = relationship("YouTubeUpload", back_populates="job", uselist=False, cascade="all, delete-orphan")


class Script(Base):
    __tablename__ = "scripts"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    raw_script = Column(Text, nullable=False)
    cleaned_narration = Column(Text, nullable=False)
    estimated_duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("ProductionJob", back_populates="script")


class Scene(Base):
    __tablename__ = "scenes"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=False)
    scene_index = Column(Integer, nullable=False)
    narration_segment = Column(Text, nullable=False)
    visual_description = Column(Text, nullable=False)
    search_keywords = Column(ARRAY(Text), default=list)
    start_time_seconds = Column(Numeric(7, 3), nullable=True)
    end_time_seconds = Column(Numeric(7, 3), nullable=True)
    asset_path = Column(Text, nullable=True)
    transition_type = Column(String(32), default="fade")

    job = relationship("ProductionJob", back_populates="scenes")


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(32), nullable=False)  # NASA, WIKIMEDIA, PEXELS, PIXABAY, LOCAL_WINDOWS
    external_id = Column(String(128), nullable=True)
    asset_type = Column(String(16), nullable=False)  # VIDEO, IMAGE, AUDIO, SFX
    file_path = Column(Text, nullable=False)
    license_info = Column(Text, nullable=True)
    resolution = Column(String(16), nullable=True)
    duration_seconds = Column(Numeric(7, 2), nullable=True)
    source_url = Column(Text, nullable=True)
    creator = Column(String(255), nullable=True)
    license_name = Column(String(64), nullable=True)
    license_url = Column(Text, nullable=True)
    attribution_text = Column(Text, nullable=True)
    is_commercial_safe = Column(Boolean, default=True)
    sha256_hash = Column(String(64), nullable=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.scenes.id", ondelete="SET NULL"), nullable=True)
    validation_status = Column(String(32), default="VERIFIED_SAFE")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("ProductionJob", back_populates="media_assets")


class RenderedVideo(Base):
    __tablename__ = "rendered_videos"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    file_path = Column(Text, nullable=False)
    resolution = Column(String(16), nullable=False)
    fps = Column(Integer, default=30)
    duration_seconds = Column(Numeric(7, 2), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    qc_passed = Column(Boolean, default=False)
    qc_log = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("ProductionJob", back_populates="rendered_video")


class Thumbnail(Base):
    __tablename__ = "thumbnails"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    resolution = Column(String(16), default="1280x720")
    prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class YouTubeUpload(Base):
    __tablename__ = "youtube_uploads"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    youtube_video_id = Column(String(64), unique=True, nullable=False)
    privacy_status = Column(String(16), default="private")
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), default=list)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

    job = relationship("ProductionJob", back_populates="youtube_upload")


class SystemLog(Base):
    __tablename__ = "system_logs"
    __table_args__ = {"schema": "voidora_prod"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("voidora_prod.production_jobs.id", ondelete="CASCADE"), nullable=True)
    level = Column(String(16), default="INFO")
    stage = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    log_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
