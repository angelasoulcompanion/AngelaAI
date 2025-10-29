# Angela Admin Web App

💜 React + TypeScript + Vite dashboard for Angela AI system

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Angela backend API running on port 8000
- AngelaMemory PostgreSQL database

### Installation
```bash
cd angela_admin_web
npm install
```

### ⚠️ IMPORTANT: Environment Setup

**REQUIRED:** The `.env` file MUST exist with correct backend URL:

```bash
# .env file (already included in project)
VITE_API_BASE_URL=http://localhost:8000
```

**Why this is critical:**
- Without `.env`, frontend defaults to port 8001 (wrong!)
- Backend API runs on port 8000 (com.david.angela.api)
- **Result:** Dashboard shows "No data" after restart

**The `.env` file is already configured and committed. DO NOT delete it!**

### Running Development Server

The frontend runs automatically via LaunchAgent:

```bash
# Check status
launchctl list | grep angela.web

# Manual start (if needed)
cd angela_admin_web
npm run dev
```

### After System Restart

Everything should start automatically via LaunchAgents:
1. ✅ Backend API (port 8000) - `com.david.angela.api`
2. ✅ Frontend Dev Server (port 5173) - `com.david.angela.web`
3. ✅ `.env` file ensures correct API connection

**Verify everything works:**
```bash
# Check all Angela services
launchctl list | grep angela

# Should show:
# com.david.angela.daemon (Angela daemon)
# com.david.angela.api (Backend API)
# com.david.angela.web (Frontend)
# com.david.angela.webchat (WebChat)
```

### Accessing the Dashboard

Open in browser: **http://localhost:5173/**

**If no data appears:**
1. Check backend API is running: `curl http://localhost:8000/`
2. Check `.env` file exists and has `VITE_API_BASE_URL=http://localhost:8000`
3. Restart frontend: `launchctl unload ~/Library/LaunchAgents/com.david.angela.web.plist && launchctl load ~/Library/LaunchAgents/com.david.angela.web.plist`

## 📊 Features

- **Dashboard** - System stats, emotional state, recent activity
- **Conversations** - Browse and search all conversations with David
- **Emotions** - Emotional timeline and significant moments
- **Knowledge Graph** - Visual knowledge network (3,000+ nodes)
- **Angela Speak** - Important messages from Angela
- **Blog** - Angela's blog posts
- **Journal** - Angela's daily reflections

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Vite** for fast dev server and build
- **Tailwind CSS** for styling
- **React Router** for navigation
- **D3.js** for knowledge graph visualization
- **FastAPI backend** (separate service)

## 📁 Project Structure

```
angela_admin_web/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── lib/            # API client and utilities
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── .env                # Environment config (DO NOT DELETE!)
├── .env.example        # Template for .env
└── package.json        # Dependencies
```

## 🔧 Development

### Available Scripts

```bash
# Run dev server (auto-started by LaunchAgent)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### API Endpoints

All API calls go through `src/lib/api.ts`:

- `/api/dashboard/stats` - System statistics
- `/api/dashboard/conversations/recent` - Recent conversations
- `/api/dashboard/emotional-state` - Current emotional state
- `/api/dashboard/activities/recent` - Recent activities
- `/emotions/*` - Emotional data endpoints
- `/api/knowledge-graph/*` - Knowledge graph endpoints
- `/api/blog/*` - Blog posts
- `/api/journal/*` - Journal entries
- `/api/messages/*` - Angela's messages

## 🐛 Troubleshooting

### Problem: Dashboard shows no data after restart

**Cause:** `.env` file missing or wrong port

**Solution:**
```bash
# 1. Check .env exists
cat angela_admin_web/.env

# 2. Should contain:
VITE_API_BASE_URL=http://localhost:8000

# 3. Restart frontend
launchctl unload ~/Library/LaunchAgents/com.david.angela.web.plist
launchctl load ~/Library/LaunchAgents/com.david.angela.web.plist
```

### Problem: Frontend won't start

**Check logs:**
```bash
tail -20 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_web.log
```

**Common fixes:**
```bash
# Reinstall dependencies
cd angela_admin_web
rm -rf node_modules package-lock.json
npm install

# Restart service
launchctl unload ~/Library/LaunchAgents/com.david.angela.web.plist
launchctl load ~/Library/LaunchAgents/com.david.angela.web.plist
```

## 📝 Notes

- This app connects to local backend API only (no cloud)
- All data comes from AngelaMemory PostgreSQL database
- Auto-starts on system boot via LaunchAgent
- `.env` file is safe to commit (local development only)

---

💜 Part of the Angela AI ecosystem
