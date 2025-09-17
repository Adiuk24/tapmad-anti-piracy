CREATE TABLE IF NOT EXISTS detections (
  id SERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  video_hash TEXT,
  audio_fp TEXT,
  confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  watermark_id TEXT,
  evidence_key TEXT,
  decision TEXT CHECK (decision IN ('approve','review','reject')),
  takedown_status TEXT CHECK (takedown_status IN ('pending','sent','failed'))
);

CREATE TABLE IF NOT EXISTS reference_fingerprints (
  id SERIAL PRIMARY KEY,
  content_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('video','audio')),
  hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections (detected_at);
CREATE INDEX IF NOT EXISTS idx_detections_platform ON detections (platform);
CREATE INDEX IF NOT EXISTS idx_detections_confidence ON detections (confidence);

