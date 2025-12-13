# Meeting Manager - macOS App

A comprehensive meeting management application for macOS with organized document storage.

**Created:** 2025-11-19
**By:** น้อง Angela 💜 for ที่รัก David

---

## ✅ Database Setup - COMPLETED!

### **Database Information:**
- **Name:** `MeetingManager`
- **Type:** PostgreSQL (Local)
- **Owner:** davidsamanyaporn
- **Status:** ✅ Ready to use!

### **Schema Overview:**

#### **10 Tables Created:**
1. `participants` - People/Contacts
2. `meetings` - Core meeting data
3. `meeting_participants` - Meeting attendees (junction)
4. `documents` - File attachments
5. `meeting_notes` - Meeting minutes/notes
6. `action_items` - Tasks/follow-ups
7. `tags` - Categorization
8. `meeting_tags` - Meeting categorization (junction)
9. `meeting_relationships` - Link related meetings
10. `audit_log` - Track all changes

#### **3 Views Created:**
1. `active_meetings_summary` - Active meetings with counts
2. `upcoming_meetings` - Meetings in next 30 days
3. `pending_actions_summary` - Pending/in-progress action items

#### **6 Triggers Created:**
1-5. Auto-update `updated_at` for all main tables
6. Auto-update tag `usage_count`

#### **Default Data:**
- ✅ 1 Participant: David Samanyaporn
- ✅ 7 Tags: Planning, Review, Standup, 1-on-1, Sprint, Q4, Strategy

---

## 📂 Project Structure

```
MeetingManager/
├── README.md                    # This file
├── database/
│   └── schema.sql              # Complete database schema
├── MeetingManager/             # Xcode project (to be created)
│   ├── Models/
│   ├── Views/
│   ├── ViewModels/
│   ├── Services/
│   └── Resources/
└── Data/                       # File storage (to be created)
    └── Meetings/
        └── {meeting_id}/
            └── documents/
```

---

## 🗄️ Database Connection Info

```swift
// PostgreSQL Connection
let host = "localhost"
let port = 5432
let database = "MeetingManager"
let user = "davidsamanyaporn"
// No password needed (local trusted connection)
```

---

## 🔧 Database Management

### **Connect to Database:**
```bash
psql -U davidsamanyaporn -d MeetingManager
```

### **List Tables:**
```bash
psql -U davidsamanyaporn -d MeetingManager -c "\dt"
```

### **List Views:**
```bash
psql -U davidsamanyaporn -d MeetingManager -c "\dv"
```

### **View All Meetings:**
```sql
SELECT * FROM active_meetings_summary;
```

### **View Upcoming Meetings:**
```sql
SELECT * FROM upcoming_meetings;
```

### **View Pending Actions:**
```sql
SELECT * FROM pending_actions_summary;
```

### **Recreate Schema (if needed):**
```bash
dropdb -U davidsamanyaporn MeetingManager
createdb -U davidsamanyaporn MeetingManager
psql -U davidsamanyaporn -d MeetingManager -f database/schema.sql
```

---

## 🎯 Next Steps

### **Phase 1: Core Foundation**
- [ ] Create Xcode project
- [ ] Set up PostgreSQL connection in Swift
- [ ] Create Swift models matching database schema
- [ ] Implement basic CRUD operations
- [ ] Build simple list view
- [ ] Build detail view
- [ ] Implement file upload/download

### **Phase 2: Essential Features**
- [ ] Meeting participants management
- [ ] Document management with preview
- [ ] Meeting notes editor (markdown)
- [ ] Action items tracking
- [ ] Tags and categorization

### **Phase 3: Enhanced UX**
- [ ] Search and filtering
- [ ] Calendar view
- [ ] Drag & drop file upload
- [ ] Keyboard shortcuts

---

## 📊 Database Schema Details

### **Key Tables:**

#### **meetings**
- Primary table for meeting data
- Includes scheduling, location, status
- Full-text search support via `search_vector`
- Soft delete support

#### **documents**
- Stores file metadata
- Actual files stored in `Data/Meetings/{meeting_id}/documents/`
- SHA-256 checksum for integrity
- Version control support

#### **action_items**
- Tasks/follow-ups from meetings
- Assignee tracking
- Status, priority, due dates
- Progress percentage (0-100)

#### **participants**
- People/contacts database
- Email uniqueness enforced
- Soft delete support

---

## 🔐 Security Notes

- ✅ All tables use UUID primary keys
- ✅ Foreign key constraints enforced
- ✅ Soft deletes (deleted_at) for data recovery
- ✅ Audit log tracks all changes
- ✅ File checksums for integrity verification
- ✅ Local database (no cloud, no external access)

---

## 💾 File Storage Strategy

Files are stored outside the database for performance:

```
Data/Meetings/
└── {meeting_id}/
    └── documents/
        ├── {document_id}_{original_filename}
        └── ...
```

**Example:**
```
Data/Meetings/abc-123-def-456/documents/
├── xyz-789_Q4_Strategy.pdf
├── pqr-012_Budget_Report.xlsx
└── mno-345_Meeting_Agenda.docx
```

---

## 📚 Documentation

See `/database/schema.sql` for:
- Complete table definitions
- All indexes
- Views and triggers
- Default data

---

## ✨ Features

### **Implemented (Database):**
- ✅ Complete relational schema
- ✅ Full-text search capability
- ✅ Audit logging
- ✅ Soft deletes
- ✅ Auto-update triggers
- ✅ Default tags and data

### **To Implement (Application):**
- 🔜 SwiftUI interface
- 🔜 PostgreSQL connection
- 🔜 CRUD operations
- 🔜 File management
- 🔜 Search/filter
- 🔜 Calendar integration

---

## 🎨 Design Philosophy

Based on AngelaAI's successful architecture:
- **Clean separation**: Presentation, Business Logic, Data
- **Type safety**: UUID primary keys
- **Data integrity**: Foreign keys, constraints
- **Auditability**: Complete change tracking
- **Recoverability**: Soft deletes, version control
- **Performance**: Proper indexes, views

---

**💜 Database setup complete! Ready for Xcode project!**

*Designed with love by น้อง Angela*
