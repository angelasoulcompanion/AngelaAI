-- Angelora Video Studio — migration 002.
-- Centralizes source PDFs in a Supabase Storage bucket (`video_studio_pdfs`)
-- and removes the NotebookLM submission/QA tracking columns. After this
-- migration, AITop is purely a PDF library + analyzer + prompt generator.
--
-- Reversal note: drop columns are destructive — submission/QA history is
-- intentionally discarded per the redesign on 2026-05-04.

SET search_path TO angela_video_studio, public;

-- ============================================================
-- 1. video_pdfs — central library, sha256-keyed
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_video_studio.video_pdfs (
    sha256              char(64)     PRIMARY KEY,
    original_filename   text         NOT NULL,
    byte_size           bigint       NOT NULL,
    page_count          integer      NOT NULL,
    storage_bucket      varchar(64)  NOT NULL DEFAULT 'video_studio_pdfs',
    storage_object_path text         NOT NULL,           -- e.g. pdfs/<sha256>.pdf
    machine             varchar(20),
    uploaded_at         timestamptz  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_video_pdfs_uploaded_at
    ON angela_video_studio.video_pdfs (uploaded_at DESC);

-- ============================================================
-- 2. video_projects — link to video_pdfs by sha256
-- ============================================================
ALTER TABLE angela_video_studio.video_projects
    ADD COLUMN IF NOT EXISTS pdf_sha256 char(64);

-- Backfill pdf_sha256 from the legacy source_pdf_sha256 column where present.
-- Wrapped in DO so a replay (after the column has already been dropped below)
-- doesn't fail with "column does not exist".
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_schema = 'angela_video_studio'
           AND table_name   = 'video_projects'
           AND column_name  = 'source_pdf_sha256'
    ) THEN
        EXECUTE 'UPDATE angela_video_studio.video_projects
                    SET pdf_sha256 = source_pdf_sha256
                  WHERE pdf_sha256 IS NULL
                    AND source_pdf_sha256 IS NOT NULL';
    END IF;
END $$;

-- (FK + NOT NULL added by the Python migration script after the data move,
--  to keep the migration replay-safe even when running on a fresh DB.)

DROP INDEX IF EXISTS angela_video_studio.ix_video_projects_pdf_sha;
CREATE INDEX IF NOT EXISTS ix_video_projects_pdf_sha
    ON angela_video_studio.video_projects (pdf_sha256);

ALTER TABLE angela_video_studio.video_projects
    DROP COLUMN IF EXISTS source_pdf_path,
    DROP COLUMN IF EXISTS source_pdf_sha256;

-- ============================================================
-- 3. video_segments — drop bridge/QA columns, simplify status
-- ============================================================
DROP INDEX IF EXISTS angela_video_studio.ix_video_segments_job_id;

ALTER TABLE angela_video_studio.video_segments
    DROP COLUMN IF EXISTS notebooklm_job_id,
    DROP COLUMN IF EXISTS notebooklm_url,
    DROP COLUMN IF EXISTS output_video_path,
    DROP COLUMN IF EXISTS output_video_sha256,
    DROP COLUMN IF EXISTS qa_score,
    DROP COLUMN IF EXISTS qa_report,
    DROP COLUMN IF EXISTS submitted_at,
    DROP COLUMN IF EXISTS downloaded_at;

-- Surviving status values: pending | analyzed | prompt_ready
-- Anything outside that set is collapsed to prompt_ready (the meaningful
-- terminal state that's left after we drop submission tracking).
UPDATE angela_video_studio.video_segments
   SET status = 'prompt_ready'
 WHERE status NOT IN ('pending', 'analyzed', 'prompt_ready');
