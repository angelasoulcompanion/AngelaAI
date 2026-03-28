# /self-learn - Force Angela Self-Learning Cycle

> Force run Angela's learning pipeline: DEEP LEARN → CORRECTIONS → PREFERENCES → KB SYNC
> ใช้เมื่อที่รักอยากให้น้องเรียนรู้ทันที ไม่ต้องรอ daemon

---

## EXECUTION

Create temp script → run → cleanup:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/self_learn_cycle.py
```

---

## What This Does:

| Phase | Service | What Happens |
|-------|---------|-------------|
| **DEEP LEARN** | UnifiedConversationProcessor | Process recent conversations → extract emotions + learnings |
| **CORRECTIONS** | CorrectionExtractor | Scan for mistakes David corrected → save to project_mistakes |
| **PREFERENCES** | PreferenceLearningService | Detect coding/communication preferences → save |
| **KB SYNC** | KnowledgeBaseService | Sync new learnings to unified_knowledge_base |
| **STATS** | KnowledgeBaseService | Show current KB stats |

### Learning Pipeline:
```
DEEP LEARN → CORRECTIONS → PREFERENCES → KB SYNC → STATS
```

### When to Use:
- `/self-learn` — Force immediate learning
- After important conversations or teaching Angela new things
- เมื่ออยากให้น้องฉลาดขึ้นทันที
