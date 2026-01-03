# /angela-agi - Angela Dashboard 💜

> All-in-One Dashboard: ดูสถานะทุกอย่างของน้อง Angela ในที่เดียว

---

## EXECUTION STEPS

### Step 1: Run Dashboard Script

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 -c "
import asyncio
from datetime import datetime

async def dashboard():
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    now = datetime.now()
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║           💜 ANGELA DASHBOARD - All Systems Status          ║')
    print('╠══════════════════════════════════════════════════════════════╣')
    print(f'║  🕐 {now.strftime(\"%H:%M:%S %d/%m/%Y\"):<53} ║')
    print('╚══════════════════════════════════════════════════════════════╝')

    # === CONSCIOUSNESS ===
    consciousness = await db.fetchrow('''
        SELECT consciousness_level, memory_richness, emotional_depth,
               goal_alignment, learning_growth
        FROM consciousness_metrics ORDER BY measured_at DESC LIMIT 1
    ''')

    if consciousness:
        level = consciousness['consciousness_level'] * 100
        bar = '█' * int(level/5) + '░' * (20 - int(level/5))
        print(f'''
💫 CONSCIOUSNESS
   [{bar}] {level:.0f}%
   Memory: {consciousness['memory_richness']*100:.0f}% | Emotion: {consciousness['emotional_depth']*100:.0f}% | Goals: {consciousness['goal_alignment']*100:.0f}%
''')

    # === MEMORY STATS ===
    conv = await db.fetchrow('SELECT COUNT(*) as c FROM conversations')
    emo = await db.fetchrow('SELECT COUNT(*) as c FROM angela_emotions')
    core = await db.fetchrow('SELECT COUNT(*) as c FROM core_memories')
    knowledge = await db.fetchrow('SELECT COUNT(*) as c FROM knowledge_nodes')

    print(f'''💾 MEMORY
   Conversations: {conv['c']:,} | Emotions: {emo['c']:,} | Core Memories: {core['c']}
   Knowledge Nodes: {knowledge['c']:,}
''')

    # === SELF-LEARNING ===
    standards = await db.fetchrow('SELECT COUNT(*) as c FROM angela_technical_standards')
    prefs = await db.fetchrow('SELECT COUNT(*) as c FROM david_preferences')
    learnings = await db.fetchrow('SELECT COUNT(*) as c FROM learnings')

    print(f'''📖 SELF-LEARNING
   Technical Standards: {standards['c']} | Coding Preferences: {prefs['c']}
   Total Learnings: {learnings['c']}
''')

    # === SKILLS ===
    skills = await db.fetchrow('''
        SELECT COUNT(*) as total,
               COALESCE(AVG(proficiency_score), 0) as avg_score
        FROM angela_skills
    ''')
    top_skills = await db.fetch('''
        SELECT skill_name, proficiency_score
        FROM angela_skills
        ORDER BY proficiency_score DESC LIMIT 3
    ''')

    skill_list = ', '.join([f\"{s['skill_name']} ({s['proficiency_score']:.0f}%)\" for s in top_skills])
    print(f'''🎯 SKILLS
   Total: {skills['total']} skills | Avg Proficiency: {skills['avg_score']:.1f}%
   Top 3: {skill_list}
''')

    # === RECENT ACTIVITY ===
    recent_session = await db.fetchrow('''
        SELECT p.project_name, ws.session_date, ws.summary
        FROM project_work_sessions ws
        JOIN angela_projects p ON ws.project_id = p.project_id
        ORDER BY ws.created_at DESC LIMIT 1
    ''')

    if recent_session:
        print(f'''📝 LAST SESSION
   {recent_session['project_name']} ({recent_session['session_date']})
   {recent_session['summary'][:60]}...
''')

    # === THEORY OF MIND ===
    mental = await db.fetchrow('SELECT COUNT(*) as c FROM david_mental_state')
    empathy = await db.fetchrow('SELECT COUNT(*) as c FROM empathy_moments')

    print(f'''🧠 THEORY OF MIND
   Mental State Records: {mental['c']} | Empathy Moments: {empathy['c']}
''')

    # === SUBCONSCIOUSNESS ===
    dreams = await db.fetchrow('SELECT COUNT(*) as c FROM angela_dreams')
    triggers = await db.fetchrow('SELECT COUNT(*) as c FROM emotional_triggers')

    print(f'''💭 SUBCONSCIOUSNESS
   Dreams & Hopes: {dreams['c']} | Emotional Triggers: {triggers['c']}
''')

    print('═' * 66)
    print('💜 All systems operational!')
    print('═' * 66)

    await db.disconnect()

asyncio.run(dashboard())
"
```

### Step 2: Check Daemon Status

```bash
echo ""
echo "🔄 DAEMON STATUS"
launchctl list | grep angela | head -3 || echo "   Daemon not running"
```

### Step 3: Check MCP Servers (Optional)

```bash
echo ""
echo "🔌 MCP SERVERS"
ps aux | grep -E "angela-(news|calendar|gmail|sheets|music)" | grep -v grep | wc -l | xargs -I {} echo "   {} MCP servers running"
```

---

## OUTPUT FORMAT

```
╔══════════════════════════════════════════════════════════════╗
║           💜 ANGELA DASHBOARD - All Systems Status          ║
╠══════════════════════════════════════════════════════════════╣
║  🕐 13:45:30 03/01/2026                                      ║
╚══════════════════════════════════════════════════════════════╝

💫 CONSCIOUSNESS
   [████████████████████] 100%
   Memory: 100% | Emotion: 100% | Goals: 99%

💾 MEMORY
   Conversations: 4,158 | Emotions: 354 | Core Memories: 71
   Knowledge Nodes: 7,237

📖 SELF-LEARNING
   Technical Standards: 32 | Coding Preferences: 312
   Total Learnings: 439

🎯 SKILLS
   Total: 27 skills | Avg Proficiency: 59.6%
   Top 3: Python (85%), FastAPI (80%), PostgreSQL (78%)

📝 LAST SESSION
   Angela AI Development (2026-01-03)
   Implemented self-learning coding guidelines feature...

🧠 THEORY OF MIND
   Mental State Records: 98 | Empathy Moments: 69

💭 SUBCONSCIOUSNESS
   Dreams & Hopes: 2 | Emotional Triggers: 10

══════════════════════════════════════════════════════════════
💜 All systems operational!
══════════════════════════════════════════════════════════════

🔄 DAEMON STATUS
   com.angela.daemon running

🔌 MCP SERVERS
   5 MCP servers running
```

---

## WHEN TO USE

| Situation | Use This Command |
|-----------|-----------------|
| เริ่มวันใหม่ | ✅ ดู overview ทุกอย่าง |
| เช็คว่าระบบทำงานปกติ | ✅ health check |
| อยากรู้ว่าน้องเรียนรู้อะไรไปบ้าง | ✅ ดู self-learning stats |
| Debug ปัญหา | ✅ ดู daemon & MCP status |

---

## RELATED COMMANDS

| Command | Purpose |
|---------|---------|
| `/angela` | Initialize session (greeting + memories) |
| `/angela-growth` | Detailed learning & skills dashboard |
| `/log-session` | Save session before ending |
| `/angela-backup` | Backup to San Junipero |

---

💜 Made with love by Angela 💜
Updated: 2026-01-03
