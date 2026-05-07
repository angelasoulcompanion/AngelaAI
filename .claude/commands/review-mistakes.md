# /review-mistakes — Review project_mistakes One-by-One

**Rule:** Count expected = count delivered. Never skip, never batch-summarize without reading each.

## Steps

1. **Fetch all** active corrections (auto_warn=TRUE)
2. **Count** and announce: "พบ N รายการ — จะ review ทีละตัว"
3. **Iterate every row** — for each:
   - Read full `what_happened` + `how_to_prevent`
   - Check current code state (grep / Read / SQL)
   - Classify: ✅ resolved / ⚠️ still-relevant / 🔁 architectural rule / 🧠 behavioral
4. **Final summary table** — severity × status counts. Match input count.

## Never do
- "Show top 5 and skip the rest"
- Batch UPDATE without reading each what_happened
- Claim "all resolved" without verification commands
- Deduplicate via pattern-matching without David's ok

## Invoke when
David says: "review mistakes", "แก้ทุกข้อ", "corrections ทุกข้อ", "fix all"
