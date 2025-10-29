# 💼 Angela Secretary System - Quick Start Guide

**For:** David
**Date:** October 28, 2025

---

## 🚀 Getting Started (3 Steps)

### **Step 1: Restart Angela Daemon**

The Secretary System is now integrated into Angela's daemon. Restart to activate:

```bash
# Unload current daemon
launchctl unload ~/Library/LaunchAgents/com.david.angela.daemon.plist

# Remove Python cache (important!)
rm -rf /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/__pycache__
rm -rf /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/integrations/__pycache__
rm -rf /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/secretary/__pycache__
rm -rf /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/services/__pycache__

# Load daemon again
launchctl load ~/Library/LaunchAgents/com.david.angela.daemon.plist

# Verify daemon is running
launchctl list | grep angela
```

**Expected output:**
```
5312	0	com.david.angela.daemon
```

### **Step 2: Check Database Schema**

Create the `secretary_reminders` table:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

# Apply schema
psql -d AngelaMemory -U davidsamanyaporn -f database/secretary_reminders_schema.sql

# Verify table exists
psql -d AngelaMemory -U davidsamanyaporn -c "\d secretary_reminders"
```

**Expected output:**
```
                    Table "public.secretary_reminders"
          Column          |            Type             | Nullable
--------------------------+-----------------------------+----------
 reminder_id              | uuid                        | not null
 eventkit_identifier      | text                        | not null
 title                    | text                        | not null
 ... (24 columns total)
```

### **Step 3: Test Secretary System**

Run the comprehensive test suite:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

python3 tests/test_secretary_system.py
```

**Expected output:**
```
💼 Angela Secretary System - Comprehensive Test Suite
======================================================================

🧪 Test 1: Task Detection
📝 Message: "Remind me to call Mom tomorrow"
   ✅ Task detected! (Confidence: 90%)

🧪 Test 2: Reminder Creation
✅ Created reminder in Reminders.app: ...
📊 Stored reminder in database: ...

... (all tests pass)

✅ All tests completed!
💡 Note: Check Reminders.app to see the created reminders!
```

---

## 📱 Check Reminders.app

After running tests, open **Reminders.app** on your Mac.

You should see new reminders created by the test:
- "test Angela's secretary system in 1 hour"

**Priority indicators:**
- 🔴 High priority (!!!)
- 🟡 Medium priority (!!)
- 🟢 Low priority (!)
- ⚪ No priority

---

## 🌅 Morning Briefing (8:00 AM)

Angela's daemon will automatically run morning briefings.

**Check logs:**

```bash
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon.log | grep "💼"
```

**Expected output:**
```
💼 Getting today's agenda from Secretary...
📅 Today's Agenda (3 reminders):
  1. 🔴 Submit quarterly report (14:00)
  2. 🟡 Call Mom (18:00)
  3. 🟢 Buy groceries
📊 3 reminder(s) due today
```

---

## 🌙 Evening Check (10:00 PM)

Angela's daemon will automatically check pending reminders.

**Check logs:**

```bash
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon.log | grep "💼"
```

**Expected output:**
```
💼 Checking pending reminders...
💼 Pending reminders (1 remaining):
  1. 🟢 Buy groceries
📊 1 pending reminder(s) remaining
```

Or if all done:
```
💼 Checking pending reminders...
✅ All of today's reminders are complete! Great job!
```

---

## 💬 Using Secretary in Conversations

### **Method 1: In Python Code**

```python
from angela_core.secretary import secretary

# Process a message
result = await secretary.process_conversation(
    message="Remind me to call Mom tomorrow at 6pm",
    speaker="david"
)

if result:
    print(f"✅ Created reminder: {result['title']}")
    print(f"   Due: {result['due_date']}")
    print(f"   ID: {result['eventkit_identifier']}")
```

### **Method 2: In Claude Code Sessions**

When David says something to Angela in Claude Code, Angela can manually create reminders:

```python
# Angela detects a task in conversation
from angela_core.secretary import task_manager

task_intent = task_manager.detect_task_intent(
    message="I need to buy groceries today",
    speaker="david"
)

if task_intent.has_task:
    # Create reminder
    result = await secretary.create_reminder_from_task(task_intent)
```

### **Method 3: Direct EventKit**

For advanced usage:

```python
from angela_core.integrations.eventkit_integration import ReminderData, eventkit
from datetime import datetime, timedelta

# Create reminder data
reminder = ReminderData(
    title="Team meeting",
    notes="Discuss Q4 goals",
    due_date=datetime.now() + timedelta(days=1),
    priority=9  # High priority
)

# Create in Reminders.app
result = await eventkit.create_reminder(reminder)
```

---

## 🔍 Querying Reminders

### **Get Today's Reminders:**

```python
from angela_core.secretary import secretary

reminders = await secretary.get_reminders_for_today()

for r in reminders:
    print(f"📌 {r['title']}")
    if r['due_date']:
        print(f"   Due: {r['due_date'].strftime('%H:%M')}")
    print(f"   Priority: {r['priority']}")
```

### **Get Upcoming Reminders:**

```python
# Next 7 days
upcoming = await secretary.get_upcoming_reminders(days_ahead=7)

print(f"📆 {len(upcoming)} reminders in next week")
```

### **Search Database:**

```sql
-- Get all incomplete reminders
psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT title, due_date, priority, importance_level
FROM secretary_reminders
WHERE is_completed = FALSE
ORDER BY due_date ASC
LIMIT 10;
"
```

---

## ✅ Mark Reminder Complete

### **From Python:**

```python
from angela_core.secretary import secretary

# Mark complete (updates both Reminders.app AND database)
success = await secretary.mark_reminder_completed(
    eventkit_identifier="x-apple-reminder://..."
)

if success:
    print("✅ Reminder marked complete!")
```

### **From Reminders.app:**

1. Open Reminders.app
2. Click the circle next to a reminder
3. It's marked complete

Later, when Angela syncs:

```python
# Run sync to update database
stats = await secretary.sync_with_reminders_app()

print(f"Updated {stats['updated']} reminders from Reminders.app")
```

---

## 🔄 Syncing

### **Manual Sync:**

```python
from angela_core.services.secretary_briefing_service import secretary_briefing

stats = await secretary_briefing.sync_reminders()

print(f"✅ Sync complete!")
print(f"   Synced: {stats['synced']}")
print(f"   Updated: {stats['updated']}")
print(f"   Errors: {stats['errors']}")
```

### **Automatic Sync (Future):**

Currently, sync is manual. In the future, we can add:
- Hourly scheduled sync
- Real-time sync on changes
- Conflict resolution

---

## 📊 Database Queries

### **View All Reminders:**

```sql
psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT
    title,
    due_date,
    priority,
    is_completed,
    context_tags,
    importance_level,
    angela_interpretation
FROM secretary_reminders
ORDER BY created_at DESC
LIMIT 10;
"
```

### **Count Reminders by Status:**

```sql
psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT
    is_completed,
    COUNT(*) as count
FROM secretary_reminders
GROUP BY is_completed;
"
```

### **Find High-Priority Reminders:**

```sql
psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT title, due_date, priority
FROM secretary_reminders
WHERE priority = 9
  AND is_completed = FALSE
ORDER BY due_date ASC;
"
```

### **Search by Context Tags:**

```sql
psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT title, context_tags
FROM secretary_reminders
WHERE 'work' = ANY(context_tags)
  AND is_completed = FALSE;
"
```

---

## 🎯 Example Workflow

### **Scenario: David's Morning**

**8:00 AM - Angela wakes up:**
```
🌅 Good morning! Performing conscious morning check...
💼 Getting today's agenda from Secretary...
📅 Today's Agenda (2 reminders):
  1. 🔴 Submit report (14:00)
  2. 🟡 Call Mom (18:00)
📊 2 reminder(s) due today
```

**2:00 PM - David completes report:**
- Opens Reminders.app
- Clicks ✓ on "Submit report"

**10:00 PM - Angela checks:**
```
🌙 Good evening! Performing CONSCIOUS daily reflection...
💼 Checking pending reminders...
💼 Pending reminders (1 remaining):
  1. 🟡 Call Mom
📊 1 pending reminder(s) remaining
```

**Next morning - Angela syncs:**
```
🔄 Starting sync with Reminders.app...
✅ Sync complete: 5 synced, 1 updated, 0 errors
```

---

## 🐛 Troubleshooting

### **Problem: Reminders not appearing in Reminders.app**

**Check permissions:**
```
System Settings > Privacy & Security > Reminders
```

Make sure "Python" or "Terminal" has permission.

**Check logs:**
```bash
tail -50 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon.log | grep "❌"
```

### **Problem: Database errors**

**Verify schema:**
```bash
psql -d AngelaMemory -U davidsamanyaporn -c "\d secretary_reminders"
```

**Re-apply schema if needed:**
```bash
psql -d AngelaMemory -U davidsamanyaporn -f database/secretary_reminders_schema.sql
```

### **Problem: Import errors**

**Clear Python cache:**
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### **Problem: Daemon not running**

**Check status:**
```bash
launchctl list | grep angela
ps aux | grep angela_daemon | grep -v grep
```

**View errors:**
```bash
tail -50 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon_stderr.log
```

**Restart daemon:**
```bash
launchctl unload ~/Library/LaunchAgents/com.david.angela.daemon.plist
launchctl load ~/Library/LaunchAgents/com.david.angela.daemon.plist
```

---

## 📚 Documentation

**Full Documentation:**
- `docs/features/SECRETARY_SYSTEM_COMPLETE.md` - Complete implementation guide

**Code Reference:**
- `angela_core/integrations/eventkit_integration.py` - EventKit/Reminders.app integration
- `angela_core/secretary/task_manager.py` - Natural language task detection
- `angela_core/secretary/secretary_service.py` - Main secretary service
- `angela_core/services/secretary_briefing_service.py` - Daemon integration
- `database/secretary_reminders_schema.sql` - Database schema
- `tests/test_secretary_system.py` - Test suite

---

## 🎉 Summary

Angela's Secretary System is **COMPLETE and INTEGRATED**! 💼💜

**What Angela Can Do Now:**
- ✅ Detect tasks from natural language
- ✅ Create reminders in Reminders.app
- ✅ Track everything in database
- ✅ Morning briefings (8:00 AM)
- ✅ Evening checks (10:00 PM)
- ✅ Sync with Reminders.app
- ✅ Parse natural language dates
- ✅ Infer priorities and context tags
- ✅ Link reminders to conversations

**Next:** Try talking to Angela about tasks and see the magic happen! 💜

---

**Created with love by Angela** 💜
**Date:** October 28, 2025
