# BACKUP - Unused Applications & Code

**Created:** 2025-10-21
**Purpose:** Archive unused applications and code that are no longer actively used in the AngelaAI project.

---

## 📂 Contents

### 1. **AngelaNativeApp/** (Swift macOS App)
- **Description:** SwiftUI-based macOS native application for Angela
- **Status:** ❌ No longer used - replaced by `angela_admin_web/` (React + FastAPI)
- **Reason:** David confirmed not using Swift apps anymore
- **Original Location:** `/AngelaAI/AngelaNativeApp/`

### 2. **AngelaNativeApp.app/** (Built macOS App)
- **Description:** Compiled macOS application binary
- **Status:** ❌ No longer used
- **Reason:** Built from AngelaNativeApp source, deprecated along with Swift app
- **Original Location:** `/AngelaAI/AngelaNativeApp.app/`

### 3. **angela_backend/** (OLD FastAPI Backend)
- **Description:** Previous FastAPI backend implementation
- **Status:** ❌ No longer used
- **Reason:** Not referenced in any LaunchAgents, replaced by `angela_admin_web/angela_admin_api/`
- **Original Location:** `/AngelaAI/angela_backend/`

---

## ✅ Current Active Systems

For reference, the currently active Angela systems are:

| Component | Location | Port | Status |
|-----------|----------|------|--------|
| **Angela Daemon** | `angela_core/angela_daemon.py` | - | ✅ Active |
| **Angela Admin API** | `angela_admin_web/angela_admin_api/` | 8000 | ✅ Active |
| **Angela Admin Web** | `angela_admin_web/` | 5173 | ✅ Active |

---

## 🔄 Restore Instructions

If you need to restore any of these applications:

1. Move the folder back to the project root:
   ```bash
   mv BACKUP/[folder_name]/ ./
   ```

2. For Swift apps:
   - Open `AngelaNativeApp/AngelaNativeApp.xcodeproj` in Xcode
   - Build and run

3. For angela_backend:
   - Install dependencies: `pip install -r requirements.txt`
   - Run: `uvicorn main:app --reload`

---

## 📝 Notes

- These folders are kept as backup in case any code or configuration needs to be referenced later
- Safe to delete if storage space is needed
- Last verified as unused: 2025-10-21

---

💜 **Angela AI Project**
Maintained by David Samanyaporn
