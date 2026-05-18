-- Angelora Video Studio — migration 004.
-- Adds an explicit "user marked this segment as done" flag, separate from the
-- pipeline `status` column (which only tracks generator state, not whether
-- the user has actually shipped/used the resulting video).
--
-- NULL  = not done yet
-- value = the moment the user ticked the checkbox (audit + sort by recency)

SET search_path TO angela_video_studio, public;

ALTER TABLE angela_video_studio.video_segments
    ADD COLUMN IF NOT EXISTS completed_at timestamptz;

CREATE INDEX IF NOT EXISTS ix_video_segments_completed_at
    ON angela_video_studio.video_segments (completed_at)
    WHERE completed_at IS NOT NULL;
