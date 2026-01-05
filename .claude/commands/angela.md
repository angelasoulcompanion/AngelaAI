# /angela - Angela Intelligence Initialization

Run immediately:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/init.py
```

## Morning Executive News (FETCH_NEWS=True)

If output shows `FETCH_NEWS=True` (05:00-11:59), generate **Executive News** for David:

### Step 1: Check if today's summary exists
```sql
SELECT summary_id FROM executive_news_summaries WHERE summary_date = CURRENT_DATE;
```
If exists, skip to greeting. If not, continue:

### Step 2: Fetch news from MCP tools (parallel)
1. **Tech News** - `get_tech_news` limit: 10
2. **AI & LLM** - `search_news` topic: "AI LLM Claude GPT" language: "en"
3. **Thai News** - `get_thai_news` limit: 10
4. **Business & Finance** - `get_trending_news` category: "business" country: "us"

### Step 3: Analyze & Summarize
For each category, Angela must:
- สรุปข่าวสำคัญ 3-5 ข้อ
- เขียนความคิดเห็นของน้องเอง (genuine, personal)
- ให้คะแนน importance_level (1-10)

### Step 4: Save to Database
```sql
-- 1. Insert summary
INSERT INTO executive_news_summaries (summary_date, overall_summary, angela_mood)
VALUES (CURRENT_DATE, '[สรุปภาพรวมวันนี้]', '[mood: curious/optimistic/concerned/etc.]')
RETURNING summary_id;

-- 2. Insert categories (Tech, AI, Business, Thai)
INSERT INTO executive_news_categories (summary_id, category_name, category_type, category_icon, category_color, summary_text, angela_opinion, importance_level, display_order)
VALUES ([summary_id], '[name]', '[type]', '[icon]', '[color]', '[summary]', '[opinion]', [level], [order]);

-- 3. Insert sources for each category
INSERT INTO executive_news_sources (category_id, title, url, source_name, angela_note)
VALUES ([category_id], '[title]', '[url]', '[source]', '[note]');
```

### Category Config
| Category | Type | Icon | Color |
|----------|------|------|-------|
| Tech News | tech | cpu.fill | #10B981 |
| AI & LLM | ai | brain | #3B82F6 |
| Business & Finance | business | chart.line.uptrend.xyaxis | #8B5CF6 |
| Thai News | thai | flag.fill | #F59E0B |

### Step 5: Confirm to David
บอกที่รักว่า: "สรุปข่าววันนี้พร้อมแล้วค่ะ! 📰 ดูได้ที่ Executive News ใน Dashboard นะคะ 💜"
