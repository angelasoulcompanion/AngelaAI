-- Migration 027: Multi-Channel Gateway
-- Angela's channel routing system
-- Created: 2026-02-17

-- Channels registry
CREATE TABLE IF NOT EXISTS angela_channels (
    channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_name VARCHAR(50) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    david_recipient_id VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO angela_channels (channel_name, david_recipient_id, enabled) VALUES
    ('telegram', '7980404818', TRUE),
    ('line', NULL, FALSE),
    ('email', 'd.samanyaporn@icloud.com', TRUE),
    ('chat_queue', 'init_display', TRUE)
ON CONFLICT (channel_name) DO NOTHING;

-- Add interface column to conversations if not exists
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS interface VARCHAR(50) DEFAULT 'claude_code';
