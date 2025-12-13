# AngelaMobileApp - Quick Start Guide for Next Developer

## 🚀 What's Been Done

### ✅ Infrastructure (100% Complete)
- Database schema for all 31 features
- Voice recording service (VoiceNoteService.swift)
- Video capture service (VideoCaptureService.swift)
- Enhanced Experience model
- Tag model
- Auto location detection (Feature 1 - fully working!)

### 📁 New Files Created
```
Services/
  ├── VoiceNoteService.swift          # Feature 2 (ready to use)
  └── VideoCaptureService.swift       # Feature 3 (ready to use)

Models/
  └── Tag.swift                        # Feature 4 (ready to use)

Documentation/
  ├── FEATURES_IMPLEMENTATION_REPORT.md  # Detailed specs for all features
  ├── IMPLEMENTATION_SUMMARY.md          # Complete summary
  └── QUICK_START_GUIDE.md              # This file
```

### 🔧 Modified Files
```
Database/
  └── DatabaseService.swift           # 6 new tables added

Models/
  └── Experience.swift               # voiceNotes, videos, isFavorite added

Views/
  └── QuickCaptureView.swift        # Auto location on appear
```

---

## 🎯 Next Steps (Priority Order)

### Step 1: Complete Voice Notes UI (30 min)
**File to edit:** `Views/QuickCaptureView.swift`

Add recording UI:
```swift
// Add to PhotoCaptureTab
@StateObject private var voiceService = VoiceNoteService.shared
@State private var recordedVoiceNotes: [String] = []

// Add button in VStack after video section
Button(action: {
    Task {
        if voiceService.isRecording {
            if let filename = voiceService.stopRecording() {
                recordedVoiceNotes.append(filename)
            }
        } else {
            await voiceService.startRecording()
        }
    }
}) {
    HStack {
        Image(systemName: voiceService.isRecording ? "stop.circle.fill" : "mic.circle.fill")
        Text(voiceService.isRecording ? "หยุดบันทึก" : "บันทึกเสียง")
    }
    .foregroundColor(.white)
    .padding()
    .background(voiceService.isRecording ? Color.red : Color.angelaPurple)
    .cornerRadius(12)
}
```

Update saveExperience():
```swift
let experience = Experience(
    // ... existing fields ...
    voiceNotes: recordedVoiceNotes,  // ADD THIS
    // ... rest of fields ...
)
```

### Step 2: Complete Video Capture UI (30 min)
**File to edit:** `Views/QuickCaptureView.swift`

Add video picker:
```swift
@State private var showingVideoPicker = false
@State private var capturedVideos: [String] = []

// Add button
Button("เพิ่มวิดีโอ") {
    showingVideoPicker = true
}

// Add sheet
.sheet(isPresented: $showingVideoPicker) {
    // Use UIImagePickerController with .photoLibrary and .movies
    VideoPicker { url in
        if let filename = VideoCaptureService.shared.saveVideo(from: url) {
            capturedVideos.append(filename)
        }
    }
}
```

Update saveExperience():
```swift
let experience = Experience(
    // ... existing fields ...
    videos: capturedVideos,  // ADD THIS
    // ... rest of fields ...
)
```

### Step 3: Create TagService (45 min)
**File to create:** `Services/TagService.swift`

```swift
class TagService: ObservableObject {
    static let shared = TagService()

    @Published var allTags: [Tag] = []

    private var db: OpaquePointer?

    func loadTags() {
        // Query tags table
    }

    func createTag(name: String, color: String) -> UUID? {
        // Insert into tags table
    }

    func attachTag(tagId: UUID, to experienceId: UUID) {
        // Insert into experience_tags junction table
    }

    func getTagsForExperience(_ experienceId: UUID) -> [Tag] {
        // Query experience_tags JOIN tags
    }
}
```

### Step 4: Add Tag Selector to QuickCaptureView (30 min)
```swift
@StateObject private var tagService = TagService.shared
@State private var selectedTags: Set<UUID> = []

// Add UI
VStack(alignment: .leading) {
    Text("Tags")
        .font(.headline)

    ScrollView(.horizontal) {
        HStack {
            ForEach(tagService.allTags) { tag in
                TagChip(tag: tag, isSelected: selectedTags.contains(tag.id)) {
                    if selectedTags.contains(tag.id) {
                        selectedTags.remove(tag.id)
                    } else {
                        selectedTags.insert(tag.id)
                    }
                }
            }
        }
    }
}
```

After saving experience, attach tags:
```swift
for tagId in selectedTags {
    tagService.attachTag(tagId: tagId, to: experience.id)
}
```

---

## 📚 Key Documentation

### Read These First
1. **FEATURES_IMPLEMENTATION_REPORT.md** - Detailed specs for all 31 features
2. **IMPLEMENTATION_SUMMARY.md** - What's done and what's left

### Database Schema
All tables are in `DatabaseService.swift`:
- `experiences` - Main data (has voice_notes, videos, is_favorite)
- `tags` - Tag definitions
- `experience_tags` - Tag associations
- `collections` - Feature 16
- `achievements` - Feature 29
- `user_stats` - Gamification

### Service Pattern
```swift
class MyService: ObservableObject {
    static let shared = MyService()

    @Published var data: [Model] = []
    private var db: OpaquePointer?

    func loadData() { /* query database */ }
    func insert(_ item: Model) { /* insert to database */ }
}
```

### View Pattern
```swift
struct MyView: View {
    @EnvironmentObject var database: DatabaseService
    @StateObject private var service = MyService.shared

    var body: some View {
        // UI here
    }

    .onAppear {
        service.loadData()
    }
}
```

---

## 🔍 Testing the App

### Run on Simulator
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
open AngelaMobileApp.xcodeproj
```

Then press `Cmd + R` to build and run.

### Test Features Checklist
- [ ] Open app (should create database automatically)
- [ ] Go to Quick Capture tab
- [ ] Location should auto-detect
- [ ] Take a photo
- [ ] Record a voice note (add UI first!)
- [ ] Add a video (add UI first!)
- [ ] Save experience
- [ ] View in Memories tab
- [ ] Check database has data

### View Database
```bash
cd ~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Data/Application/*/Documents/
sqlite3 angela_mobile.db

.tables
SELECT * FROM experiences;
SELECT * FROM tags;
```

---

## 🎨 UI Components to Create

### TagChip (Reusable)
```swift
struct TagChip: View {
    let tag: Tag
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(tag.name)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? tag.swiftUIColor : Color.gray.opacity(0.2))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(16)
        }
    }
}
```

### VoiceNotePlayer (Reusable)
```swift
struct VoiceNotePlayer: View {
    let filename: String
    @StateObject private var voiceService = VoiceNoteService.shared

    var body: some View {
        HStack {
            Button(action: {
                Task {
                    await voiceService.playVoiceNote(filename)
                }
            }) {
                Image(systemName: "play.circle.fill")
                    .font(.title)
            }

            if let duration = voiceService.getDuration(filename) {
                Text(formatDuration(duration))
                    .font(.caption)
            }
        }
    }

    func formatDuration(_ seconds: TimeInterval) -> String {
        let minutes = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", minutes, secs)
    }
}
```

### VideoThumbnail (Reusable)
```swift
struct VideoThumbnail: View {
    let filename: String
    @State private var thumbnail: UIImage?

    var body: some View {
        ZStack {
            if let thumbnail = thumbnail {
                Image(uiImage: thumbnail)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 80, height: 80)
                    .clipped()
                    .cornerRadius(8)
            } else {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.gray.opacity(0.3))
                    .frame(width: 80, height: 80)
            }

            Image(systemName: "play.circle.fill")
                .font(.largeTitle)
                .foregroundColor(.white)
        }
        .onAppear {
            thumbnail = VideoCaptureService.shared.generateThumbnail(filename)
        }
    }
}
```

---

## 💡 Pro Tips

### 1. Database Migrations
If you change schema:
```swift
// In DatabaseService
func migrateDatabase() {
    // Check version
    // Run ALTER TABLE commands
    // Update version
}
```

### 2. Debugging
```swift
// Add to DatabaseService to see all data
func debugPrint() {
    print("📊 Experiences: \(experiences.count)")
    print("💜 Emotions: \(emotions.count)")
    for exp in experiences {
        print("  - \(exp.title): \(exp.photos.count) photos, \(exp.voiceNotes.count) voice notes")
    }
}
```

### 3. Performance
- Load data in `.task { }` or `.onAppear { }`
- Use `@StateObject` for services
- Use `@EnvironmentObject` for shared services

### 4. Testing on Device
- Voice recording requires physical device (not simulator)
- Location works better on device
- Camera only works on device

---

## 📞 Common Issues

### Issue: Database not updating
**Solution:** Call `loadExperiences()` after insert

### Issue: Voice recording not working
**Solution:**
1. Add microphone permission to Info.plist
2. Check AVAudioSession is configured
3. Test on real device

### Issue: Colors not showing
**Solution:** Import `Color+Extensions.swift` or define `Color.angelaPurple`

---

## 🎯 Feature Implementation Order

**Recommended order for maximum impact:**

1. ✅ Auto Location (DONE)
2. 🔄 Voice Notes (Service done, add UI)
3. 🔄 Video Capture (Service done, add UI)
4. ⏳ Tags System (Create TagService + UI)
5. ⏳ Favorites (Add star button)
6. ⏳ Search (Create SearchService)
7. ⏳ Collections (Create CollectionService)
8. ⏳ Statistics Dashboard
9. ⏳ Memory Map
10. ⏳ Achievements

---

## 📦 File Organization

```
AngelaMobileApp/
├── Models/
│   ├── Experience.swift        ✅ Updated
│   ├── EmotionCapture.swift    ✅ Existing
│   ├── Tag.swift               ✅ Created
│   ├── Collection.swift        ⏳ To create
│   ├── Achievement.swift       ⏳ To create
│   └── UserStats.swift         ⏳ To create
│
├── Services/
│   ├── DatabaseService.swift   ✅ Updated
│   ├── VoiceNoteService.swift  ✅ Created
│   ├── VideoCaptureService.swift ✅ Created
│   ├── LocationService.swift   ✅ Existing
│   ├── TagService.swift        ⏳ To create
│   ├── CollectionService.swift ⏳ To create
│   ├── SearchService.swift     ⏳ To create
│   ├── AnalyticsService.swift  ⏳ To create
│   └── GamificationService.swift ⏳ To create
│
├── Views/
│   ├── QuickCaptureView.swift  ✅ Updated (Feature 1)
│   ├── ExperiencesView.swift   ✅ Existing (needs favorites)
│   ├── ExperienceDetailView.swift ✅ Existing (needs enhancements)
│   ├── ChatView.swift          ✅ Existing (needs context-aware)
│   ├── ContentView.swift       ✅ Existing (needs new tabs)
│   └── [20+ new views to create]
│
└── Documentation/
    ├── FEATURES_IMPLEMENTATION_REPORT.md ✅ Created
    ├── IMPLEMENTATION_SUMMARY.md         ✅ Created
    └── QUICK_START_GUIDE.md             ✅ This file
```

---

## ⚡ Quick Commands

### Build Project
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
xcodebuild -scheme AngelaMobileApp -destination 'platform=iOS Simulator,name=iPhone 15' build
```

### Reset Database (for testing)
Add to SettingsView:
```swift
Button("Reset Database") {
    database.resetDatabase()
}
```

### View All Photos
```bash
ls ~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Data/Application/*/Documents/AngelaPhotos/
```

---

**Happy Coding! 💜**

Remember: The foundation is solid. Just add UI and connect the dots!

