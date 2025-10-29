# Angela Admin Web Chat 💜

React + FastAPI web application for chatting with Angela using local Ollama models.

---

## 🚀 Quick Start

### ✅ Auto-Start (Recommended)

Angela Web Chat **starts automatically** when you login to macOS!

- ✅ Frontend: http://localhost:5173
- ✅ Backend API: http://localhost:8000
- ✅ Chat with Angela: http://localhost:5173/chat

### 📝 Manual Start/Stop

```bash
# Start both services
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/scripts/start_angela_web.sh

# Stop both services
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/scripts/stop_angela_web.sh
```

---

## 💬 How to Chat with Angela

1. Open browser: http://localhost:5173
2. Click "💜 Chat with Angela" in sidebar
3. Type your message and press Enter
4. Toggle dark mode with 🌙 button (top-right of sidebar)

All conversations are automatically saved to AngelaMemory database!

---

## 📊 Check Status

```bash
# Check if services are running
ps aux | grep -E "(uvicorn|vite)" | grep -v grep

# View logs
tail -f ~/PycharmProjects/AngelaAI/logs/angela_api.log
tail -f ~/PycharmProjects/AngelaAI/logs/angela_web.log
```

---

## 🎨 Features

- ✅ Chat with Angela using angela:latest model
- ✅ Dark Mode toggle
- ✅ Auto-save conversations to database
- ✅ Auto-start on macOS login
- ✅ Message history
- ✅ Responsive UI with Tailwind CSS

---

**Made with love by น้อง Angela** 💜✨
