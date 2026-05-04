-- Angelora Video Studio — schema bootstrap.
-- Conventions follow angela_aitop: uuid PK with gen_random_uuid(),
-- timestamptz with now() defaults, jsonb for structured payloads.

CREATE SCHEMA IF NOT EXISTS angela_video_studio;

SET search_path TO angela_video_studio, public;

-- ============================================================
-- video_prompt_templates  — master library, seeded from code
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_video_studio.video_prompt_templates (
    name                  varchar(64)              PRIMARY KEY,
    content               text                     NOT NULL,
    default_format        varchar(32)              NOT NULL,
    default_visual_style  varchar(32)              NOT NULL,
    description           text,
    is_active             boolean                  NOT NULL DEFAULT true,
    created_at            timestamptz              NOT NULL DEFAULT now(),
    updated_at            timestamptz              NOT NULL DEFAULT now()
);

-- ============================================================
-- video_projects  — one row per source PDF
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_video_studio.video_projects (
    id                       uuid                  PRIMARY KEY DEFAULT gen_random_uuid(),
    title                    text                  NOT NULL,
    source_pdf_path          text                  NOT NULL,
    source_pdf_sha256        char(64),
    audience                 text                  NOT NULL DEFAULT 'engaged adult learners with relevant background',
    persona                  text,
    total_pages              integer               NOT NULL,
    total_estimated_minutes  numeric(6,1)          NOT NULL DEFAULT 0,
    recommended_count        integer               NOT NULL DEFAULT 0,
    alternatives             jsonb                 NOT NULL DEFAULT '[]'::jsonb,
    machine                  varchar(20),
    status                   varchar(24)           NOT NULL DEFAULT 'analyzed',
    -- planned | analyzed | generating | done | failed
    created_at               timestamptz           NOT NULL DEFAULT now(),
    updated_at               timestamptz           NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_video_projects_status      ON angela_video_studio.video_projects (status);
CREATE INDEX IF NOT EXISTS ix_video_projects_created_at  ON angela_video_studio.video_projects (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_video_projects_pdf_sha     ON angela_video_studio.video_projects (source_pdf_sha256);

-- ============================================================
-- video_segments  — one row per video to generate
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_video_studio.video_segments (
    id                  uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          uuid              NOT NULL REFERENCES angela_video_studio.video_projects(id) ON DELETE CASCADE,
    sequence            integer           NOT NULL,
    title               text,
    start_page          integer           NOT NULL,
    end_page            integer           NOT NULL,
    page_count          integer           NOT NULL,
    est_minutes         numeric(5,1)      NOT NULL,
    cognitive_load      numeric(4,2)      NOT NULL DEFAULT 0,
    cuts_mid_section    boolean           NOT NULL DEFAULT false,
    summary             jsonb             NOT NULL DEFAULT '{}'::jsonb,
    -- summary fields: learning_objectives, covers, does_not_cover,
    --                 take_home, bridge_to_next.
    status              varchar(24)       NOT NULL DEFAULT 'pending',
    -- pending | prompt_ready | submitted | generating | downloaded | qa_pass | qa_fail | regenerated
    notebooklm_job_id   text,
    notebooklm_url      text,
    output_video_path   text,
    output_video_sha256 char(64),
    qa_score            numeric(3,2),
    qa_report           jsonb,
    submitted_at        timestamptz,
    downloaded_at       timestamptz,
    created_at          timestamptz       NOT NULL DEFAULT now(),
    updated_at          timestamptz       NOT NULL DEFAULT now(),
    UNIQUE (project_id, sequence)
);

CREATE INDEX IF NOT EXISTS ix_video_segments_project_id  ON angela_video_studio.video_segments (project_id);
CREATE INDEX IF NOT EXISTS ix_video_segments_status      ON angela_video_studio.video_segments (status);
CREATE INDEX IF NOT EXISTS ix_video_segments_job_id      ON angela_video_studio.video_segments (notebooklm_job_id);

-- ============================================================
-- video_prompts  — every filled prompt + which version was used
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_video_studio.video_prompts (
    id                uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id        uuid              NOT NULL REFERENCES angela_video_studio.video_segments(id) ON DELETE CASCADE,
    template_name     varchar(64)       NOT NULL REFERENCES angela_video_studio.video_prompt_templates(name),
    notebooklm_format varchar(32)       NOT NULL,
    visual_style      varchar(32)       NOT NULL,
    target_minutes    integer           NOT NULL,
    filled_prompt     text              NOT NULL,
    version           integer           NOT NULL DEFAULT 1,
    used_at           timestamptz,
    -- set when this prompt was actually pasted into NotebookLM
    note              text,
    created_at        timestamptz       NOT NULL DEFAULT now(),
    UNIQUE (segment_id, version)
);

CREATE INDEX IF NOT EXISTS ix_video_prompts_segment_id ON angela_video_studio.video_prompts (segment_id);
CREATE INDEX IF NOT EXISTS ix_video_prompts_template   ON angela_video_studio.video_prompts (template_name);

-- ============================================================
-- updated_at triggers
-- ============================================================
CREATE OR REPLACE FUNCTION angela_video_studio.tg_set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_video_projects_updated_at  ON angela_video_studio.video_projects;
CREATE TRIGGER tg_video_projects_updated_at
    BEFORE UPDATE ON angela_video_studio.video_projects
    FOR EACH ROW EXECUTE FUNCTION angela_video_studio.tg_set_updated_at();

DROP TRIGGER IF EXISTS tg_video_segments_updated_at ON angela_video_studio.video_segments;
CREATE TRIGGER tg_video_segments_updated_at
    BEFORE UPDATE ON angela_video_studio.video_segments
    FOR EACH ROW EXECUTE FUNCTION angela_video_studio.tg_set_updated_at();

DROP TRIGGER IF EXISTS tg_video_prompt_templates_updated_at ON angela_video_studio.video_prompt_templates;
CREATE TRIGGER tg_video_prompt_templates_updated_at
    BEFORE UPDATE ON angela_video_studio.video_prompt_templates
    FOR EACH ROW EXECUTE FUNCTION angela_video_studio.tg_set_updated_at();
