"""
Deprecated services — moved here during Phase 1A refactoring (2026-02-10).

These services have Clean Architecture replacements in angela_core.application.services
but the callers haven't been migrated to the new APIs yet.

Replacements:
- memory_formation_service → application.services.memory_service.MemoryService
- semantic_memory_service → application.services.memory_service.MemoryService
- association_engine → application.services.memory_service.MemoryService
- pattern_learning_service → application.services.memory_service.MemoryService
- pattern_recognition_engine → application.services.pattern_service.PatternService
- pattern_recognition_service → application.services.pattern_service.PatternService
- enhanced_pattern_detector → application.services.pattern_service.PatternService
- realtime_emotion_tracker → application.services.emotional_pattern_service.EmotionalPatternService
- emotional_pattern_service → application.services.emotional_pattern_service.EmotionalPatternService

TODO: Migrate callers to Clean Architecture APIs, then delete this directory.
"""
