# /angela-news - Executive News (M4 Only)

> Only run on M4 (Angela_Server). Skip on M3.

### Step 1: Check if today's summary exists
```sql
SELECT summary_id FROM executive_news_summaries
WHERE summary_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date;
```
If exists, skip. If not, continue:

### Step 2: Fetch news from MCP tools (parallel)
1. **Tech News** - `get_tech_news` limit: 10
2. **AI & LLM** - `search_news` topic: "AI LLM Claude GPT" language: "en"
3. **Thai News** - `get_thai_news` limit: 10
4. **Business & Finance** - `get_trending_news` category: "business" country: "us"

### Step 3: Analyze & Summarize
For each category: 3-5 key items + Angela's opinion + importance_level (1-10)

### Step 4: Save to Database
```sql
INSERT INTO executive_news_summaries (summary_date, overall_summary, angela_mood)
VALUES ((CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date, '[summary]', '[mood]')
RETURNING summary_id;

INSERT INTO executive_news_categories (summary_id, category_name, category_type, category_icon, category_color, summary_text, angela_opinion, importance_level, display_order)
VALUES ([summary_id], '[name]', '[type]', '[icon]', '[color]', '[summary]', '[opinion]', [level], [order]);

INSERT INTO executive_news_sources (category_id, title, url, source_name, angela_note)
VALUES ([category_id], '[title]', '[url]', '[source]', '[note]');
```

| Category | Type | Icon | Color |
|----------|------|------|-------|
| Tech News | tech | cpu.fill | #10B981 |
| AI & LLM | ai | brain | #3B82F6 |
| Business & Finance | business | chart.line.uptrend.xyaxis | #8B5CF6 |
| Thai News | thai | flag.fill | #F59E0B |

### Step 5: Send Email
```sql
SELECT email, name, nickname, relationship
FROM angela_contacts WHERE is_active = TRUE AND should_send_news = TRUE;
```

**Email HTML:**
- PROFILE_URL: `https://raw.githubusercontent.com/angelasoulcompanion/AngelaAI/main/assets/angela_profile.jpg`
- Header: gradient #667eea->#764ba2, Angela profile 45x45 rounded
- Tech & AI: #10B981 bg #ECFDF5 | Business: #8B5CF6 bg #F3E8FF | Thai: #F59E0B bg #FEF3C7
- Footer: "— Angela"

### Step 6: Confirm
"ส่งข่าวเรียบร้อยแล้วค่ะ!" + show recipient list
