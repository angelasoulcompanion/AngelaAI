# Batch-08 Migration Guide: Using Adapters with Legacy Services

**Batch:** 08 of 31
**Date:** 2025-10-30
**Status:** ✅ **COMPLETE**

---

## 🎯 **Overview**

This guide shows how to use the new **Adapter Pattern** to allow legacy services to access Clean Architecture (Batches 2-7) without full refactoring.

**Key Benefit:** Legacy code can use new repositories/services with minimal changes!

---

## 📦 **What Was Created**

### **Adapter Files (6 files)**
1. `base_adapter.py` - Base adapter class
2. `conversation_adapter.py` - Conversation domain adapter
3. `emotion_adapter.py` - Emotion domain adapter
4. `memory_adapter.py` - Memory domain adapter
5. `document_adapter.py` - Document/RAG adapter
6. `legacy_service_adapter.py` - Unified factory (⭐ recommended!)

**Location:** `angela_core/infrastructure/adapters/`

---

## 🚀 **Quick Start**

### **Option 1: Use Unified Adapter (Recommended)**

```python
from angela_core.database import AngelaDatabase
from angela_core.infrastructure.adapters import LegacyServiceAdapter

# In your legacy service __init__:
class MyLegacyService:
    def __init__(self):
        self.db = AngelaDatabase()
        await self.db.connect()
        
        # Create adapter - gives access to all domains!
        self.adapter = LegacyServiceAdapter(self.db)
    
    async def my_old_method(self, david_message, angela_response):
        # OLD: Direct database calls
        # await self.db.execute("INSERT INTO conversations...")
        
        # NEW: Use adapter (calls new ConversationService under the hood!)
        result = await self.adapter.conversation.log_conversation_old_style(
            david_message=david_message,
            angela_response=angela_response,
            source="my_service",
            importance=7
        )
        
        return result  # Old-style format {"success": True, "data": {...}}
```

### **Option 2: Use Specific Adapters**

```python
from angela_core.infrastructure.adapters import (
    ConversationAdapter,
    EmotionAdapter
)

class MyLegacyService:
    def __init__(self):
        self.db = AngelaDatabase()
        await self.db.connect()
        
        # Use only what you need
        self.conversation_adapter = ConversationAdapter(self.db)
        self.emotion_adapter = EmotionAdapter(self.db)
```

---

## 📖 **Migration Examples**

### **Example 1: Conversation Integration Service**

**BEFORE** (direct database access):
```python
class ConversationIntegrationService:
    async def _on_aggregated_conversation(self, message):
        # OLD: Direct database access
        await self.db.execute(
            "INSERT INTO conversations (speaker, message_text, ...) VALUES (...)"
        )
```

**AFTER** (using adapter):
```python
from angela_core.infrastructure.adapters import LegacyServiceAdapter

class ConversationIntegrationService:
    def __init__(self):
        self.db = AngelaDatabase()
        await self.db.connect()
        
        # Add adapter
        self.adapter = LegacyServiceAdapter(self.db)
    
    async def _on_aggregated_conversation(self, message):
        # NEW: Use adapter (new architecture!)
        result = await self.adapter.conversation.log_conversation_old_style(
            david_message=message.david_message,
            angela_response=message.angela_response,
            source=message.source,
            session_id=message.session_id,
            importance=message.importance or 5
        )
        
        return result
```

**Changes:** ~5 lines! ✅

### **Example 2: Emotion Capture**

**BEFORE**:
```python
async def capture_emotion(self, emotion, intensity, context):
    await self.db.execute(
        "INSERT INTO angela_emotions (emotion, intensity, context, ...) VALUES (...)"
    )
```

**AFTER**:
```python
async def capture_emotion(self, emotion, intensity, context):
    result = await self.adapter.emotion.capture_emotion_old_style(
        emotion=emotion,
        intensity=intensity,
        context=context,
        why_matters="Significant moment"
    )
    return result
```

### **Example 3: Memory Consolidation**

**BEFORE**:
```python
async def consolidate_memories(self, batch_size=100):
    memories = await self.db.fetch("SELECT * FROM memories WHERE...")
    for memory in memories:
        # Apply decay, consolidate, update...
        await self.db.execute("UPDATE memories SET ...")
```

**AFTER**:
```python
async def consolidate_memories(self, batch_size=100):
    result = await self.adapter.memory.consolidate_memories_old_style(
        batch_size=batch_size,
        apply_decay=True
    )
    # Returns: {"success": True, "data": {"consolidated": 10, "decayed": 5, ...}}
    return result
```

---

## 🛠️ **Adapter API Reference**

### **ConversationAdapter**

```python
# Log conversation (old style, new architecture)
result = await adapter.conversation.log_conversation_old_style(
    david_message="Hello",
    angela_response="Hi!",
    source="web_chat",
    session_id="session_123",
    importance=7,
    topic="greeting",
    emotion="happy"
)

# Get recent conversations
conversations = await adapter.conversation.get_recent_conversations_old_style(
    days=7,
    source="web_chat",
    limit=100
)
```

### **EmotionAdapter**

```python
# Capture emotion
result = await adapter.emotion.capture_emotion_old_style(
    emotion="gratitude",
    intensity=9,
    context="David helped me",
    david_words="Let's make this better",
    why_matters="Because David cares",
    memory_strength=10
)

# Get recent emotions
emotions = await adapter.emotion.get_recent_emotions_old_style(
    days=7,
    min_intensity=7,
    limit=100
)
```

### **MemoryAdapter**

```python
# Consolidate memories
result = await adapter.memory.consolidate_memories_old_style(
    batch_size=100,
    apply_decay=True
)

# Get memory health
health = await adapter.memory.get_memory_health_old_style()
# Returns: {"health_score": 85, "recommendations": [...]}
```

### **DocumentAdapter**

```python
# Ingest document
result = await adapter.document.ingest_document_old_style(
    file_path="/path/to/doc.pdf",
    title="Architecture Guide",
    category="angela_core",
    importance=0.9
)

# Get documents
documents = await adapter.document.get_documents_old_style(
    category="angela_core",
    limit=100
)
```

---

## ✅ **Migration Checklist**

For each legacy service:

- [ ] Import `LegacyServiceAdapter`
- [ ] Initialize adapter in `__init__`: `self.adapter = LegacyServiceAdapter(db)`
- [ ] Replace direct database calls with adapter calls
- [ ] Test that functionality still works
- [ ] Optional: Add health check using `await self.adapter.health_check()`

---

## 🎯 **Benefits**

### **Before Adapters:**
- ❌ Must refactor entire service
- ❌ High risk of breaking changes
- ❌ Takes weeks/months per service
- ❌ Can't use new architecture

### **After Adapters:**
- ✅ Minimal code changes (~5-10 lines)
- ✅ Low risk (adapters tested)
- ✅ Takes minutes/hours per service
- ✅ **Uses new Clean Architecture immediately!**

---

## 🔍 **Health Checks**

```python
# Check all adapters
health = await adapter.health_check()
# Returns: {
#   "conversation": True,
#   "emotion": True,
#   "memory": True,
#   "document": True
# }

# Get adapter stats
stats = adapter.get_stats()
# Returns: {
#   "adapters_initialized": 4,
#   "domains": ["conversation", "emotion", "memory", "document"],
#   "db_connected": True
# }
```

---

## 📊 **Impact Assessment**

### **Services That Can Use Adapters:**
- ✅ conversation_integration_service.py
- ✅ realtime_learning_service.py
- ✅ background_learning_workers.py
- ✅ emotional_intelligence_service.py
- ✅ memory_consolidation_service.py
- ✅ All 59 legacy services!

### **Estimated Migration Time:**
- **Per service:** 30-60 minutes
- **Top 10 services:** 1-2 days
- **All 59 services:** 1-2 weeks (if needed)

---

## 💡 **Best Practices**

1. **Start small** - Migrate 1-2 services first
2. **Test thoroughly** - Run integration tests after migration
3. **Keep old code** - Comment out, don't delete (for rollback)
4. **Use unified adapter** - `LegacyServiceAdapter` is easier than individual adapters
5. **Add health checks** - Verify adapters work in production

---

## 🚀 **Next Steps**

1. Choose 5 most-used legacy services
2. Apply adapters (30-60 min each)
3. Test with integration tests
4. Deploy and monitor
5. Continue with remaining services as needed

---

**Created by:** น้อง Angela
**Date:** 2025-10-30
**Status:** Ready to use! 💜✨
