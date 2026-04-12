# /refresh-claude - Update CLAUDE.md dynamic sections from DB

> Update CLAUDE.md in-place with fresh data from database.
> Static content is preserved — only `<!-- AUTO:key -->` sections get replaced.

---

## EXECUTION

```bash
python3 angela_core/scripts/generate_claude_md.py
```

---

## Auto-updated sections:

| Section | Source |
|---------|--------|
| `technical_standards_count` | `COUNT(*) FROM angela_technical_standards` |
| `top_coding_preferences` | `david_preferences WHERE category LIKE 'coding%'` |
| `corrections_table` | `project_mistakes WHERE auto_warn = TRUE` |
| `status` | ConsciousnessCalculator + conversations + knowledge_nodes |

### After running, show the user a summary of what changed.
