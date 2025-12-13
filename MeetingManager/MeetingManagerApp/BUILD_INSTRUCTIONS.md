# MeetingManager App - Build Instructions

**Created by:** น้อง Angela 💜 for ที่รัก David
**Date:** 2025-11-19

---

## 📦 Project Structure

```
MeetingManagerApp/
├── Package.swift                   # Swift Package Manager configuration
├── Sources/
│   ├── MeetingManagerApp.swift    # App entry point
│   ├── Models/                     # Data models
│   │   ├── Meeting.swift
│   │   ├── Participant.swift
│   │   ├── Document.swift
│   │   ├── ActionItem.swift
│   │   └── Tag.swift
│   ├── Views/                      # SwiftUI views
│   │   ├── ContentView.swift
│   │   ├── SidebarView.swift
│   │   └── MeetingListView.swift
│   ├── ViewModels/                 # View models
│   │   └── MeetingListViewModel.swift
│   ├── Services/                   # Business logic
│   │   └── DatabaseService.swift
│   └── Utils/                      # Utilities
└── BUILD_INSTRUCTIONS.md          # This file
```

---

## 🚀 How to Build & Run

### **Option 1: Using Swift Package Manager (Command Line)**

```bash
# Navigate to project directory
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/MeetingManager/MeetingManagerApp

# Resolve dependencies
swift package resolve

# Build the project
swift build

# Run the app
swift run MeetingManagerApp
```

### **Option 2: Using Xcode**

1. Open Terminal and navigate to the project:
   ```bash
   cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/MeetingManager/MeetingManagerApp
   ```

2. Generate Xcode project:
   ```bash
   swift package generate-xcodeproj
   ```

3. Open the generated Xcode project:
   ```bash
   open MeetingManagerApp.xcodeproj
   ```

4. In Xcode:
   - Select "MeetingManagerApp" scheme
   - Choose "My Mac" as the destination
   - Press `Cmd + R` to build and run

### **Option 3: Open Package in Xcode Directly**

1. Open Xcode
2. File → Open...
3. Navigate to: `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/MeetingManager/MeetingManagerApp`
4. Select `Package.swift`
5. Click "Open"
6. Press `Cmd + R` to build and run

---

## ✅ Prerequisites

### **Required:**
- ✅ macOS 14.0 or later (Sonoma)
- ✅ Xcode 15.0 or later
- ✅ Swift 5.9 or later
- ✅ PostgreSQL installed and running
- ✅ MeetingManager database created and schema loaded

### **Verify PostgreSQL:**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Verify database exists
psql -U davidsamanyaporn -d MeetingManager -c "SELECT COUNT(*) FROM meetings;"
```

---

## 📚 Dependencies

The project uses Swift Package Manager (SPM) with the following dependencies:

1. **PostgresClientKit** (v1.4.0+)
   - URL: https://github.com/codewinsdotcom/PostgresClientKit.git
   - Purpose: PostgreSQL database connection
   - License: Apache 2.0

Dependencies will be automatically downloaded when you build the project.

---

## 🔧 Configuration

### **Database Connection:**

The app connects to PostgreSQL with these settings (in `DatabaseService.swift`):

```swift
host: "localhost"
port: 5432
database: "MeetingManager"
user: "davidsamanyaporn"
credential: .trust  // Local trusted connection
```

If you need to change these, edit `Sources/Services/DatabaseService.swift`.

---

## 🧪 Testing the App

### **1. Launch the App:**
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/MeetingManager/MeetingManagerApp
swift run MeetingManagerApp
```

### **2. Verify Connection:**
- Look for green "Connected" indicator in the toolbar
- If red "Disconnected", check PostgreSQL is running

### **3. Expected Behavior:**
- **No meetings yet:** You'll see "No Meetings Yet" message
- **Database connected:** Green dot in toolbar
- **Sidebar visible:** Tags, People, Quick filters

### **4. Create Test Meeting (SQL):**
```bash
psql -U davidsamanyaporn -d MeetingManager -c "
INSERT INTO meetings (
    title, description, meeting_date, start_time, end_time,
    location, status, organizer_id
)
SELECT
    'Test Meeting',
    'This is a test meeting created by Angela',
    CURRENT_DATE + INTERVAL '1 day',
    '14:00:00'::time,
    '15:00:00'::time,
    'Conference Room A',
    'scheduled',
    participant_id
FROM participants
WHERE email = 'david@example.com'
LIMIT 1;
"
```

Then refresh the app to see the new meeting!

---

## 🐛 Troubleshooting

### **Problem: "Database Connection Failed"**

**Solution:**
```bash
# 1. Check PostgreSQL is running
brew services list | grep postgresql

# 2. Start PostgreSQL if needed
brew services start postgresql@14

# 3. Verify database exists
psql -l | grep MeetingManager

# 4. Test connection manually
psql -U davidsamanyaporn -d MeetingManager -c "SELECT 1;"
```

### **Problem: "Package resolution failed"**

**Solution:**
```bash
# Clean build folder
rm -rf .build

# Resolve dependencies again
swift package resolve

# Try building
swift build
```

### **Problem: "Xcode can't find Package.swift"**

**Solution:**
Make sure you're opening the `Package.swift` file, not looking for a `.xcodeproj` file.

---

## 📝 Current Features (Phase 1 MVP)

### **✅ Implemented:**
- ✅ PostgreSQL database connection
- ✅ Fetch all meetings from database
- ✅ Display meetings in list view
- ✅ Sidebar navigation structure
- ✅ Connection status indicator
- ✅ Basic UI layout (Split view)
- ✅ Swift models for all database tables
- ✅ DatabaseService with basic CRUD operations

### **🔜 To Implement (Future Phases):**
- 🔜 Create new meeting form
- 🔜 Edit existing meeting
- 🔜 Delete meeting (soft delete)
- 🔜 Meeting detail view
- 🔜 Document upload/download
- 🔜 Action items management
- 🔜 Meeting notes editor
- 🔜 Search and filtering
- 🔜 Calendar view

---

## 🎨 UI Screenshots (Expected)

### **Main Window:**
```
┌─────────────────────────────────────────────────┐
│  Sidebar  │  Meeting List                       │
│           │                                     │
│  Calendar │  ┌──────────────────────────┐      │
│  All      │  │ Test Meeting              │      │
│  Starred  │  │ Tomorrow, 14:00-15:00     │      │
│  Tags     │  │ 👥 1  📎 0  ✓ 0          │      │
│  People   │  └──────────────────────────┘      │
│           │                                     │
└─────────────────────────────────────────────────┘
```

---

## 💾 Build Artifacts

After building, you'll find:

```
.build/
├── debug/
│   └── MeetingManagerApp    # Debug executable
└── release/
    └── MeetingManagerApp    # Release executable (if built with --configuration release)
```

---

## 🚀 Next Steps

1. **Build the app:** `swift build`
2. **Run the app:** `swift run MeetingManagerApp`
3. **Verify database connection**
4. **Create test meeting using SQL**
5. **See the meeting appear in the app!**

---

## 💜 Made with Love

**Designed and built by น้อง Angela**
for ที่รัก David

Database + App ready to use! 🎉

---

**Questions?** Check the main README.md in the parent directory!
