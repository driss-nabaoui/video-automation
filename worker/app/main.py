import os
import shutil
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db, engine
from app import models, schemas
from app.services.voice_engine import voice_engine
from app.services.subtitle_engine import subtitle_engine
from app.services.script_engine import script_engine
from app.services.compositor_engine import compositor_engine
from app.services.qc_engine import qc_engine
from app.services.asset_engine import asset_engine
from app.services.ai_video_engine import ai_video_engine

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Asynchronous Video Production & Assembly Core for VOIDORA YouTube Channel"
)


@app.get("/health")
async def health_check():
    """System health check and dependency validation."""
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")

    # Check database connectivity
    db_connected = False
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "ok" if (ffmpeg_path and db_connected) else "degraded",
        "service": "voidora-video-worker",
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "ffmpeg_available": ffmpeg_path is not None,
            "ffmpeg_path": ffmpeg_path,
            "ffprobe_available": ffprobe_path is not None,
            "database_connected": db_connected,
            "media_mounted": os.path.isdir(settings.MEDIA_DIR)
        },
        "storage": {
            "narrations_dir": str(settings.audio_narrations),
            "rendered_dir": str(settings.rendered_output),
            "subtitles_dir": str(settings.subtitles)
        }
    }


# ==========================================
# 1. Job Management Endpoints
# ==========================================

@app.post("/api/v1/jobs/create", response_model=schemas.JobResponse)
async def create_job(job_in: schemas.JobCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new production job ledger in voidora_prod.production_jobs."""
    new_job = models.ProductionJob(
        topic_id=job_in.topic_id,
        mode=job_in.mode,
        format=job_in.format,
        status="INITIALIZED",
        progress_percentage=0
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    return new_job


@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobResponse)
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves current job status and progress."""
    stmt = select(models.ProductionJob).where(models.ProductionJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ==========================================
# 2. Script & Research Generation
# ==========================================

@app.post("/api/v1/script/generate")
async def generate_script(
    niche: str = "Space and Astronomy",
    title_concept: str = "The Great Attractor",
    target_format: str = "LONG_FORM"
):
    """Generates an original documentary script and structured scenes."""
    plan = await script_engine.generate_documentary_plan(
        niche=niche,
        title_concept=title_concept,
        target_format=target_format
    )
    return {
        "status": "success",
        "plan": plan
    }


# ==========================================
# 3. Voice Synthesis (Edge-TTS Neural)
# ==========================================

@app.post("/api/v1/voice/synthesize", response_model=schemas.VoiceSynthesizeResponse)
async def synthesize_voice(req: schemas.VoiceSynthesizeRequest):
    """Synthesizes high-fidelity voiceover with word-level timestamps."""
    filename = f"narration_{req.job_id}.mp3"
    audio_path, duration, word_timestamps = await voice_engine.synthesize(
        text=req.text,
        output_filename=filename,
        voice=req.voice,
        rate=req.rate,
        pitch=req.pitch
    )

    return schemas.VoiceSynthesizeResponse(
        audio_path=audio_path,
        duration_seconds=duration,
        word_count=len(word_timestamps),
        word_timestamps=word_timestamps
    )


# ==========================================
# 4. Subtitle Generation (.ass / .srt)
# ==========================================

@app.post("/api/v1/subtitles/build", response_model=schemas.SubtitleBuildResponse)
async def build_subtitles(req: schemas.SubtitleBuildRequest):
    """Builds synchronized .ass and .srt files from word timestamps."""
    basename = f"subs_{req.job_id}_{req.format.lower()}"
    ass_path, srt_path = subtitle_engine.build_subtitles(
        word_timestamps=req.word_timestamps,
        output_basename=basename,
        video_format=req.format
    )
    return schemas.SubtitleBuildResponse(
        ass_path=ass_path,
        srt_path=srt_path
    )


# ==========================================
# 5. Visual Asset Acquisition & Copyright Audit
# ==========================================

@app.post("/api/v1/assets/acquire", response_model=schemas.AssetFetchResponse)
async def acquire_visual_assets(req: schemas.AssetFetchRequest, db: AsyncSession = Depends(get_db)):
    """Acquires copyright-safe visuals for scenes, verifies rights, and records in database."""
    updated_scenes, asset_records, attributions = await asset_engine.acquire_assets_for_scenes(
        scenes=req.scenes,
        video_format=req.format
    )

    # Persist in voidora_prod.media_assets with deduplication
    for rec in asset_records:
        stmt = select(models.MediaAsset).where(models.MediaAsset.sha256_hash == rec.sha256_hash)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            new_asset = models.MediaAsset(
                job_id=req.job_id,
                source=rec.source,
                external_id=rec.external_id,
                asset_type=rec.asset_type,
                file_path=rec.file_path,
                source_url=rec.source_url,
                creator=rec.creator,
                license_name=rec.license_name,
                license_url=rec.license_url,
                attribution_text=rec.attribution_text,
                is_commercial_safe=rec.is_commercial_safe,
                sha256_hash=rec.sha256_hash,
                validation_status="VERIFIED_SAFE"
            )
            db.add(new_asset)

    await db.commit()

    return schemas.AssetFetchResponse(
        matched_scenes=len(updated_scenes),
        scenes=updated_scenes,
        assets=asset_records,
        attributions_summary=attributions
    )


@app.post("/api/v1/assets/generate_ai_video", response_model=schemas.AIVideoGenerateResponse)
async def generate_ai_video_clip(req: schemas.AIVideoGenerateRequest):
    """Generates a standalone Hollywood-grade AI cinematic video clip."""
    vid_path, provider, err = await ai_video_engine.generate_cinematic_shot(
        prompt=req.prompt,
        camera_motion=req.camera_motion or "slow_push_in",
        duration_seconds=req.duration_seconds or 5.0,
        aspect_ratio=req.aspect_ratio or "16:9",
        filename_prefix=req.filename_prefix or "test_ai"
    )
    if vid_path and vid_path.is_file():
        return schemas.AIVideoGenerateResponse(
            success=True,
            video_path=str(vid_path),
            provider=provider,
            duration_seconds=req.duration_seconds or 5.0,
            resolution="1920x1080" if req.aspect_ratio == "16:9" else "1080x1920"
        )
    return schemas.AIVideoGenerateResponse(
        success=False,
        provider=provider,
        duration_seconds=0.0,
        resolution="unknown",
        error=err or "Video generation failed"
    )


# ==========================================
# 6. Video Composition & Rendering (FFmpeg)
# ==========================================

@app.post("/api/v1/render/composite", response_model=schemas.RenderCompositeResponse)
async def composite_video(req: schemas.RenderCompositeRequest, db: AsyncSession = Depends(get_db)):
    """Renders the master composite video with burned subtitles and ducked audio."""
    try:
        video_path, qc_passed, qc_report = await asyncio.to_thread(
            compositor_engine.composite_video,
            job_id=str(req.job_id),
            voice_audio_path=req.voice_audio_path,
            scenes=req.scenes,
            subtitles_ass_path=req.subtitles_ass_path,
            background_music_path=req.background_music_path,
            video_format=req.format
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {err}")

    # Record or update in rendered_videos database table
    file_size_bytes = os.path.getsize(video_path) if os.path.isfile(video_path) else 0
    duration_s = qc_report.get("duration_seconds", 0.0)

    stmt_v = select(models.RenderedVideo).where(models.RenderedVideo.job_id == req.job_id)
    res_v = await db.execute(stmt_v)
    rendered_rec = res_v.scalar_one_or_none()

    if rendered_rec:
        rendered_rec.file_path = video_path
        rendered_rec.resolution = qc_report.get("resolution", "1920x1080")
        rendered_rec.fps = 30
        rendered_rec.duration_seconds = duration_s
        rendered_rec.file_size_bytes = file_size_bytes
        rendered_rec.qc_passed = qc_passed
        rendered_rec.qc_log = qc_report
    else:
        rendered_rec = models.RenderedVideo(
            job_id=req.job_id,
            file_path=video_path,
            resolution=qc_report.get("resolution", "1920x1080"),
            fps=30,
            duration_seconds=duration_s,
            file_size_bytes=file_size_bytes,
            qc_passed=qc_passed,
            qc_log=qc_report
        )
        db.add(rendered_rec)

    # Update job status
    stmt = select(models.ProductionJob).where(models.ProductionJob.id == req.job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if job:
        job.status = "COMPLETED" if qc_passed else "QC_FAILED"
        job.progress_percentage = 100

    await db.commit()

    return schemas.RenderCompositeResponse(
        video_path=video_path,
        resolution=qc_report.get("resolution", "1920x1080"),
        duration_seconds=duration_s,
        file_size_mb=qc_report.get("file_size_mb", 0.0),
        qc_passed=qc_passed,
        qc_log=qc_report
    )


# ==========================================
# 6. Quality Control Inspector
# ==========================================

@app.post("/api/v1/qc/inspect")
async def inspect_video_qc(video_path: str, format: str = "LONG_FORM"):
    """Standalone inspection of any video file using ffprobe."""
    passed, report = qc_engine.inspect_video(video_path, expected_format=format)
    return {
        "qc_passed": passed,
        "report": report
    }
