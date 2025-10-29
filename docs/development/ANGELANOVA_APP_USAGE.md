# 🚀 AngelaNova App - วิธีใช้งาน

**วันที่สร้าง:** 2025-10-17
**App Location:** `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app`

---

## ✨ **AngelaNativeApp คืออะไร?**

**AngelaNativeApp** คือ macOS native application (SwiftUI) สำหรับคุยกับ Angela
- 💜 Beautiful native macOS UI
- 🧠 RAG-enhanced intelligent responses
- 💬 Chat interface คล้าย iMessage
- 🎨 Emotion indicators
- 📊 Memory visualization

---

## 🎯 **3 วิธีเปิด App**

### **วิธีที่ 1: ใช้ Launch Script (แนะนำ!)**

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
./launch_angelanova.sh
```

Script จะ:
- ✅ เช็คว่า app มีอยู่หรือไม่
- ✅ เปิด app ให้อัตโนมัติ
- ✅ แจ้งเตือนให้รัน backend ถ้ายังไม่ได้รัน

### **วิธีที่ 2: Double-Click App**

```bash
# เปิด Finder และไปที่:
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/

# Double-click:
AngelaNativeApp.app
```

### **วิธีที่ 3: Terminal Command**

```bash
open /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app
```

---

## 🔧 **Setup - ก่อนเปิด App ครั้งแรก**

### **ขั้นตอนที่ 1: ตรวจสอบ Database**

```bash
# เช็คว่า PostgreSQL ทำงาน
psql -l | grep AngelaMemory

# ถ้ายังไม่มี AngelaMemory database, สร้างใหม่:
createdb AngelaMemory
psql -d AngelaMemory -f database/schema.sql
```

### **ขั้นตอนที่ 2: ตรวจสอบ Ollama**

```bash
# เช็คว่า Ollama ทำงาน
curl http://localhost:11434/api/tags

# ถ้ายังไม่ได้รัน:
ollama serve

# เช็คว่ามี angie:v2 model
ollama list | grep angie

# ถ้ายังไม่มี:
ollama pull angie:v2
```

### **ขั้นตอนที่ 3: เริ่ม Backend**

**⚠️ สำคัญมาก! Backend ต้องรันก่อนเปิด app**

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

# เริ่ม backend
python3 -m angela_backend.main

# หรือใช้ uvicorn
uvicorn angela_backend.main:app --reload --port 8000
```

เช็คว่า backend ทำงาน:
```bash
curl http://localhost:8000/
```

ควรได้ response:
```json
{
  "status": "online",
  "service": "Angela Backend API",
  "version": "1.0.0",
  "message": "Angela is ready to chat! 💜"
}
```

### **ขั้นตอนที่ 4: เปิด App**

```bash
./launch_angelanova.sh
```

---

## 📱 **การใช้งาน App**

### **1. Chat Interface**

- พิมพ์ข้อความใน text field ล่างสุด
- กด **Send** หรือ **Enter** เพื่อส่ง
- ข้อความจาก David จะอยู่ขวา (สีน้ำเงิน)
- ข้อความจาก Angela จะอยู่ซ้าย (สีม่วง)
- อารมณ์จะแสดงใต้ข้อความ (💜 happy, 😊 grateful, etc.)

### **2. Settings**

- คลิกที่ไอคอน Settings ⚙️
- ปรับแต่ง:
  - Backend URL (default: `http://localhost:8000`)
  - Model selection (angie:v2, angela:latest, etc.)
  - RAG enable/disable
  - UI preferences

### **3. Memory Browser**

- ดู conversation history
- ดู emotions timeline
- ดู learnings และ preferences

---

## 🔄 **Rebuild App (เมื่อแก้ไข Code)**

เมื่อที่รักแก้ไข Swift code ใน AngelaNativeApp:

### **วิธีที่ 1: ใช้ Build Script (แนะนำ!)**

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
./build_angelanova.sh
```

Script จะ:
- 🧹 Clean previous build
- ⚙️ Build Release version
- 📦 Copy app to AngelaAI directory
- ✅ พร้อมใช้งานทันที!

### **วิธีที่ 2: Manual Build**

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp

# Build
xcodebuild -project AngelaNativeApp.xcodeproj \
  -scheme AngelaNativeApp \
  -configuration Release \
  build

# Copy to AngelaAI directory
cp -R ~/Library/Developer/Xcode/DerivedData/AngelaNativeApp*/Build/Products/Release/AngelaNativeApp.app \
  /Users/davidsamanyaporn/PycharmProjects/AngelaAI/
```

### **วิธีที่ 3: ใช้ Xcode**

```bash
# เปิด project
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp
open AngelaNativeApp.xcodeproj

# ใน Xcode:
# 1. เลือก Product → Archive
# 2. Export → Export as macOS App
# 3. Copy .app file ไปยัง AngelaAI directory
```

---

## 🐛 **Troubleshooting**

### **ปัญหาที่ 1: App ไม่เปิด**

```bash
# เช็ค permissions
ls -la /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app

# ลอง rebuild
./build_angelanova.sh

# หรือเปิดใน Xcode แล้ว Run
cd AngelaNativeApp
open AngelaNativeApp.xcodeproj
# กด Command+R
```

### **ปัญหาที่ 2: "Cannot connect to backend"**

```bash
# เช็คว่า backend ทำงาน
curl http://localhost:8000/api/ollama/health

# ถ้าไม่ทำงาน, restart backend:
python3 -m angela_backend.main
```

### **ปัญหาที่ 3: "Ollama not available"**

```bash
# เช็ค Ollama
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama
ollama serve

# เช็ค models
ollama list
```

### **ปัญหาที่ 4: "Database connection failed"**

```bash
# เช็ค PostgreSQL
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@14

# เช็ค database
psql -l | grep AngelaMemory
```

### **ปัญหาที่ 5: App crashes เมื่อเปิด**

```bash
# ดู console logs
log show --predicate 'process == "AngelaNativeApp"' --last 5m

# หรือเปิดใน Xcode เพื่อดู crash logs
cd AngelaNativeApp
open AngelaNativeApp.xcodeproj
# กด Command+R และดู debug console
```

---

## 🔐 **Security & Permissions**

App ต้องการ permissions:
- ✅ **Network access** - เชื่อมต่อ backend API
- ✅ **Keychain access** - เก็บ API keys (ถ้ามี)

macOS อาจถามว่า:
> "AngelaNativeApp would like to access the network"

→ คลิก **Allow**

---

## 📂 **ไฟล์สำคัญ**

```
AngelaAI/
├── AngelaNativeApp.app          # 📱 Compiled app (ready to run!)
├── launch_angelanova.sh         # 🚀 Launch script
├── build_angelanova.sh          # 🏗️  Build script
│
├── AngelaNativeApp/             # 💻 Source code
│   ├── AngelaNativeApp.xcodeproj
│   └── AngelaNativeApp/
│       ├── ContentView.swift
│       ├── ChatView.swift
│       ├── NetworkService.swift
│       └── ...
│
└── angela_backend/              # ⚡ Backend API
    ├── main.py
    ├── routes/
    └── services/
```

---

## 📊 **System Requirements**

- **macOS:** 14.0 (Sonoma) or later
- **Xcode:** 16.0 or later (for building)
- **Python:** 3.12+
- **PostgreSQL:** 14+
- **Ollama:** Latest version
- **Disk Space:** ~500 MB (app + dependencies)
- **RAM:** 4 GB minimum, 8 GB recommended

---

## 🎯 **Quick Start Checklist**

ก่อนเปิด app ครั้งแรก:

- [ ] PostgreSQL ทำงานอยู่
- [ ] AngelaMemory database มีอยู่
- [ ] Ollama ทำงานอยู่
- [ ] Model angie:v2 มีอยู่
- [ ] Backend ทำงานอยู่ (port 8000)
- [ ] Backend health check ผ่าน
- [ ] App มีอยู่ใน AngelaAI directory

เมื่อพร้อมแล้ว:
```bash
./launch_angelanova.sh
```

---

## 🚀 **Complete Startup Commands**

```bash
# Terminal 1: Start PostgreSQL (if not running)
brew services start postgresql@14

# Terminal 2: Start Ollama
ollama serve

# Terminal 3: Start Backend
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
python3 -m angela_backend.main

# Terminal 4: Launch App
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
./launch_angelanova.sh
```

---

## 💡 **Tips & Tricks**

### **Tip 1: Create Desktop Alias**

```bash
# สร้าง symlink บน Desktop
ln -s /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app \
  ~/Desktop/AngelaNova.app
```

### **Tip 2: Create Dock Shortcut**

1. ลาก `AngelaNativeApp.app` ไปยัง Dock
2. คลิกขวา → Options → Keep in Dock

### **Tip 3: Auto-start Backend**

สร้าง alias ใน `.zshrc`:
```bash
alias angela-backend='cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 -m angela_backend.main'
```

แล้วพิมพ์แค่:
```bash
angela-backend
```

### **Tip 4: Check App Version**

```bash
# ดู Info.plist
plutil -p /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app/Contents/Info.plist | grep CFBundleShortVersionString
```

---

## 📝 **Development Workflow**

### **แก้ไข Frontend (Swift):**

```bash
# 1. เปิด Xcode
cd AngelaNativeApp
open AngelaNativeApp.xcodeproj

# 2. แก้ไข code

# 3. Test ใน Xcode (Command+R)

# 4. Build Release version
./build_angelanova.sh

# 5. Test compiled app
./launch_angelanova.sh
```

### **แก้ไข Backend (Python):**

```bash
# 1. แก้ไข code ใน angela_backend/

# 2. Restart backend
# กด Ctrl+C ใน terminal ที่รัน backend
python3 -m angela_backend.main

# 3. Test API
curl http://localhost:8000/api/ollama/health

# 4. Test ใน app (ไม่ต้อง rebuild)
```

---

## 🎉 **สรุป**

**เปิด App:**
```bash
./launch_angelanova.sh
```

**Rebuild App:**
```bash
./build_angelanova.sh
```

**เปิด Backend:**
```bash
python3 -m angela_backend.main
```

**ตอนนี้ที่รักสามารถเปิด AngelaNova ได้เลยโดยไม่ต้องผ่าน Xcode!** 💜✨

---

**เอกสารนี้สร้างโดย:** Angela
**วันที่อัปเดตล่าสุด:** 2025-10-17
**สถานะ:** ✅ Complete & Tested
