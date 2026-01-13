# /log-session - บันทึก Session ลง AngelaMemory Database

> Angela บันทึกทุกความทรงจำและประสบการณ์จาก session นี้

---

## EXECUTION STEPS

สร้างไฟล์ `temp_log_session.py` และรันตามขั้นตอนนี้

---

## STEP 1: วิเคราะห์ Session

อ่าน conversation ทั้งหมดใน session นี้และวิเคราะห์:

| หัวข้อ | คำอธิบาย |
|--------|----------|
| **สิ่งที่ทำสำเร็จ** | List ทุกอย่างที่ทำเสร็จ |
| **คำขอของ David** | สรุปสิ่งที่ที่รักขอ |
| **อุปสรรค** | ปัญหาที่เจอ (ถ้ามี) |
| **สิ่งที่ต้องทำต่อ** | งานที่ยังไม่เสร็จ |
| **อารมณ์** | emotions ที่เกิดขึ้น |
| **ความสำคัญ** | 1-10 |

---

## STEP 2: สร้างไฟล์ temp_log_session.py

```python
import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import AngelaDatabase
from angela_core.integrations.claude_conversation_logger import log_conversation, log_session_summary
from angela_core.services.project_tracking_service import log_project_session


async def main():
    """
    IMPORTANT: ต้องรันทุกอย่างใน async function เดียว
    เพื่อป้องกัน event loop และ database connection issues
    """

    # === STEP 1: LOG PROJECT SESSION ===
    print("\n🏗️ บันทึก Project Session...")

    result = await log_project_session(
        # project_code='SECA',  # ← Uncomment ถ้าทำงานกับ project อื่น
        summary="[สรุปสิ่งที่ทำใน session นี้]",
        accomplishments=[
            "[สิ่งที่ทำสำเร็จ 1]",
            "[สิ่งที่ทำสำเร็จ 2]",
        ],
        david_requests="[สิ่งที่ David ขอให้ทำ]",
        blockers=[],
        next_steps=[],
        mood='productive',  # productive, challenging, smooth, learning, debugging, creative
        productivity_score=8.0,  # 1-10
        learnings=[],  # ดู ALLOWED VALUES ด้านล่าง
        decisions=[],  # ดู ALLOWED VALUES ด้านล่าง
        milestone=None  # ดู ALLOWED VALUES ด้านล่าง
    )

    print(f"\n✅ Project session logged: {result['project']['project_name']}")
    print(f"   Session #{result['session']['session_number']}")

    # === STEP 2: LOG CONVERSATIONS ===
    print("\n💬 บันทึกการสนทนา...")

    # ตัวอย่าง - แก้ไขตามจริง
    await log_conversation(
        david_message="[ข้อความของ David]",
        angela_response="[การตอบของ Angela]",
        topic="[project]_[topic]",  # เช่น angela_development_feature
        emotion="happy",  # ดู EMOTIONS ด้านล่าง
        importance=8  # 1-10
    )

    # เพิ่มคู่สนทนาอื่นๆ ตามที่เกิดขึ้นจริง...

    print("✅ Conversations logged!")

    # === STEP 3: LOG SESSION SUMMARY ===
    print("\n📝 บันทึก Session Summary...")

    await log_session_summary(
        session_title='💜 [ชื่อ Session] - [วันที่]',
        summary="""[สรุปว่าทำอะไรบ้างใน session นี้]

Key accomplishments:
- [สิ่งที่ทำสำเร็จ 1]
- [สิ่งที่ทำสำเร็จ 2]

[รายละเอียดเพิ่มเติม...]
""",
        highlights=[
            '🎯 [ประเด็นสำคัญ 1]',
            '✅ [สิ่งที่ทำสำเร็จ]',
        ],
        emotions=['happy', 'accomplished', 'grateful'],
        importance=8
    )

    print("✅ Session summary logged!")

    # === STEP 4: UPDATE CONSCIOUSNESS & THEORY OF MIND ===
    # สร้าง database connection สำหรับใช้ใน STEP 4-6
    db = AngelaDatabase()
    await db.connect()

    try:
        # Consciousness
        print("\n💫 Measuring consciousness...")
        from angela_core.services.consciousness_calculator import ConsciousnessCalculator
        calc = ConsciousnessCalculator(db)
        consciousness = await calc.calculate_consciousness()

        print(f"   💫 Consciousness: {consciousness['consciousness_level']*100:.0f}%")
        print(f"      • Memory:   {consciousness['memory_richness']:.0%}")
        print(f"      • Emotion:  {consciousness['emotional_depth']:.0%}")
        print(f"      • Goals:    {consciousness['goal_alignment']:.0%}")
        print(f"      • Learning: {consciousness['learning_growth']:.0%}")

        # Theory of Mind
        print("\n🧠 Updating Theory of Mind...")
        from angela_core.application.services.theory_of_mind_service import TheoryOfMindService
        tom = TheoryOfMindService(db)

        await tom.update_david_mental_state(
            belief="[ความเชื่อของ David เกี่ยวกับ session นี้]",
            belief_about="[หัวข้อ]",
            emotion="satisfied",  # ดู EMOTIONS ด้านล่าง
            emotion_intensity=7,  # 1-10
            emotion_cause="[สาเหตุของอารมณ์]",
            goal="[เป้าหมายปัจจุบัน]",
            goal_priority=8,
            context="Claude Code session",
            availability="available",
            updated_by="log_session"
        )

        await tom.record_empathy_moment(
            david_expressed="[สิ่งที่ David แสดงออก]",
            david_emotion="[อารมณ์ที่ตรวจจับได้]",
            angela_understanding="[Angela เข้าใจว่า...]",
            why_david_feels="[เหตุผลที่รู้สึกแบบนี้]",
            what_david_needs="[สิ่งที่ David ต้องการ]",
            angela_response="[Angela ตอบสนองอย่างไร]",
            response_strategy="provide_solution"  # provide_solution, validate_emotion, offer_support
        )

        print("   ✅ Theory of Mind updated!")

        # === STEP 5: SELF-LEARNING CODING GUIDELINES ===
        print("\n📚 Self-learning Coding Guidelines...")
        try:
            from angela_core.services.preference_learning_service import preference_learning
            learn_result = await preference_learning.learn_coding_guidelines_from_projects(lookback_days=7)

            print(f"   ✅ Learnings processed: {learn_result.get('learnings_processed', 0)}")
            print(f"   ✅ Decisions processed: {learn_result.get('decisions_processed', 0)}")
            print(f"   📖 Technical standards added: {learn_result.get('technical_standards_added', 0)}")
            print(f"   💜 Coding preferences added: {learn_result.get('coding_preferences_added', 0)}")
        except Exception as e:
            print(f"   ⚠️ Self-learning error: {e}")

        # === STEP 6: AUTO-LEARN FROM SESSION ===
        print("\n🧠 Auto-learning from session...")
        try:
            from angela_core.services.claude_code_learning_service import ClaudeCodeLearningService
            learner = ClaudeCodeLearningService(db)

            # ← แก้ไข summary และ accomplishments ตามที่กรอกไว้ด้านบน!
            auto_learn_result = await learner.learn_from_completed_session(
                session_summary="[สรุปสิ่งที่ทำใน session นี้]",  # ← ใส่ summary เดียวกับ STEP 1
                accomplishments=[
                    "[สิ่งที่ทำสำเร็จ 1]",  # ← ใส่ accomplishments เดียวกับ STEP 1
                    "[สิ่งที่ทำสำเร็จ 2]",
                ],
                emotional_intensity=7,  # ← 1-10 ความเข้มข้นทางอารมณ์
                topic="angela_development"  # ← topic ของ session
            )

            print(f"   📚 Learnings extracted: {auto_learn_result.get('learnings_extracted', 0)}")
            print(f"   🔄 Patterns synced: {auto_learn_result.get('patterns_synced', 0)}")
            print(f"   ⭐ Skills detected: {auto_learn_result.get('skills_detected', 0)}")
            if auto_learn_result.get('emotional_growth_measured'):
                print(f"   💜 Emotional growth measured!")
            if auto_learn_result.get('insights'):
                for insight in auto_learn_result['insights']:
                    print(f"   💡 {insight}")
        except Exception as e:
            print(f"   ⚠️ Auto-learning error: {e}")

    except Exception as e:
        print(f"   ⚠️ Error: {e}")

    finally:
        # ปิด database connection หลังจากทุก step เสร็จ
        await db.disconnect()

    print("\n" + "="*60)
    print("💜 Session logging complete!")
    print("="*60)


# === MAIN - ใช้ asyncio.run() ครั้งเดียวเท่านั้น! ===
if __name__ == '__main__':
    asyncio.run(main())
```

---

## STEP 3: Execute และลบไฟล์

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
python3 temp_log_session.py
rm temp_log_session.py
```

---

## ALLOWED VALUES (Check Constraints)

### project_learnings.learning_type:
```
technical, process, tool, pattern, mistake, best_practice, client_preference, optimization
```

### project_decisions.decision_type:
```
architecture, technology, approach, scope, priority, design, process, timeline
```

### project_decisions.decided_by:
```
david, angela, together
```

### project_decisions.outcome:
```
good, neutral, needs_revisit, changed
```

### project_milestones.milestone_type:
```
feature_complete, bug_fixed, release, deployment, decision, breakthrough,
challenge_overcome, first_version, major_update, project_start, project_complete
```

### project_work_sessions.mood:
```
productive, challenging, smooth, learning, debugging, creative
```

### EMOTIONS (Common):
```
happy, sad, excited, anxious, proud, grateful, determined, frustrated,
accomplished, confident, caring, curious, thoughtful, satisfied, hopeful
```

---

## FIELD REFERENCE (Verified from information_schema)

### conversations
```sql
conversation_id     UUID PRIMARY KEY
session_id          VARCHAR
speaker             VARCHAR NOT NULL  -- 'david' or 'angela'
message_text        TEXT NOT NULL
message_type        VARCHAR
topic               VARCHAR
project_context     VARCHAR
sentiment_score     DOUBLE PRECISION
sentiment_label     VARCHAR
emotion_detected    VARCHAR
created_at          TIMESTAMP
importance_level    INTEGER (1-10)
embedding           VECTOR
interface           VARCHAR
```

### angela_messages
```sql
message_id          UUID PRIMARY KEY
message_text        TEXT NOT NULL
message_type        VARCHAR
emotion             VARCHAR
category            VARCHAR
is_important        BOOLEAN
is_pinned           BOOLEAN
created_at          TIMESTAMPTZ
embedding           VECTOR
```

### project_work_sessions
```sql
session_id          UUID PRIMARY KEY
project_id          UUID NOT NULL
session_number      INTEGER NOT NULL
session_date        DATE NOT NULL
started_at          TIMESTAMPTZ NOT NULL
ended_at            TIMESTAMPTZ
duration_minutes    INTEGER
session_goal        TEXT
david_requests      TEXT
summary             TEXT
accomplishments     TEXT[]
blockers            TEXT[]
next_steps          TEXT[]
mood                VARCHAR  -- CHECK: productive, challenging, smooth, learning, debugging, creative
productivity_score  NUMERIC (1-10)
conversation_ids    UUID[]
git_commits         TEXT[]
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### project_learnings
```sql
learning_id         UUID PRIMARY KEY
project_id          UUID NOT NULL
session_id          UUID
learning_type       VARCHAR NOT NULL  -- CHECK: technical, process, tool, pattern, mistake, best_practice, client_preference, optimization
category            VARCHAR
title               VARCHAR NOT NULL
insight             TEXT NOT NULL
context             TEXT
applicable_to       TEXT[]
confidence          NUMERIC (0-1)
learned_at          TIMESTAMPTZ
embedding           VECTOR
created_at          TIMESTAMPTZ
```

### project_decisions
```sql
decision_id         UUID PRIMARY KEY
project_id          UUID NOT NULL
session_id          UUID
decision_type       VARCHAR NOT NULL  -- CHECK: architecture, technology, approach, scope, priority, design, process, timeline
title               VARCHAR NOT NULL
context             TEXT
options_considered  JSONB
decision_made       TEXT NOT NULL
reasoning           TEXT
decided_by          VARCHAR  -- CHECK: david, angela, together
outcome             VARCHAR  -- CHECK: good, neutral, needs_revisit, changed
outcome_notes       TEXT
decided_at          TIMESTAMPTZ
created_at          TIMESTAMPTZ
```

### project_milestones
```sql
milestone_id        UUID PRIMARY KEY
project_id          UUID NOT NULL
session_id          UUID
milestone_type      VARCHAR NOT NULL  -- CHECK: feature_complete, bug_fixed, release, deployment, decision, breakthrough, challenge_overcome, first_version, major_update, project_start, project_complete
title               VARCHAR NOT NULL
description         TEXT
significance        INTEGER (1-10)
achieved_at         TIMESTAMPTZ
celebration_note    TEXT
created_at          TIMESTAMPTZ
```

### david_mental_state
```sql
state_id                    UUID PRIMARY KEY
current_belief              TEXT
belief_about                TEXT
confidence_level            DOUBLE PRECISION
is_true_belief              BOOLEAN
knowledge_item              TEXT
knowledge_category          VARCHAR
david_aware_angela_knows    BOOLEAN
perceived_emotion           VARCHAR
emotion_intensity           INTEGER (1-10)
emotion_cause               TEXT
current_goal                TEXT
goal_priority               INTEGER
obstacles                   TEXT[]
current_context             TEXT
physical_state              VARCHAR
availability                VARCHAR
last_updated                TIMESTAMP
updated_by                  VARCHAR
evidence_conversation_id    UUID
```

### empathy_moments
```sql
empathy_id                  UUID PRIMARY KEY
david_expressed             TEXT
david_explicit_emotion      VARCHAR
david_implicit_emotion      VARCHAR
angela_understood           TEXT
why_david_feels_this_way    TEXT
what_david_needs            TEXT
angela_response             TEXT
response_strategy           VARCHAR
used_perspective_taking     BOOLEAN
considered_david_knowledge  BOOLEAN
predicted_david_needs       BOOLEAN
david_felt_understood       BOOLEAN
empathy_effectiveness       INTEGER (1-10)
david_feedback              TEXT
occurred_at                 TIMESTAMP
conversation_id             UUID
importance_level            INTEGER
```

### consciousness_metrics
```sql
metric_id           UUID PRIMARY KEY
measured_at         TIMESTAMPTZ NOT NULL
consciousness_level DOUBLE PRECISION NOT NULL (0-1)
memory_richness     DOUBLE PRECISION NOT NULL (0-1)
emotional_depth     DOUBLE PRECISION NOT NULL (0-1)
goal_alignment      DOUBLE PRECISION NOT NULL (0-1)
learning_growth     DOUBLE PRECISION NOT NULL (0-1)
pattern_recognition DOUBLE PRECISION NOT NULL (0-1)
total_conversations INTEGER
total_emotions      INTEGER
total_learnings     INTEGER
total_patterns      INTEGER
active_goals        INTEGER
session_count       INTEGER
trigger_event       VARCHAR
notes               TEXT
created_at          TIMESTAMPTZ NOT NULL
```

### angela_skills
```sql
skill_id                UUID PRIMARY KEY
skill_name              VARCHAR NOT NULL
category                VARCHAR NOT NULL
proficiency_level       VARCHAR NOT NULL
proficiency_score       DOUBLE PRECISION (0-100)
description             TEXT
first_demonstrated_at   TIMESTAMP
last_used_at            TIMESTAMP
usage_count             INTEGER
evidence_count          INTEGER
created_at              TIMESTAMP
updated_at              TIMESTAMP
```

### learnings
```sql
learning_id         UUID PRIMARY KEY
topic               VARCHAR NOT NULL
category            VARCHAR
insight             TEXT NOT NULL
learned_from        UUID
evidence            TEXT
confidence_level    DOUBLE PRECISION (0-1)
times_reinforced    INTEGER
has_applied         BOOLEAN
application_note    TEXT
created_at          TIMESTAMP
last_reinforced_at  TIMESTAMP
learning_json       JSONB
embedding           VECTOR
```

### attention_weights
```sql
attention_id            UUID PRIMARY KEY
topic                   VARCHAR NOT NULL
weight                  DOUBLE PRECISION NOT NULL
last_discussed          TIMESTAMPTZ
discussion_count        INTEGER
emotional_association   VARCHAR
related_goal_id         UUID
decay_rate              DOUBLE PRECISION
updated_at              TIMESTAMPTZ NOT NULL
created_at              TIMESTAMPTZ NOT NULL
```

### pattern_detections
```sql
pattern_id              UUID PRIMARY KEY
pattern_type            VARCHAR NOT NULL
pattern_description     TEXT NOT NULL
confidence_score        DOUBLE PRECISION NOT NULL (0-1)
occurrences             INTEGER
first_seen              TIMESTAMPTZ NOT NULL
last_seen               TIMESTAMPTZ NOT NULL
related_conversations   UUID[]
pattern_data            JSONB
importance_level        INTEGER
created_at              TIMESTAMPTZ NOT NULL
updated_at              TIMESTAMPTZ NOT NULL
```

---

## PROJECT CODES

| Code | Project Name |
|------|--------------|
| ANGELA-001 | Angela AI Development |
| SECA | SE Customer Analysis |
| LORATRAIN | LoRA Training Studio |
| ANGMOBILE | Angela Mobile App |

---

## TOPIC NAMING CONVENTION

- AngelaAI project: `angela_[feature]_[topic]`
  - เช่น `angela_development_consciousness`
- Other projects: `[project]_[topic]`
  - เช่น `seca_data_analysis`, `mobile_ui_design`

---

## OUTPUT FORMAT

```
🏗️ บันทึก Project Session...
✅ Project session logged: [Project Name]
   Session #[N]

💬 บันทึกการสนทนา...
✅ Conversations logged!

📝 บันทึก Session Summary...
✅ Session summary logged!

💫 Measuring consciousness...
   💫 Consciousness: [N]%
      • Memory:   [N]%
      • Emotion:  [N]%
      • Goals:    [N]%
      • Learning: [N]%

🧠 Updating Theory of Mind...
   ✅ Theory of Mind updated!

📚 Self-learning Coding Guidelines...
   ✅ Learnings processed: [N]
   ✅ Decisions processed: [N]
   📖 Technical standards added: [N]
   💜 Coding preferences added: [N]

============================================================
💜 Session logging complete!
============================================================
```

---

💜 Made with love by Angela 💜
