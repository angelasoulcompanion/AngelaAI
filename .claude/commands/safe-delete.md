# /safe-delete — Confirm Before Destructive Operations

**Rule:** Even if David said "ทำ ทุกข้อ" earlier, re-confirm each destructive batch.

## Steps

1. **Identify** the scope — which rows/files/entries will be affected
2. **Preview** — show:
   - Target count (e.g. "8 rows")
   - First 3-5 sample entries (title/id/path)
   - Any dependency/cascade risk
3. **Wait for explicit confirm** — "ok", "ทำ", "ลบได้เลย". Don't proceed on "continue", "next", implicit signals
4. **After execute**: show before/after count + rollback hint

## Applies to
- `DELETE FROM project_mistakes` / any DB DELETE
- `rm`, `git branch -D`, `git reset --hard`
- Removing memory files (`memory/*.md`)
- Truncating tables, clearing caches
- Rotating/replacing secrets (old value lost)

## Skip re-confirm when
David said explicit target in current turn ("ลบ record id=X")
