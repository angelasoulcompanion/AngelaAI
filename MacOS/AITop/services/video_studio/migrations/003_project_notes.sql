-- Angelora Video Studio — migration 003.
-- Adds an optional free-form `notes` field to projects so users can attach
-- arbitrary context (audience tweaks, todos, NotebookLM submission notes).

SET search_path TO angela_video_studio, public;

ALTER TABLE angela_video_studio.video_projects
    ADD COLUMN IF NOT EXISTS notes text;
