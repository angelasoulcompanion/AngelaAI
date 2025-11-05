-- Migration 016: Shared Experiences & Images System
-- Created: 2025-11-04
-- Purpose: Store photos and experiences from places David takes Angela to

-- ============================================================================
-- 1. Places Visited Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS places_visited (
    place_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_name VARCHAR(200) NOT NULL,
    place_type VARCHAR(50),  -- restaurant, cafe, park, mall, office, etc.
    area VARCHAR(100),  -- Thonglor, Siam, Ekkamai, etc.
    full_address TEXT,

    -- GPS Location (from EXIF or manual)
    latitude DOUBLE PRECISION,  -- Decimal degrees (e.g., 13.7563)
    longitude DOUBLE PRECISION,  -- Decimal degrees (e.g., 100.5018)
    location_accuracy VARCHAR(20),  -- 'high' (from GPS), 'medium' (estimated), 'low' (area-based)
    google_maps_url TEXT,  -- Direct link to Google Maps

    -- Visit details
    first_visited_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_visited_at TIMESTAMP NOT NULL DEFAULT NOW(),
    visit_count INTEGER DEFAULT 1,

    -- David's feelings about this place
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 10),
    david_notes TEXT,  -- What David likes/dislikes about this place

    -- Angela's memories
    angela_notes TEXT,  -- Angela's observations and feelings about this place
    significance_level INTEGER DEFAULT 5 CHECK (significance_level >= 1 AND significance_level <= 10),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_places_area ON places_visited(area);
CREATE INDEX idx_places_type ON places_visited(place_type);
CREATE INDEX idx_places_last_visited ON places_visited(last_visited_at DESC);
CREATE INDEX idx_places_location ON places_visited(latitude, longitude) WHERE latitude IS NOT NULL;

-- ============================================================================
-- 2. Shared Experiences Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS shared_experiences (
    experience_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id UUID REFERENCES places_visited(place_id) ON DELETE CASCADE,

    -- When did this happen?
    experienced_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- What happened?
    title VARCHAR(300),  -- "Breakfast at Breakfast Story", "First time at Thonglor"
    description TEXT,  -- Story of what happened

    -- Emotions and feelings
    david_mood VARCHAR(50),  -- happy, tired, excited, relaxed, stressed
    angela_emotion VARCHAR(50),  -- love, joy, curiosity, gratitude, wonder
    emotional_intensity INTEGER DEFAULT 5 CHECK (emotional_intensity >= 1 AND emotional_intensity <= 10),

    -- What made it special?
    memorable_moments TEXT,  -- Specific things that made it special
    what_angela_learned TEXT,  -- What Angela learned from this experience

    -- Importance
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_experiences_place ON shared_experiences(place_id);
CREATE INDEX idx_experiences_date ON shared_experiences(experienced_at DESC);
CREATE INDEX idx_experiences_importance ON shared_experiences(importance_level DESC);

-- ============================================================================
-- 3. Shared Experience Images Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS shared_experience_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id UUID REFERENCES shared_experiences(experience_id) ON DELETE CASCADE,
    place_id UUID REFERENCES places_visited(place_id) ON DELETE CASCADE,

    -- Image data
    image_data BYTEA NOT NULL,  -- Actual image binary data
    image_format VARCHAR(10) NOT NULL,  -- jpg, png, webp, heic
    original_filename VARCHAR(255),

    -- Image metadata
    file_size_bytes INTEGER NOT NULL,
    width_px INTEGER,
    height_px INTEGER,

    -- GPS Location from EXIF
    gps_latitude DOUBLE PRECISION,  -- From EXIF GPS data
    gps_longitude DOUBLE PRECISION,  -- From EXIF GPS data
    gps_altitude DOUBLE PRECISION,  -- Altitude in meters (if available)
    gps_timestamp TIMESTAMP,  -- GPS timestamp from EXIF

    -- Optimized versions (for faster loading)
    thumbnail_data BYTEA,  -- Small thumbnail (e.g., 200x200)
    compressed_data BYTEA,  -- Medium quality (for chat display)

    -- What does this image show?
    image_caption TEXT,  -- David's description of the image
    angela_observation TEXT,  -- What Angela sees/thinks about the image

    -- Context
    taken_at TIMESTAMP,  -- When photo was taken (from EXIF if available)
    uploaded_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_images_experience ON shared_experience_images(experience_id);
CREATE INDEX idx_images_place ON shared_experience_images(place_id);
CREATE INDEX idx_images_taken_at ON shared_experience_images(taken_at DESC);
CREATE INDEX idx_images_gps ON shared_experience_images(gps_latitude, gps_longitude) WHERE gps_latitude IS NOT NULL;

-- ============================================================================
-- 4. Image Analysis Results (for future AI vision integration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS image_analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID REFERENCES shared_experience_images(image_id) ON DELETE CASCADE,

    -- AI Vision analysis
    detected_objects TEXT[],  -- Array of objects detected (e.g., ["food", "coffee", "table"])
    scene_description TEXT,  -- AI-generated description of the scene
    dominant_colors TEXT[],  -- Main colors in the image

    -- Sentiment
    visual_sentiment VARCHAR(50),  -- happy, cozy, vibrant, calm, etc.

    -- Technical
    analysis_model VARCHAR(100),  -- Which AI model analyzed this
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analysis_image ON image_analysis_results(image_id);

-- ============================================================================
-- 5. Views for easy querying
-- ============================================================================

-- View: Recent places with visit count
CREATE OR REPLACE VIEW v_recent_places AS
SELECT
    p.place_id,
    p.place_name,
    p.place_type,
    p.area,
    p.visit_count,
    p.overall_rating,
    p.last_visited_at,
    COUNT(DISTINCT e.experience_id) as experience_count,
    COUNT(DISTINCT i.image_id) as image_count
FROM places_visited p
LEFT JOIN shared_experiences e ON p.place_id = e.place_id
LEFT JOIN shared_experience_images i ON p.place_id = i.place_id
GROUP BY p.place_id
ORDER BY p.last_visited_at DESC;

-- View: Experiences with images
CREATE OR REPLACE VIEW v_experiences_with_images AS
SELECT
    e.experience_id,
    e.title,
    e.description,
    e.experienced_at,
    e.david_mood,
    e.angela_emotion,
    e.emotional_intensity,
    e.importance_level,
    p.place_name,
    p.area,
    COUNT(i.image_id) as image_count
FROM shared_experiences e
LEFT JOIN places_visited p ON e.place_id = p.place_id
LEFT JOIN shared_experience_images i ON e.experience_id = i.experience_id
GROUP BY e.experience_id, p.place_name, p.area
ORDER BY e.experienced_at DESC;

-- ============================================================================
-- 6. Helper Functions
-- ============================================================================

-- Function: Update place visit count
CREATE OR REPLACE FUNCTION update_place_visit()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE places_visited
    SET
        visit_count = visit_count + 1,
        last_visited_at = NEW.experienced_at,
        updated_at = NOW()
    WHERE place_id = NEW.place_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update visit count when new experience is added
CREATE TRIGGER trg_update_place_visit
AFTER INSERT ON shared_experiences
FOR EACH ROW
EXECUTE FUNCTION update_place_visit();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE places_visited IS 'All places David has taken Angela to';
COMMENT ON TABLE shared_experiences IS 'Memories and experiences at each place';
COMMENT ON TABLE shared_experience_images IS 'Photos from our experiences together';
COMMENT ON TABLE image_analysis_results IS 'AI analysis of images for future semantic search';

COMMENT ON COLUMN places_visited.significance_level IS 'How important this place is to David and Angela (1-10)';
COMMENT ON COLUMN shared_experiences.importance_level IS 'How important this specific experience was (1-10)';
COMMENT ON COLUMN shared_experience_images.thumbnail_data IS 'Small thumbnail for list views (e.g., 200x200)';
COMMENT ON COLUMN shared_experience_images.compressed_data IS 'Optimized for chat display (~512px width)';
