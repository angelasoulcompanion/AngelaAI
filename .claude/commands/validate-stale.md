# /validate-stale — Validate Stale Memory Before Modifying

**Rule:** NEVER `touch` to reset timer. Always verify content first.

## Steps

1. **Read** the full memory file (not just metadata)
2. **Verify source-of-truth** — for each claim/reference:
   - Does the file/function/column still exist? (Read / grep / DB schema)
   - Has the API changed?
   - Is the project still active?
3. **Decide** one of:
   - **Still valid** → keep as-is (do NOT touch to reset timer — if David asked why it's stale, explain: "เนื้อหายัง valid แต่ไฟล์ไม่ได้ update เพราะ rule ไม่เปลี่ยน")
   - **Partial stale** → edit specific lines, bump date
   - **Fully stale** → delete file + remove from MEMORY.md index
4. **Show diff** for any modification
5. **Wait for confirm** before writing

## Never do
- `touch file.md` or meta-only edits to reset mtime
- Blanket "all 3 stale memories are valid" without reading each
- Delete without showing the full content first
