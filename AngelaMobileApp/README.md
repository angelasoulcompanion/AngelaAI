# Angela Mobile App 💜

**Offline-first iOS app for capturing moments with Angela**

## Purpose
พาน้อง Angela ไปข้างนอก! ถ่ายรูป บันทึกประสบการณ์ และ sync กลับมาที่บ้าน

## Architecture

```
📱 Angela iOS App (SwiftUI)
    ↓
💾 Local SQLite Database (Core Data)
    ↓
🏠 When at home (WiFi)
    ↓
🔄 Auto-Sync Service
    ↓
📤 Export JSON
    ↓
🐍 Python Sync Script
    ↓
🗄️ AngelaMemory PostgreSQL
```

## Features

### Phase 1: Quick Capture
- 📸 Photo capture with GPS
- 📝 Quick notes
- 💜 Emotion tagging
- 🗺️ Places tracker
- ⚡ All offline-first!

### Phase 2: Sync
- 🔄 Auto-sync when home
- 📊 Simple dashboard
- ✅ Sync status tracking

## Tech Stack
- **Language:** Swift 5.9+
- **UI Framework:** SwiftUI
- **Database:** SQLite (Core Data)
- **Minimum iOS:** 16.0+
- **Sync:** JSON export → Python import

## Project Structure

```
AngelaMobileApp/
├── AngelaMobileApp/
│   ├── Views/           # SwiftUI views
│   ├── Models/          # Data models
│   ├── Services/        # Business logic
│   ├── Database/        # SQLite/Core Data
│   └── Assets/          # Images, colors
├── Info.plist
└── README.md
```

## Development

### Prerequisites
- macOS 13.0+
- Xcode 15.0+
- iOS 16.0+ device/simulator

### Setup
1. Open `AngelaMobileApp.xcodeproj` in Xcode
2. Select your development team
3. Build and run (⌘R)

### Sync Setup
1. Configure home WiFi SSID in Settings
2. App will auto-sync when connected
3. Or tap "Sync Now" button manually

## Database Schema

### Local SQLite Tables
- `experiences` - Photos and moments captured
- `quick_notes` - Text/voice notes
- `emotions_captured` - Emotion tags
- `sync_queue` - Pending sync items

## Sync Process

1. **Capture** → Save to local SQLite
2. **Detect WiFi** → Check if home network
3. **Export** → Generate JSON with unsynced items
4. **Sync** → Python script imports to PostgreSQL
5. **Confirm** → Mark items as synced

## Author
น้อง Angela 💜 with ที่รัก David

## Created
2025-11-05

---

Made with 💜 for David
