-- ============================================================================
-- MEETING MANAGER DATABASE SCHEMA
-- Created: 2025-11-19
-- Database: MeetingManager
-- PostgreSQL 14+
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. PARTICIPANTS (People/Contacts)
-- ============================================================================
CREATE TABLE participants (
    participant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Info
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    job_title VARCHAR(200),
    department VARCHAR(100),
    company VARCHAR(200),

    -- Profile
    avatar_url TEXT,
    notes TEXT,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete
);

CREATE INDEX idx_participants_email ON participants(email);
CREATE INDEX idx_participants_name ON participants(full_name);
CREATE INDEX idx_participants_active ON participants(is_active) WHERE is_active = true;

-- ============================================================================
-- 2. MEETINGS (Core Table)
-- ============================================================================
CREATE TABLE meetings (
    meeting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Info
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Scheduling
    meeting_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    duration_minutes INTEGER,  -- Calculated or manual
    timezone VARCHAR(50) DEFAULT 'Asia/Bangkok',

    -- Location
    location VARCHAR(300),
    is_virtual BOOLEAN DEFAULT false,
    meeting_link TEXT,  -- Zoom, Teams, etc.

    -- Organization
    meeting_type VARCHAR(50),  -- 'standup', '1-on-1', 'review', 'planning', etc.
    status VARCHAR(50) DEFAULT 'scheduled',  -- 'scheduled', 'in_progress', 'completed', 'cancelled'

    -- Organizer
    organizer_id UUID REFERENCES participants(participant_id),

    -- Rich Content
    agenda TEXT,  -- Meeting agenda/outline
    objectives TEXT,  -- Meeting goals

    -- Metadata
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern VARCHAR(100),  -- 'daily', 'weekly', 'monthly', 'custom'
    parent_meeting_id UUID REFERENCES meetings(meeting_id),  -- For recurring meetings

    -- Search Optimization
    search_vector tsvector,  -- Full-text search

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Completion
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT
);

CREATE INDEX idx_meetings_date ON meetings(meeting_date DESC);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_organizer ON meetings(organizer_id);
CREATE INDEX idx_meetings_type ON meetings(meeting_type);
CREATE INDEX idx_meetings_search ON meetings USING gin(search_vector);

-- ============================================================================
-- 3. MEETING_PARTICIPANTS (Junction Table)
-- ============================================================================
CREATE TABLE meeting_participants (
    meeting_participant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(participant_id),

    -- Role in Meeting
    role VARCHAR(50) DEFAULT 'attendee',  -- 'organizer', 'attendee', 'optional', 'presenter'

    -- RSVP
    rsvp_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'accepted', 'declined', 'tentative'
    rsvp_at TIMESTAMP,

    -- Attendance
    attended BOOLEAN,
    joined_at TIMESTAMP,
    left_at TIMESTAMP,

    -- Notes
    participant_notes TEXT,  -- Private notes for this participant

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(meeting_id, participant_id)
);

CREATE INDEX idx_meeting_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX idx_meeting_participants_participant ON meeting_participants(participant_id);
CREATE INDEX idx_meeting_participants_rsvp ON meeting_participants(rsvp_status);

-- ============================================================================
-- 4. DOCUMENTS (File Attachments)
-- ============================================================================
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,

    -- File Info
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,  -- User's original filename
    file_path TEXT NOT NULL,  -- Relative path from storage root
    file_size BIGINT NOT NULL,  -- Size in bytes
    mime_type VARCHAR(100),
    file_extension VARCHAR(10),

    -- Document Metadata
    title VARCHAR(500),  -- Optional user-friendly title
    description TEXT,
    document_type VARCHAR(50),  -- 'agenda', 'presentation', 'report', 'minutes', 'other'

    -- Organization
    display_order INTEGER DEFAULT 0,  -- For custom sorting

    -- Upload Info
    uploaded_by UUID REFERENCES participants(participant_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Version Control (Optional)
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES documents(document_id),

    -- Access
    is_public BOOLEAN DEFAULT false,
    download_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    -- Checksum for integrity
    checksum VARCHAR(64),  -- SHA-256 hash

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_documents_meeting ON documents(meeting_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);

-- ============================================================================
-- 5. MEETING_NOTES (Meeting Minutes/Notes)
-- ============================================================================
CREATE TABLE meeting_notes (
    note_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,

    -- Content
    note_type VARCHAR(50) DEFAULT 'general',  -- 'general', 'decision', 'discussion', 'summary'
    title VARCHAR(300),
    content TEXT NOT NULL,

    -- Rich Text Format
    format VARCHAR(20) DEFAULT 'markdown',  -- 'markdown', 'html', 'plain'

    -- Organization
    section VARCHAR(100),  -- 'Opening', 'Discussion', 'Decisions', 'Next Steps'
    display_order INTEGER DEFAULT 0,

    -- Author
    created_by UUID REFERENCES participants(participant_id),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_meeting_notes_meeting ON meeting_notes(meeting_id);
CREATE INDEX idx_meeting_notes_type ON meeting_notes(note_type);
CREATE INDEX idx_meeting_notes_section ON meeting_notes(section);

-- ============================================================================
-- 6. ACTION_ITEMS (Tasks/Follow-ups from Meetings)
-- ============================================================================
CREATE TABLE action_items (
    action_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,

    -- Task Details
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Assignment
    assigned_to UUID REFERENCES participants(participant_id),
    assigned_by UUID REFERENCES participants(participant_id),

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'cancelled', 'blocked'
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'

    -- Deadlines
    due_date DATE,
    completed_at TIMESTAMP,

    -- Progress
    progress_percentage INTEGER DEFAULT 0,  -- 0-100

    -- Notes
    completion_notes TEXT,
    blocker_notes TEXT,  -- If status = 'blocked'

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX idx_action_items_assigned_to ON action_items(assigned_to);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_due_date ON action_items(due_date);
CREATE INDEX idx_action_items_priority ON action_items(priority);

-- ============================================================================
-- 7. TAGS (Categorization)
-- ============================================================================
CREATE TABLE tags (
    tag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    tag_name VARCHAR(100) NOT NULL UNIQUE,
    tag_color VARCHAR(7),  -- Hex color code, e.g., '#FF5733'
    description TEXT,

    -- Usage Stats
    usage_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_name ON tags(tag_name);

-- ============================================================================
-- 8. MEETING_TAGS (Junction Table)
-- ============================================================================
CREATE TABLE meeting_tags (
    meeting_tag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(meeting_id, tag_id)
);

CREATE INDEX idx_meeting_tags_meeting ON meeting_tags(meeting_id);
CREATE INDEX idx_meeting_tags_tag ON meeting_tags(tag_id);

-- ============================================================================
-- 9. MEETING_RELATIONSHIPS (Link Related Meetings)
-- ============================================================================
CREATE TABLE meeting_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    related_meeting_id UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,

    relationship_type VARCHAR(50),  -- 'follow_up', 'prerequisite', 'related', 'duplicate'
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(meeting_id, related_meeting_id)
);

CREATE INDEX idx_meeting_relationships_meeting ON meeting_relationships(meeting_id);
CREATE INDEX idx_meeting_relationships_related ON meeting_relationships(related_meeting_id);

-- ============================================================================
-- 10. AUDIT_LOG (Track Changes)
-- ============================================================================
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Entity
    entity_type VARCHAR(50) NOT NULL,  -- 'meeting', 'document', 'action_item', etc.
    entity_id UUID NOT NULL,

    -- Action
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'restore'

    -- User
    performed_by UUID REFERENCES participants(participant_id),

    -- Changes
    old_values JSONB,
    new_values JSONB,

    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_performed_by ON audit_log(performed_by);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active Meetings with Participant Count
CREATE VIEW active_meetings_summary AS
SELECT
    m.meeting_id,
    m.title,
    m.meeting_date,
    m.start_time,
    m.end_time,
    m.status,
    m.location,
    COUNT(DISTINCT mp.participant_id) as participant_count,
    COUNT(DISTINCT d.document_id) as document_count,
    COUNT(DISTINCT ai.action_item_id) as action_item_count,
    COUNT(DISTINCT CASE WHEN ai.status = 'completed' THEN ai.action_item_id END) as completed_actions
FROM meetings m
LEFT JOIN meeting_participants mp ON m.meeting_id = mp.meeting_id
LEFT JOIN documents d ON m.meeting_id = d.meeting_id AND d.deleted_at IS NULL
LEFT JOIN action_items ai ON m.meeting_id = ai.meeting_id AND ai.deleted_at IS NULL
WHERE m.deleted_at IS NULL
GROUP BY m.meeting_id;

-- Upcoming Meetings (Next 30 Days)
CREATE VIEW upcoming_meetings AS
SELECT
    m.*,
    p.full_name as organizer_name,
    COUNT(DISTINCT mp.participant_id) as participant_count
FROM meetings m
LEFT JOIN participants p ON m.organizer_id = p.participant_id
LEFT JOIN meeting_participants mp ON m.meeting_id = mp.meeting_id
WHERE m.deleted_at IS NULL
  AND m.status = 'scheduled'
  AND m.meeting_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
GROUP BY m.meeting_id, p.full_name
ORDER BY m.meeting_date, m.start_time;

-- Pending Action Items Summary
CREATE VIEW pending_actions_summary AS
SELECT
    ai.*,
    m.title as meeting_title,
    m.meeting_date,
    p.full_name as assigned_to_name
FROM action_items ai
LEFT JOIN meetings m ON ai.meeting_id = m.meeting_id
LEFT JOIN participants p ON ai.assigned_to = p.participant_id
WHERE ai.deleted_at IS NULL
  AND ai.status IN ('pending', 'in_progress')
ORDER BY ai.due_date NULLS LAST, ai.priority DESC;

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATE
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_participants_updated_at BEFORE UPDATE ON participants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_action_items_updated_at BEFORE UPDATE ON action_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_notes_updated_at BEFORE UPDATE ON meeting_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update tag usage count
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tags SET usage_count = usage_count + 1 WHERE tag_id = NEW.tag_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tags SET usage_count = usage_count - 1 WHERE tag_id = OLD.tag_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tag_count_on_insert AFTER INSERT ON meeting_tags
    FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();

CREATE TRIGGER update_tag_count_on_delete AFTER DELETE ON meeting_tags
    FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();

-- ============================================================================
-- INITIAL DATA / SEED DATA
-- ============================================================================

-- Insert default participant (David)
INSERT INTO participants (full_name, email, job_title, company, is_active)
VALUES ('David Samanyaporn', 'david@example.com', 'Developer', 'Self', true)
ON CONFLICT (email) DO NOTHING;

-- Insert default tags
INSERT INTO tags (tag_name, tag_color, description) VALUES
    ('Planning', '#3B82F6', 'Strategic planning meetings'),
    ('Review', '#10B981', 'Review and retrospective meetings'),
    ('Standup', '#F59E0B', 'Daily standup meetings'),
    ('1-on-1', '#8B5CF6', 'One-on-one meetings'),
    ('Sprint', '#EF4444', 'Sprint-related meetings'),
    ('Q4', '#06B6D4', 'Q4 related topics'),
    ('Strategy', '#EC4899', 'Strategic discussions')
ON CONFLICT (tag_name) DO NOTHING;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ MeetingManager database schema created successfully!';
    RAISE NOTICE '📊 Tables created: 10';
    RAISE NOTICE '👁️  Views created: 3';
    RAISE NOTICE '⚡ Triggers created: 6';
    RAISE NOTICE '🏷️  Default tags: 7';
    RAISE NOTICE '💜 Ready to use!';
END $$;
