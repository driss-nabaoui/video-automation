-- VOIDORA Video Automation Engine - Production Database Schema
-- Schema: voidora_prod (Isolated from n8n internal tables)

CREATE SCHEMA IF NOT EXISTS voidora_prod;

-- 1. Topics and Research Sources
CREATE TABLE IF NOT EXISTS voidora_prod.topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche VARCHAR(64) NOT NULL,
    title_concept VARCHAR(255) NOT NULL,
    angle TEXT NOT NULL,
    source_references JSONB DEFAULT '[]'::jsonb,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Production Jobs
CREATE TABLE IF NOT EXISTS voidora_prod.production_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES voidora_prod.topics(id) ON DELETE SET NULL,
    mode VARCHAR(16) NOT NULL CHECK (mode IN ('AUTOMATIC', 'LOCAL_IMPORT')),
    format VARCHAR(16) NOT NULL CHECK (format IN ('LONG_FORM', 'SHORTS')),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    progress_percentage INT DEFAULT 0,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    lock_token VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Scripts & Narration Text
CREATE TABLE IF NOT EXISTS voidora_prod.scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    raw_script TEXT NOT NULL,
    cleaned_narration TEXT NOT NULL,
    estimated_duration_seconds INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Scene-by-Scene Production Plan
CREATE TABLE IF NOT EXISTS voidora_prod.scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    scene_index INT NOT NULL,
    narration_segment TEXT NOT NULL,
    visual_description TEXT NOT NULL,
    search_keywords TEXT[] DEFAULT '{}',
    start_time_seconds NUMERIC(7,3),
    end_time_seconds NUMERIC(7,3),
    asset_path TEXT,
    transition_type VARCHAR(32) DEFAULT 'fade'
);

-- 5. Media Asset Ledger
CREATE TABLE IF NOT EXISTS voidora_prod.media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    source VARCHAR(32) NOT NULL,
    external_id VARCHAR(128),
    asset_type VARCHAR(16) NOT NULL CHECK (asset_type IN ('VIDEO', 'IMAGE', 'AUDIO', 'SFX')),
    file_path TEXT NOT NULL,
    license_info TEXT,
    resolution VARCHAR(16),
    duration_seconds NUMERIC(7,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Master Rendered Video Output
CREATE TABLE IF NOT EXISTS voidora_prod.rendered_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL UNIQUE REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    resolution VARCHAR(16) NOT NULL,
    fps INT NOT NULL DEFAULT 30,
    duration_seconds NUMERIC(7,2) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    qc_passed BOOLEAN DEFAULT FALSE,
    qc_log JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Thumbnails
CREATE TABLE IF NOT EXISTS voidora_prod.thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    resolution VARCHAR(16) NOT NULL DEFAULT '1280x720',
    prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. YouTube Upload Ledger
CREATE TABLE IF NOT EXISTS voidora_prod.youtube_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    youtube_video_id VARCHAR(64) UNIQUE NOT NULL,
    privacy_status VARCHAR(16) NOT NULL DEFAULT 'private',
    title VARCHAR(100) NOT NULL,
    description TEXT,
    tags TEXT[],
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. System Logs & Execution Traces
CREATE TABLE IF NOT EXISTS voidora_prod.system_logs (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID REFERENCES voidora_prod.production_jobs(id) ON DELETE CASCADE,
    level VARCHAR(16) NOT NULL DEFAULT 'INFO',
    stage VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON voidora_prod.production_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scenes_job ON voidora_prod.scenes(job_id, scene_index);
CREATE INDEX IF NOT EXISTS idx_logs_job ON voidora_prod.system_logs(job_id, created_at);
CREATE INDEX IF NOT EXISTS idx_media_job ON voidora_prod.media_assets(job_id);
