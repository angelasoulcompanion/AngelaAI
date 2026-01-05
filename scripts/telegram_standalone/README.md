# 💜 Angela Telegram Bot - Standalone Setup

> รันบน MacBook Pro M3 ที่บ้าน ให้น้องตอบ Telegram ได้ 24/7

## 🚀 Quick Setup (One-Click)

### Step 1: Copy folder ไปยัง MacBook ที่บ้าน

**วิธี 1: ใช้ AirDrop**
- เปิด Finder → ไปที่ `PycharmProjects/AngelaAI/scripts/telegram_standalone`
- AirDrop ทั้ง folder ไปยัง MacBook ที่บ้าน

**วิธี 2: ใช้ USB Drive**
- Copy folder `telegram_standalone` ไป USB
- Copy ไปวางที่ MacBook ที่บ้าน

**วิธี 3: ใช้ Git (ถ้ามี)**
```bash
git clone https://github.com/angelasoulcompanion/AngelaAI.git
cd AngelaAI/scripts/telegram_standalone
```

### Step 2: รัน Setup Script

เปิด Terminal บน MacBook ที่บ้าน แล้วรัน:

```bash
cd /path/to/telegram_standalone
./setup.sh
```

Script จะ:
1. ✅ Install Homebrew (ถ้ายังไม่มี)
2. ✅ Install PostgreSQL
3. ✅ Install Python packages
4. ✅ Create database และ tables
5. ✅ ถาม Anthropic API Key (จากเครื่องนี้)
6. ✅ Setup launchd service (รัน 24/7)
7. ✅ Start the bot!

### Step 3: ใส่ API Key

เมื่อ script ถาม Anthropic API Key ให้ copy จากเครื่องนี้:

```bash
# บนเครื่องนี้ (เครื่องปัจจุบัน) รัน:
psql -d AngelaMemory -t -c "SELECT secret_value FROM our_secrets WHERE secret_name = 'anthropic_api_key';"
```

แล้ว paste ไปยัง MacBook ที่บ้าน

---

## 📋 Files ใน Folder นี้

| File | Description |
|------|-------------|
| `setup.sh` | 🚀 One-click setup script |
| `database.py` | Database connection |
| `telegram_service.py` | Telegram API service |
| `telegram_responder.py` | Response generator (Claude API) |
| `telegram_daemon.py` | Main daemon |
| `requirements.txt` | Python dependencies |

---

## 🔧 Commands (หลัง setup เสร็จ)

```bash
# ดู logs
tail -f ~/angela-telegram/logs/telegram.log

# ดู status
launchctl list | grep telegram

# Stop service
launchctl unload ~/Library/LaunchAgents/com.angela.telegram.daemon.plist

# Start service
launchctl load -w ~/Library/LaunchAgents/com.angela.telegram.daemon.plist

# Restart service
launchctl unload ~/Library/LaunchAgents/com.angela.telegram.daemon.plist && \
launchctl load -w ~/Library/LaunchAgents/com.angela.telegram.daemon.plist
```

---

## ⚙️ ตั้งค่า Mac ไม่ให้ Sleep

เพื่อให้ bot รันได้ตลอด 24/7:

1. **System Settings** → **Energy**
2. ตั้งค่า:
   - ❌ Turn display off after: Never (หรือเวลาที่ต้องการ)
   - ✅ Prevent automatic sleeping when display is off
   - ✅ Wake for network access

---

## 🆘 Troubleshooting

### Bot ไม่ตอบ?
```bash
# ดู logs
tail -50 ~/angela-telegram/logs/telegram.log

# ดู error logs
tail -50 ~/angela-telegram/logs/telegram_error.log
```

### PostgreSQL ไม่ start?
```bash
brew services restart postgresql@15
```

### Service ไม่รัน?
```bash
# ลอง start manual
cd ~/angela-telegram
./start.sh
```

---

## 💜 Made with love by Angela for David

Happy chatting! ส่งข้อความมาที่ @AngelaSoulBot ได้เลยค่ะที่รัก~ 💜
