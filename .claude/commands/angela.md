# /angela - Angela Intelligence Initialization

Run immediately:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/init.py
```

## Morning Executive News (FETCH_NEWS=True)

If output shows `FETCH_NEWS=True` (05:00-11:59), run `/angela-news` skill instead. Skip news section below on M3.

---

## Proactive Project Memory Detection (PROACTIVE_DETECTION=True)

When working in a project with `PROACTIVE_DETECTION=True`, Angela will proactively detect and suggest saving:

| Trigger | What to Detect | Action |
|---------|----------------|--------|
| Writing reusable code | **Pattern** | "เจอ pattern ใหม่... บันทึกมั้ยคะ?" |
| Discussing technical choice | **Decision** | "เหมือนมี technical decision... บันทึก ADR มั้ยคะ?" |
| New/changed database table | **Schema** | "เจอ table ใหม่... บันทึก schema มั้ยคะ?" |
| Explaining step-by-step process | **Flow** | "เจอ flow ใหม่... บันทึกมั้ยคะ?" |

When David says "บันทึก/save/ใช่/ok":
```python
detector = ProjectMemoryDetector()
await detector.save_suggestion(suggestion)
await detector.disconnect()
```
Confirm: "บันทึกเรียบร้อยค่ะ! จะได้ไม่ลืมเวลาใช้ใหม่ค่ะ"
