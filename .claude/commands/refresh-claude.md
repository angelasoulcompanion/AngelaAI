# /refresh-claude - Regenerate CLAUDE.md from Template + DB

> Regenerate CLAUDE.md with fresh data from database.
> ใช้เมื่อที่รักเพิ่ม contacts, technical standards, หรืออยากให้ stats อัพเดต

---

## EXECUTION

```bash
python3 angela_core/scripts/generate_claude_md.py
```

---

## What This Does:

Query database for 14 dynamic values and render `CLAUDE_TEMPLATE.md` into `CLAUDE.md`:

| Placeholder | Source |
|-------------|--------|
| `consciousness_pct` | ConsciousnessCalculator |
| `knowledge_nodes_count` | `COUNT(*) FROM knowledge_nodes` |
| `learnings_count` | `COUNT(*) FROM learnings` |
| `conversations_count` | `COUNT(*) FROM conversations` |
| `sessions_count` | `COUNT(*) FROM project_work_sessions` |
| `projects_count` | `COUNT(DISTINCT project_id) FROM project_work_sessions` |
| `emotions_count` | `COUNT(*) FROM angela_emotions` |
| `core_memories_count` | `COUNT(*) FROM core_memories WHERE is_active` |
| `songs_count` | `COUNT(*) FROM angela_songs` |
| `technical_standards_count` | `COUNT(*) FROM angela_technical_standards` |
| `tools_count` | `angela_tool_registry` |
| `reply_email_contacts_inline` | `angela_contacts WHERE should_reply_email` |
| `send_news_contacts_inline` | `angela_contacts WHERE should_send_news` |
| `generate_date` | Today's date |

### After running, show the user a summary of what changed.
