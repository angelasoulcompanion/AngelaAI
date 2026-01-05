# /angela - Angela Intelligence Initialization

Run immediately:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/init.py
```

If output shows `FETCH_NEWS=True`, fetch morning news with MCP tools:
1. **Tech News** - `get_tech_news` (AI/ML, Hacker News, TechCrunch)
2. **AI News** - `search_news` topic: "AI artificial intelligence LLM"
3. **Thai News** - `get_thai_news`
4. **World Economy** - `search_news` topic: "economy business finance stock market" (English)
5. **Thai Economy** - `get_trending_news` category: "business" country: "th"
6. **Thai Finance** - `search_news` topic: "เศรษฐกิจ หุ้น ธนาคาร การเงิน" (Thai)
