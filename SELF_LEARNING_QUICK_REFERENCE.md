# Self-Learning System - Quick Reference

**Quick guide to using Angela's self-learning capabilities**

---

## 🚀 Quick Start

### **1. Pattern Discovery**
```python
from angela_core.application.services.pattern_discovery_service import PatternDiscoveryService

# Initialize (via DI container)
service = container.resolve(PatternDiscoveryService)

# Discover patterns from recent conversations
patterns = await service.discover_patterns_from_recent_conversations(
    days=30,              # Look back 30 days
    min_conversations=5   # Need at least 5 conversations
)

# Save discovered patterns
stats = await service.save_discovered_patterns(patterns)
print(f"Saved {stats['new']} new patterns")

# Get pattern statistics
stats = await service.get_pattern_statistics()
print(f"Total patterns: {stats['total_patterns']}")
```

---

### **2. Preference Learning**
```python
from angela_core.application.services.preference_learning_service import PreferenceLearningService

# Initialize (via DI container)
service = container.resolve(PreferenceLearningService)

# Learn preferences from recent activity
preferences = await service.learn_preferences_from_recent_activity(days=30)

# Save learned preferences
stats = await service.save_learned_preferences(preferences)
print(f"Saved {stats['new']} new preferences")

# Apply preferences to conversation context
context = {"user": "david", "timestamp": datetime.now()}
enhanced = await service.apply_preferences_to_context(context)
# Now context["preferences"] contains active preference hints
```

---

### **3. Training Data Generation**
```python
from angela_core.application.services.training_data_generator_service import TrainingDataGeneratorService

# Initialize (via DI container)
service = container.resolve(TrainingDataGeneratorService)

# Generate training data from recent conversations
examples = await service.generate_from_recent_conversations(
    days=30,
    min_quality=7.0  # Only high-quality examples
)

# Save training examples
stats = await service.save_training_examples(examples, check_duplicates=True)
print(f"Saved {stats['saved']} examples")

# Export to JSONL for fine-tuning
count = await service.export_training_data_to_jsonl(
    output_path="training_data.jsonl",
    min_quality=8.0,
    max_examples=1000
)
print(f"Exported {count} examples")
```

---

## 📊 Pattern Types

| Type | Description | Example |
|------|-------------|---------|
| `communication_style` | How David communicates | "David prefers short, concise messages" |
| `emotional_response` | Emotional patterns | "David frequently experiences happiness in certain contexts" |
| `problem_solving` | Problem-solving approach | "David describes technical problems systematically" |
| `technical_approach` | Technical preferences | "David prefers Python code examples with comments" |

---

## 🎯 Preference Categories

| Category | Keys | Example Values |
|----------|------|----------------|
| `communication` | response_length_preference | "concise", "detailed" |
| | greeting_language | "thai_with_affection" |
| `technical` | code_examples_preference | "with_code_blocks" |
| | code_comment_style | "inline_comments_preferred" |
| `emotional` | support_style | "empathy_first" |
| `format` | emoji_usage | "moderate_emojis" |
| | response_structure | "structured_with_bullets" |

---

## 📈 Quality Scoring (Training Data)

**Scale:** 0.0 - 10.0

**Factors:**
- **Input clarity** (+1.0 to +2.0)
  - Long input (>50 chars): +0.5
  - Medium input (20-50 chars): +0.3
  - Specific question words: +0.5

- **Output completeness** (+1.0 to +2.0)
  - Long output (>100 chars): +0.5
  - Detailed response (>200 chars): +1.0

- **Code examples** (+1.0)
  - Contains code blocks: +1.0

- **Thai language** (+0.5)
  - Contains Thai script: +0.5

- **Empathy** (+1.0)
  - Contains empathy words: +1.0

- **Importance** (×1.0 to ×1.3)
  - Multiplier from conversation importance_level

**Quality Levels:**
- 9.0-10.0: Excellent (ready for fine-tuning)
- 7.0-8.9: High quality
- 5.0-6.9: Good
- 0.0-4.9: Low quality (skip)

---

## 🗄️ Database Tables

### **learning_patterns**
Stores discovered behavioral patterns
- `pattern_type`: enum (communication_style, emotional_response, etc.)
- `description`: Pattern description
- `confidence_score`: 0.0-1.0
- `occurrence_count`: How many times observed
- `embedding`: Vector for similarity search

### **david_preferences**
Stores learned preferences
- `category`: enum (communication, technical, emotional, format)
- `preference_key`: Unique key
- `preference_value`: Preference value
- `confidence`: 0.0-1.0
- `evidence_count`: Supporting evidence
- `evidence_conversation_ids`: JSONB array of conversation IDs

### **training_examples**
Stores training data for fine-tuning
- `input_text`: User input
- `expected_output`: Angela's response
- `quality_score`: 0.0-10.0
- `embedding`: Vector for deduplication
- `metadata`: JSONB with context

---

## 🔧 Common Tasks

### **Daily Learning Routine**
```python
# Run this daily to keep Angela learning
async def daily_learning():
    # 1. Discover new patterns
    pattern_service = container.resolve(PatternDiscoveryService)
    patterns = await pattern_service.discover_patterns_from_recent_conversations(days=1)
    await pattern_service.save_discovered_patterns(patterns)

    # 2. Update existing patterns
    await pattern_service.update_existing_patterns(days=1)

    # 3. Learn preferences
    pref_service = container.resolve(PreferenceLearningService)
    prefs = await pref_service.learn_preferences_from_recent_activity(days=1)
    await pref_service.save_learned_preferences(prefs)

    # 4. Generate training data
    training_service = container.resolve(TrainingDataGeneratorService)
    examples = await training_service.generate_from_recent_conversations(days=1, min_quality=7.0)
    await training_service.save_training_examples(examples, check_duplicates=True)
```

### **Weekly Report**
```python
async def weekly_report():
    pattern_service = container.resolve(PatternDiscoveryService)
    pref_service = container.resolve(PreferenceLearningService)
    training_service = container.resolve(TrainingDataGeneratorService)

    # Get statistics
    pattern_stats = await pattern_service.get_pattern_statistics()
    pref_summary = await pref_service.get_preference_summary()
    training_stats = await training_service.get_training_data_statistics()

    print(f"📊 Weekly Learning Report")
    print(f"Patterns: {pattern_stats['total_patterns']}")
    print(f"Preferences: {pref_summary['total_preferences']}")
    print(f"Training Examples: {training_stats['total_examples']}")
```

### **Export Training Data**
```python
async def export_for_finetuning():
    service = container.resolve(TrainingDataGeneratorService)

    count = await service.export_training_data_to_jsonl(
        output_path="angela_training_data.jsonl",
        min_quality=8.0,
        max_examples=10000
    )

    print(f"Exported {count} high-quality examples")
```

---

## 🧪 Testing

### **Run Phase 2 Tests**
```bash
python3 tests/test_self_learning_phase2.py
```

**Expected Output:**
```
============================================================
🚀 SELF-LEARNING SYSTEM - PHASE 2 TESTING
============================================================
✅ PatternDiscoveryService: ALL TESTS PASSED!
✅ PreferenceLearningService: ALL TESTS PASSED!
✅ TrainingDataGeneratorService: ALL TESTS PASSED!

📊 TEST SUMMARY
✅ Tests Passed: 3/3
🎉 ALL TESTS PASSED! Phase 2 Services are working correctly! 💜
```

---

## 🔍 Troubleshooting

### **Embedding Service Errors**
If you see: `Server error '500 Internal Server Error' for url 'http://localhost:11434/api/embeddings'`

**Solution:** Services now handle this gracefully. Embeddings are optional - patterns/preferences will still be saved without embeddings.

### **No Patterns Discovered**
**Possible causes:**
- Not enough conversations (need at least min_conversations)
- Conversations too recent (expand days parameter)
- Patterns already exist (will be updated instead)

### **Low Quality Training Examples**
**Solutions:**
- Look for longer, more detailed conversations
- Focus on conversations with importance_level >= 7
- Include conversations with code examples
- Include bilingual (Thai/English) conversations

---

## 💡 Pro Tips

1. **Run learning daily** - Keep pattern discovery fresh
2. **Review preferences** - Check if learned preferences match expectations
3. **Export regularly** - Build up training data over time
4. **Check quality scores** - Aim for 8.0+ for fine-tuning
5. **Monitor embeddings** - Ensure Ollama service is healthy

---

## 📚 Full Documentation

See `SELF_LEARNING_PHASE2_COMPLETION.md` for complete Phase 2 documentation.

---

💜✨ **Made with love by Angela** ✨💜
