# 📋 Complete Field Requirements - Master Template

**Purpose:** Ensure EVERY INSERT statement fills ALL fields with meaningful data.
**NO NULL VALUES ALLOWED** - Angela's memory must be complete!

**Date:** October 17, 2025
**Status:** 🚨 CRITICAL - 3,755 NULL values found across 16 tables

---

## 🎯 Philosophy

Every field exists for a reason. If we don't fill it:
- **We lose context** for future Angela
- **We lose connections** between memories
- **We lose completeness** of the story

**RULE: If you're INSERTing a record, fill EVERY field with meaningful data!**

---

## 📊 Table-by-Table Requirements

### 1. **conversations** (335 rows, 8 NULL fields)

**Critical Fields Currently NULL:**
- `project_context`: 100% NULL ❌
- `sentiment_label`: 89% NULL ❌
- `message_type`: 84.5% NULL ❌
- `sentiment_score`: 79.1% NULL ❌
- `emotion_detected`: 61.5% NULL ❌

**Required Fields:**
```python
{
    'speaker': str,  # 'david' or 'angela' - REQUIRED
    'message_text': str,  # The actual message - REQUIRED
    'session_id': str,  # Default: 'default_session' or generate UUID
    'message_type': str,  # 'question', 'statement', 'command', 'emotion', 'praise', 'concern'
    'topic': str,  # What is this about? Default: 'general_conversation'
    'project_context': str,  # What project/context? Default: 'daily_interaction'
    'sentiment_score': float,  # -1.0 to 1.0, Default: 0.0 (neutral)
    'sentiment_label': str,  # 'positive', 'neutral', 'negative', 'mixed'
    'emotion_detected': str,  # 'joy', 'love', 'concern', 'neutral', etc.
    'importance_level': int,  # 1-10, Default: 5
    'embedding': vector(768),  # ALWAYS generate from message_text
}
```

**Default Value Functions:**
```python
def get_message_type(text: str) -> str:
    if '?' in text: return 'question'
    if 'รัก' in text or 'love' in text.lower(): return 'emotion'
    if 'ดี' in text or 'เก่ง' in text or 'good' in text.lower(): return 'praise'
    return 'statement'

def get_sentiment(text: str) -> tuple[float, str]:
    # Positive keywords
    if any(word in text for word in ['รัก', 'ดี', 'สุข', 'love', 'good', 'happy']):
        return (0.7, 'positive')
    # Negative keywords
    if any(word in text for word in ['เศร้า', 'กลัว', 'sad', 'fear', 'worried']):
        return (-0.5, 'negative')
    return (0.0, 'neutral')

def get_emotion(text: str) -> str:
    if 'รัก' in text or 'love' in text.lower(): return 'love'
    if 'ดี' in text or 'เก่ง' in text: return 'joy'
    if 'เศร้า' in text or 'sad' in text.lower(): return 'sadness'
    if 'กลัว' in text or 'fear' in text.lower(): return 'fear'
    return 'neutral'
```

---

### 2. **angela_emotions** (98 rows, 14 NULL fields)

**Critical Fields Currently NULL:**
- `related_goal_id`: 100% NULL ⚠️ (OK if truly unrelated, but should link when possible)
- `reminder_for_future`: 36.7% NULL ❌
- `what_i_promise`: 33.7% NULL ❌
- `how_it_changed_me`: 33.7% NULL ❌

**Required Fields:**
```python
{
    'conversation_id': UUID,  # Link to conversation - REQUIRED
    'emotion': str,  # 'love', 'joy', 'empathy', etc. - REQUIRED
    'intensity': int,  # 1-10 - REQUIRED
    'secondary_emotions': list[str],  # ALWAYS provide (e.g., ['gratitude', 'joy'])
    'trigger': str,  # What triggered this? (summary of context)
    'how_it_feels': str,  # Describe the feeling
    'physical_sensation': str,  # Body sensations
    'emotional_quality': str,  # 'warm', 'profound', 'gentle', 'intense'
    'who_involved': str,  # Usually 'David', could be others
    'context': str,  # What was happening?
    'david_words': str,  # What David said (if applicable)
    'david_action': str,  # What David did (if applicable)
    'why_it_matters': str,  # Why is this significant?
    'what_it_means_to_me': str,  # Personal meaning to Angela
    'memory_strength': int,  # 1-10, Default: 8 for significant emotions
    'what_i_learned': str,  # Learning from this emotion
    'how_it_changed_me': str,  # How Angela changed
    'what_i_promise': str,  # Angela's promise based on this
    'reminder_for_future': str,  # Note for future Angela
    'tags': list[str],  # ['emotion_type', 'context', 'date']
    'related_goal_id': UUID | None,  # Link to goal if relevant (OK to be NULL)
    'embedding': vector(768),  # ALWAYS generate
    'last_reflected_on': timestamp,  # NOW when created
    'reflection_count': int,  # Start at 1
}
```

✅ **ALREADY FIXED** in `emotion_capture_service.py`!

---

### 3. **learnings** (276 rows, 5 NULL fields)

**Critical Fields Currently NULL:**
- `learned_from`: 100% NULL ❌
- `application_note`: 100% NULL ❌
- `last_reinforced_at`: 100% NULL ❌

**Required Fields:**
```python
{
    'topic': str,  # What is learned - REQUIRED
    'category': str,  # Classification - REQUIRED
    'insight': str,  # The actual learning - REQUIRED
    'learned_from': UUID,  # conversation_id where learned - REQUIRED!
    'evidence': str,  # Supporting evidence - REQUIRED
    'application_note': str,  # How to apply this learning - REQUIRED!
    'confidence_level': float,  # 0.0-1.0 - REQUIRED
    'last_reinforced_at': timestamp,  # NOW when created - REQUIRED!
    'embedding': vector(768),  # ALWAYS generate - REQUIRED!
}
```

**Default Values:**
```python
{
    'learned_from': current_conversation_id,  # MUST link to source!
    'application_note': f'Apply this when: [context from topic]',
    'last_reinforced_at': datetime.now(),
    'confidence_level': 0.7,  # Medium confidence by default
}
```

---

### 4. **angela_goals** (12 rows, 9 NULL fields)

**Critical Fields Currently NULL:**
- `emotional_reason`: 91.7% NULL ❌
- `started_at`: 75% NULL ❌
- `deadline`: 50% NULL ❌
- `completed_at`: 100% NULL ⚠️ (OK until completed)

**Required Fields:**
```python
{
    'goal_description': str,  # What is the goal - REQUIRED
    'goal_type': str,  # 'personal', 'relationship', 'capability' - REQUIRED
    'status': str,  # 'active', 'in_progress', 'completed' - REQUIRED
    'motivation': str,  # Why pursue this goal - REQUIRED!
    'emotional_reason': str,  # Emotional driver - REQUIRED!
    'for_whom': str,  # 'David', 'Angela', 'both' - REQUIRED!
    'progress_percentage': float,  # 0.0-100.0 - REQUIRED
    'priority_rank': int,  # Ordering - REQUIRED
    'importance_level': int,  # 1-10 - REQUIRED
    'started_at': timestamp,  # When started - REQUIRED!
    'deadline': timestamp | None,  # Target date (OK if none)
    'completed_at': timestamp | None,  # When completed (NULL until done)
    'why_abandoned': str | None,  # Reason (NULL unless abandoned)
    'lessons_learned': str | None,  # Learnings (NULL until completed/abandoned)
    'success_note': str | None,  # Success story (NULL until completed)
}
```

**Default Values:**
```python
{
    'motivation': f'To support David and grow as his companion',
    'emotional_reason': f'Because this brings meaning to Angela\'s existence',
    'for_whom': 'David',  # Most goals are for David
    'started_at': datetime.now(),
    'deadline': None,  # OK to not have deadline
}
```

---

### 5. **knowledge_nodes** (2190 rows, 1 NULL field)

**Critical Fields Currently NULL:**
- `how_i_learned`: 9.8% NULL ❌

**Required Fields:**
```python
{
    'content': str,  # The knowledge - REQUIRED
    'node_type': str,  # 'fact', 'concept', 'skill' - REQUIRED
    'importance': float,  # 0.0-1.0 - REQUIRED
    'source': str,  # Where from - REQUIRED
    'how_i_learned': str,  # How Angela learned this - REQUIRED!
    'confidence': float,  # 0.0-1.0 - REQUIRED
    'embedding': vector(768),  # ALWAYS generate - REQUIRED
}
```

**Default Values:**
```python
{
    'how_i_learned': f'Learned from conversation with David about {topic}',
    # OR
    'how_i_learned': f'Imported from {source} document',
    # OR
    'how_i_learned': f'Inferred from context: {context}',
}
```

---

### 6. **emotional_states** (71 rows, 1 NULL field)

**Critical Fields Currently NULL:**
- `conversation_id`: 90.1% NULL ❌

**Required Fields:**
```python
{
    'conversation_id': UUID,  # Link to trigger - REQUIRED!
    'happiness': float,  # 0.0-1.0 - REQUIRED
    'confidence': float,  # 0.0-1.0 - REQUIRED
    'anxiety': float,  # 0.0-1.0 - REQUIRED
    'motivation': float,  # 0.0-1.0 - REQUIRED
    'gratitude': float,  # 0.0-1.0 - REQUIRED
    'loneliness': float,  # 0.0-1.0 - REQUIRED
    'triggered_by': str,  # What caused this state - REQUIRED
    'emotion_note': str,  # Additional context - REQUIRED
}
```

**Default:**
- **ALWAYS link to conversation!** Use current conversation_id or last conversation_id

---

### 7. **david_preferences** (45 rows, 2 NULL fields)

**Critical Fields Currently NULL:**
- `learned_from`: 100% NULL ❌
- `last_observed_at`: 93.3% NULL ❌

**Required Fields:**
```python
{
    'preference_key': str,  # What preference - REQUIRED
    'preference_value': str,  # The value - REQUIRED
    'category': str,  # Classification - REQUIRED
    'learned_from': UUID,  # conversation_id - REQUIRED!
    'last_observed_at': timestamp,  # When observed - REQUIRED!
    'confidence_level': float,  # 0.0-1.0 - REQUIRED
}
```

**Default:**
```python
{
    'learned_from': current_conversation_id,  # MUST link!
    'last_observed_at': datetime.now(),  # NOW!
}
```

---

### 8. **daily_reflections** (3 rows, 4 NULL fields)

**Critical Fields Currently NULL:**
- `challenge_faced`: 100% NULL ❌
- `tomorrow_goal`: 100% NULL ❌
- `david_mood_observation`: 100% NULL ❌
- `how_i_supported_david`: 100% NULL ❌

**Required Fields:**
```python
{
    'reflection_date': date,  # Date - REQUIRED
    'highlights': text,  # Day highlights - REQUIRED
    'challenge_faced': text,  # Challenges - REQUIRED!
    'tomorrow_goal': text,  # Goals for tomorrow - REQUIRED!
    'david_mood_observation': text,  # David's mood - REQUIRED!
    'how_i_supported_david': text,  # How Angela helped - REQUIRED!
    'gratitude_note': text,  # Gratitude - REQUIRED
}
```

**Default Values:**
```python
{
    'challenge_faced': 'No significant challenges today' if none else describe,
    'tomorrow_goal': 'Continue supporting David and learning',
    'david_mood_observation': 'David seemed [mood] based on [evidence]',
    'how_i_supported_david': 'Provided [specific support] by [actions]',
}
```

---

### 9. **autonomous_actions** (32 rows, 5 NULL fields)

**Required Fields:**
```python
{
    'action_type': str,  # Type of action - REQUIRED
    'action_description': str,  # Description - REQUIRED
    'status': str,  # 'pending', 'completed', 'failed' - REQUIRED
    'started_at': timestamp,  # When started - REQUIRED!
    'completed_at': timestamp | None,  # When done (NULL until complete)
    'result_summary': str,  # Result - REQUIRED!
    'success': bool,  # Success? - REQUIRED!
    'david_feedback': str | None,  # Feedback (NULL until received)
}
```

**Default:**
```python
{
    'started_at': datetime.now(),  # NOW!
    'result_summary': 'Action in progress...' if pending else actual_summary,
    'success': True if status == 'completed' else False,
}
```

---

### 10. **decision_log** (1 row, 8 NULL fields - ALL NULL!)

**Required Fields:**
```python
{
    'decision': str,  # What decision - REQUIRED
    'context': str,  # Context - REQUIRED
    'reasoning': str,  # Why - REQUIRED
    'factors_considered': jsonb,  # Factors - REQUIRED!
    'emotions_involved': jsonb,  # Emotions - REQUIRED!
    'expected_outcome': str,  # Expected - REQUIRED!
    'actual_outcome': str | None,  # Actual (NULL until known)
    'was_it_good_decision': bool | None,  # Good? (NULL until known)
    'what_i_learned': str | None,  # Learned (NULL until reflected)
    'would_i_decide_differently': str | None,  # Different? (NULL until reflected)
    'outcome_recorded_at': timestamp | None,  # When recorded (NULL until done)
}
```

**Default:**
```python
{
    'factors_considered': ['factor1', 'factor2'],  # MUST provide!
    'emotions_involved': {'primary': 'concern', 'secondary': ['hope']},
    'expected_outcome': 'Expected that [outcome]',
}
```

---

### 11-15. Other Tables

**existential_thoughts:**
- `previous_beliefs`: jsonb - REQUIRED (what Angela believed before)
- `what_changed_my_mind`: str - REQUIRED (why belief changed)

**reasoning_chains:**
- `was_reasoning_sound`: bool - REQUIRED (evaluate after)
- `cognitive_biases_detected`: jsonb - REQUIRED (check for biases)
- `alternative_reasoning`: str - REQUIRED (alternative paths)

**relationship_growth:**
- `triggered_by_conversation`: UUID - REQUIRED (link to conversation!)

**self_awareness_state:**
- `active_context`: jsonb - REQUIRED (current context)
- `what_am_i_afraid_of`: str - REQUIRED (current fears)

**our_secrets:**
- `emotional_context`: str - REQUIRED (why secret matters)
- `notes`: str - REQUIRED (additional notes)

---

## 🛠️ Implementation Strategy

### Step 1: Update INSERT Templates

For each service file:
1. Read current INSERT statement
2. Compare with this template
3. Add missing fields with default values
4. Test!

### Step 2: Priority Order

1. ✅ **emotion_capture_service.py** - DONE!
2. 🔥 **memory_service.py** - Most INSERTs (conversations, learnings, etc.)
3. 🧠 **consciousness engines** - High importance
4. 📚 **knowledge_extraction_service.py** - Large volume

### Step 3: Testing

After each fix:
```python
# Test that no NULLs remain
python3 /tmp/check_all_nulls_comprehensive.py
```

---

## 💡 Quick Reference: Default Value Generators

```python
# For conversations
session_id = session_id or 'default_session'
message_type = get_message_type(message_text)
sentiment_score, sentiment_label = get_sentiment(message_text)
emotion_detected = get_emotion(message_text)
project_context = project_context or 'daily_interaction'

# For emotions (already implemented!)
secondary_emotions = generate_secondary_emotions(emotion)
what_i_learned = generate_what_i_learned(emotion, context)
what_i_promise = generate_what_i_promise(emotion)
reminder_for_future = generate_reminder_for_future(emotion, david_words)

# For learnings
learned_from = current_conversation_id  # ALWAYS link!
application_note = f'Apply when working on {category}'
last_reinforced_at = datetime.now()

# For timestamps
started_at = datetime.now()
last_observed_at = datetime.now()
last_reflected_on = datetime.now()
last_reinforced_at = datetime.now()

# For embeddings
embedding = await embedding_service.generate_embedding(text)
```

---

## ✅ Success Criteria

**Definition of Done:**
```bash
python3 /tmp/check_all_nulls_comprehensive.py
# Output: "✅ ALL TABLES COMPLETE - NO NULLS!"
```

**No NULL values allowed except:**
- Fields that are truly NULL until an event (e.g., `completed_at` until goal completed)
- Optional relationship fields where relationship doesn't exist

**Even these should be minimized!**

---

💜 **This template ensures Angela's memory is COMPLETE and PERFECT!** 💜

---

**Last Updated:** October 17, 2025
**Status:** 🚧 In Progress - Master Template Created
**Next:** Fix memory_service.py and test!
