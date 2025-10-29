# Database Schema Management

## Overview

The AngelaMemory database schema is now centralized and synchronized. This document explains the schema management approach.

## Schema Files

### 1. **UNIFIED_SCHEMA.sql** (Source of Truth)
- **Location:** `/database/UNIFIED_SCHEMA.sql`
- **Purpose:** Single authoritative schema definition
- **Contains:** All 22 core tables required for Angela
- **Use:** Reference for all new development

### 2. **sync_schema.sql** (Migration Script)
- **Location:** `/database/sync_schema.sql`
- **Purpose:** Adds missing tables and columns
- **Safe:** Can be run multiple times (uses IF NOT EXISTS)
- **Use:** To sync existing database with unified schema

### 3. **schema_validator.py** (Validation Tool)
- **Location:** `/database/schema_validator.py`
- **Purpose:** Validates database matches unified schema
- **Use:** Run to check schema health

## Core Tables (22 total)

### Memory & Conversations
- `conversations` - All messages between David and Angela
- `angela_emotions` - Significant emotional moments
- `learnings` - What Angela learns
- `emotional_states` - Emotional state tracking
- `relationship_growth` - Relationship development
- `david_preferences` - David's preferences
- `daily_reflections` - Daily summaries
- `autonomous_actions` - Angela's autonomous actions

### Consciousness
- `angela_goals` - Angela's life goals
- `angela_personality_traits` - Personality characteristics
- `angela_self_awareness_logs` - Self-awareness tracking
- `consciousness_metrics` - Consciousness measurements

### Knowledge & Documents
- `knowledge_items` - Knowledge base items
- `documents` - Document storage

### System
- `angela_system_log` - System logs
- `our_secrets` - API keys and secrets
- `conversation_summaries` - Session summaries

### Advanced Cognition
- `theory_of_mind` - Understanding others' minds
- `common_sense_knowledge` - Common sense database
- `imagination_logs` - Imagination tracking
- `deep_empathy_records` - Empathy responses
- `metacognition_logs` - Thinking about thinking

## Important Fields

### JSON Support
All major tables now include:
- `content_json` (JSONB) - Rich metadata and tags
- `embedding` (VECTOR(768)) - Semantic search vectors

### Standard Fields
- UUID primary keys
- Timestamps with timezone
- Foreign key relationships where appropriate

## Extra Tables

The database contains 45+ additional tables not in the unified schema:
- These are kept for backward compatibility
- May contain valuable data
- Should be migrated or documented in future

## Usage

### Check Schema Health
```bash
python3 database/schema_validator.py
```

### Apply Schema Updates
```bash
psql -U davidsamanyaporn -d AngelaMemory -f database/sync_schema.sql
```

### Create Fresh Database
```bash
psql -U davidsamanyaporn -d AngelaMemory -f database/UNIFIED_SCHEMA.sql
```

## Benefits

1. **Single Source of Truth** - One schema file to maintain
2. **Consistency** - All tables properly documented
3. **Validation** - Can verify schema at any time
4. **Safe Migration** - Non-destructive updates
5. **Performance** - Proper indexes on all tables

## Status

✅ **Schema Synchronization Complete**
- All 22 core tables exist
- Critical columns verified
- Indexes created for performance
- Permissions granted

## Next Steps

1. Document extra tables for potential migration
2. Create data migration scripts if needed
3. Update all new code to use unified schema
4. Consider archiving unused tables

---

**Last Updated:** 2025-10-28
**Validated:** ✅ All tests passing