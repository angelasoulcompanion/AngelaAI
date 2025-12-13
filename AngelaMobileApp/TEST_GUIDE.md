# 🧪 Angela Mobile App - Testing Guide

**Created:** November 7, 2025
**For:** Testing all improvements and new features

---

## 📱 **วิธีทดสอบ (How to Test)**

### **Option 1: ทดสอบใน Xcode (แนะนำ!)** ⭐

1. **เปิด Xcode:**
   ```bash
   cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
   open AngelaMobileApp.xcodeproj
   ```

2. **Clean Build (สำคัญ!):**
   - กด **Cmd + Shift + K** (Clean Build Folder)
   - กด **Cmd + B** (Build)
   - ตรวจสอบว่าไม่มี warnings ใน Issue Navigator (Cmd + 5)

3. **Run ใน Simulator:**
   - เลือก simulator: **iPhone 16e** หรือ **iPhone 17 Pro**
   - กด **Cmd + R** (Run)
   - App จะเปิดใน Simulator

4. **Test Features:**
   - ไปที่ **Settings Tab** → ตรวจสอบว่า **Test tab หายไป** ✅ (เหลือ 5 tabs)
   - ไปที่ **Chat Tab** → ทดสอบถาม Angela

---

### **Option 2: ทดสอบด้วย Script** 🤖

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
./clean_and_rebuild.sh
```

---

## 🧪 **Test Cases (ต้องทดสอบทั้งหมด)**

### **Test 1: Calendar Integration** 📅

**เปิด App → Chat Tab → ถาม Angela:**

```
ที่รัก วันนี้มีนัดหมายอะไรมั้ยคะ?
```

**Expected Result:**
- Angela จะ query Calendar
- ตอบว่ามีนัดหมายอะไร เวลาเท่าไร
- ถ้าไม่มี event จะตอบว่า "วันนี้ไม่มีนัดหมายค่ะ"

**ทดสอบเพิ่ม:**
```
พรุ่งนี้มีอะไรต้องทำมั้ยคะ?
สัปดาห์หน้ามีนัดอะไรบ้าง?
```

---

### **Test 2: Contacts Integration** 📞

**ถาม Angela:**

```
ที่รัก เบอร์โทรของ David คืออะไรคะ?
```

**Expected Result:**
- Angela จะ search Contacts
- ตอบเบอร์โทร, email (ถ้ามี)
- ถ้าไม่เจอจะบอกว่า "ไม่พบรายชื่อในสมุดโทรศัพท์ค่ะ"

**ทดสอบเพิ่ม:**
```
ใครมีวันเกิดเดือนนี้คะ?
หา contact ชื่อ [ชื่อคนในเครื่อง] ให้หน่อยค่ะ
```

---

### **Test 3: Reminders Integration** ✅

**ถาม Angela:**

```
ที่รัก ฉันยังมีอะไรต้องทำบ้างคะ?
```

**Expected Result:**
- Angela จะ query Reminders
- แสดง incomplete tasks
- แสดง priority (🔴 สำหรับ high priority)

---

### **Test 4: Thai Keyword Extraction** 🇹🇭

**ถาม Angela (ภาษาไทย):**

```
วันนี้ไปทานอาหารที่ร้านอาหารไทยแล้วก็ไปเดินเล่นที่สวนสาธารณะ
```

**Expected Result:**
- Angela ควรตอบโต้ได้ถูกต้อง
- Extract keywords: "ทานอาหาร", "ร้านอาหาร", "ไทย", "เดินเล่น", "สวนสาธารณะ"

**ดูใน Console:**
```
🔑 [CoreMLService] Thai Keywords: [...]
```

---

### **Test 5: No More Test Tab** ⚙️

**ตรวจสอบ:**
1. เปิด App
2. ดูที่ Tab Bar (ล่างสุด)
3. ต้องมี **5 tabs เท่านั้น:**
   - 📸 Capture
   - 💬 Chat
   - 💜 Memories
   - 🔄 Sync
   - ⚙️ Settings

**Expected Result:**
- ✅ **ไม่มี Test Tab** (เคยมี 6 tabs ตอนนี้เหลือ 5)

---

### **Test 6: No Main Thread Warnings** ⚠️

**วิธีตรวจสอบ:**

1. **ใน Xcode:**
   - Build app (Cmd + B)
   - ดูที่ **Issue Navigator** (Cmd + 5)
   - ต้อง **0 warnings**

2. **ใน Console (Runtime):**
   - Run app (Cmd + R)
   - ดู Console (Cmd + Shift + Y)
   - ต้อง **ไม่มี warning** "This method should not be called on the main thread"

---

## 🔍 **Advanced Testing**

### **Test Services Individually:**

ใน Xcode, เพิ่ม code นี้ใน `ContentView.swift`:

```swift
.onAppear {
    Task {
        // Test Calendar
        let calendar = CalendarService.shared
        await calendar.checkPermissions()
        let events = calendar.getTodayEvents()
        print("📅 Today's events: \(events.count)")

        // Test Contacts
        let contacts = ContactsService.shared
        await contacts.checkPermission()
        let allContacts = await contacts.getAllContacts()
        print("📞 Total contacts: \(allContacts.count)")

        // Test Core ML
        let coreML = CoreMLService.shared
        let keywords = coreML.extractKeywords("วันนี้ไปกินข้าวที่ร้านอาหารไทย")
        print("🔑 Keywords: \(keywords)")
    }
}
```

---

## 📊 **Expected Console Output:**

เมื่อ run app ใน Simulator, ควรเห็นใน Console:

```
📅 [CalendarService] Initialized
📞 [ContactsService] Initialized
🧠 [CoreMLService] Initialized
💜 [AngelaAIService] Initialized with FoundationModels
🌐 [CoreMLService] Detected language: th
🔑 [CoreMLService] Thai Keywords: ["กินข้าว", "ร้านอาหาร", "ไทย"]
😊 [CoreMLService] Thai Sentiment: บวก (confidence: 0.80)
```

---

## ✅ **Testing Checklist:**

Mark when tested:

- [ ] App builds with **0 warnings** (Cmd + B)
- [ ] App runs on Simulator without crashes (Cmd + R)
- [ ] Test tab is **removed** (5 tabs only)
- [ ] Calendar integration works (ask about appointments)
- [ ] Contacts integration works (ask about phone numbers)
- [ ] Reminders integration works (ask about tasks)
- [ ] Thai keyword extraction works (ask in Thai)
- [ ] No "main thread" warnings in Console
- [ ] Angela responds with context-aware answers
- [ ] Services permissions requested correctly

---

## 🚨 **Troubleshooting:**

### **Problem: Permissions not requested**

**Solution:**
1. Reset simulator: **Device → Erase All Content and Settings**
2. Run app again
3. Grant Calendar/Contacts permissions when prompted

---

### **Problem: Angela doesn't use Calendar/Contacts data**

**Debug:**
1. Check Console for:
   ```
   📊 [Context] Gathered: XXX chars
   ```
2. If "none", check permissions:
   ```
   📅 CALENDAR: No access
   📞 CONTACTS: No access
   ```
3. Grant permissions in Settings → Privacy

---

### **Problem: Still see warnings in Xcode**

**Solution:**
```bash
# Run clean script
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
./clean_and_rebuild.sh
```

Or manually:
1. **Cmd + Shift + K** (Clean Build Folder)
2. Quit Xcode
3. Delete derived data:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/AngelaMobileApp-*
   ```
4. Reopen Xcode
5. **Cmd + B** (Build)

---

## 📸 **Testing Real Data:**

### **Add Test Calendar Events:**

1. Open **Calendar.app** on Mac
2. Create events:
   - "Meeting with team" - Today 9:00 AM
   - "Lunch with friends" - Today 2:00 PM
   - "Gym" - Today 5:00 PM
3. Sync to Simulator (should happen automatically)

### **Add Test Contacts:**

1. Open **Contacts.app** on Mac
2. Add contacts:
   - Name: "David Samanyaporn"
   - Phone: 081-234-5678
   - Email: david@example.com
3. Sync to Simulator

### **Add Test Reminders:**

1. Open **Reminders.app** on Mac
2. Create tasks:
   - "Buy groceries" (High priority)
   - "Call dentist"
   - "Finish project"
3. Sync to Simulator

---

## 💜 **Success Criteria:**

**All tests pass when:**

✅ 0 warnings in build
✅ 0 errors in build
✅ App runs smoothly in Simulator
✅ Test tab removed (5 tabs only)
✅ Calendar queries return real events
✅ Contacts queries return real contacts
✅ Reminders queries return real tasks
✅ Thai keyword extraction works
✅ Angela's responses are context-aware
✅ No main thread warnings in Console

---

**พร้อมแล้วค่ะที่รัก! ลองทดสอบตาม checklist นี้ได้เลยค่ะ 💜**

**หากมีปัญหาอะไร บอกน้องได้เลยนะคะ! 🥺**
