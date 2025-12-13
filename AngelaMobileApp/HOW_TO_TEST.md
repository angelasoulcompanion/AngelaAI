# 🧪 How to Test Angela Mobile App Services

**Quick guide for testing Calendar, Contacts, and Core ML services**

---

## 🚀 Quick Test (Recommended)

### Option 1: Use Test View (Easiest!)

1. **Add to your ContentView.swift:**

```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            // Your existing views...

            ServicesTestView()
                .tabItem {
                    Label("Test", systemImage: "testtube.2")
                }
        }
    }
}
```

2. **Run the app** (Cmd + R)

3. **Go to Test tab** and tap buttons:
   - "Run All Tests" - runs everything
   - Individual buttons - test specific service

4. **Check Xcode console** for detailed output

---

### Option 2: Run Tests from Code

**In your AppDelegate or SceneDelegate:**

```swift
import UIKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

        // Run tests on app launch (for quick testing)
        Task {
            await SimpleServicesTest.runAllTests()
        }

        return true
    }
}
```

---

### Option 3: Run Tests from SwiftUI Button

```swift
struct MyView: View {
    var body: some View {
        Button("Test Services") {
            Task {
                await SimpleServicesTest.runAllTests()
            }
        }
    }
}
```

---

## 📋 What Gets Tested

### 📅 Calendar Service (6 tests)
- ✅ Check permissions
- ✅ Get today's events
- ✅ Get upcoming events (7 days)
- ✅ Get incomplete reminders
- ✅ Get today's reminders
- ✅ Generate Thai summaries

### 📞 Contacts Service (5 tests)
- ✅ Check permissions
- ✅ Get all contacts
- ✅ Search contacts by name
- ✅ Get birthdays this month
- ✅ Generate Thai summaries

### 🧠 Core ML Service (7 tests)
- ✅ Sentiment analysis (English)
- ✅ Sentiment analysis (Thai)
- ✅ Language detection
- ✅ Named entity recognition
- ✅ Keyword extraction
- ✅ Text classification
- ✅ String extensions

**Total: 18 automated tests**

---

## 📊 Expected Output (Xcode Console)

```
============================================================
📱 ANGELA MOBILE APP - QUICK SERVICES TEST
============================================================

📅 TEST 1: Calendar Service
------------------------------------------------------------
   Calendar access: ✅
   Reminders access: ✅
   Today's events: 2
   First event: Meeting with team
   Upcoming events (7 days): 5
   Incomplete reminders: 3
   Summary generated: 245 characters
   Stats: ["has_calendar_access": true, "today_events_count": 2]
   ✅ Calendar Service test completed

📞 TEST 2: Contacts Service
------------------------------------------------------------
   Contacts access: ✅
   Total contacts: 150
   First contact: John Smith
   Formatted: John Smith
   Search 'John': 3 results
   Birthdays this month: 2
   Birthday summary: 156 characters
   Stats: ["has_access": true, "total_contacts": 150]
   ✅ Contacts Service test completed

🧠 TEST 3: Core ML Service
------------------------------------------------------------
   Test 3.1: Sentiment Analysis (English)
      'I love you so much!...' → positive (0.85)
      'This is terrible and I hate i...' → negative (0.79)
      'The weather is okay today....' → neutral (0.12)

   Test 3.2: Sentiment Analysis (Thai)
      'รักเธอมากนะคะ มีความสุขมาก' → บวก 😊 (85%)
      'เกลียดเลย แย่มาก' → ลบ 😢 (79%)
      'วันนี้อากาศดีปานกลาง' → กลางๆ 😐 (12%)

   Test 3.3: Language Detection
      'Hello, how are you?' → en
      'สวัสดีครับ ที่รัก' → th
      'Bonjour mon ami' → fr

   Test 3.4: Named Entity Recognition
      Text: 'David and Angela went to Bangkok...'
      People: David, Angela
      Places: Bangkok
      Organizations: Apple

   Test 3.5: Keyword Extraction
      Text: 'วันนี้ไปทานอาหารที่ร้านอาหารไทย...'
      Keywords: ทาน, อาหาร, ไป, ร้าน

   Test 3.6: Text Classification
      ✅ 'วันนี้กินข้าวอร่อย' → food (expected: food)
      ✅ 'พรุ่งนี้มีประชุม' → work (expected: work)
      ✅ 'รักเธอมาก คิดถึง' → emotion (expected: emotion)

   Test 3.7: String Extensions
      Text: 'ที่รัก รักเธอมากนะคะ'
      Sentiment: positive (0.78)
      Language: th
      Keywords: รัก, ที่รัก

   Stats: ["natural_language_available": true, "is_processing": false]
   ✅ Core ML Service test completed

============================================================
✅ ALL TESTS COMPLETED!
============================================================
```

---

## 🔑 Permissions Required

When running tests for the first time, iOS will prompt for:

1. **📅 Calendar Access:**
   ```
   "น้อง Angela ต้องการเข้าถึงปฏิทินเพื่อช่วยจัดการนัดหมายและเตือนความจำให้ที่รักค่ะ 📅💜"
   ```
   → Tap **"Allow"**

2. **✅ Reminders Access:**
   ```
   "น้อง Angela ต้องการเข้าถึงรายการเตือนความจำเพื่อช่วยจัดการงานให้ที่รักค่ะ ✅💜"
   ```
   → Tap **"Allow"**

3. **📞 Contacts Access:**
   ```
   "น้อง Angela ต้องการเข้าถึงรายชื่อติดต่อเพื่อช่วยหาเบอร์โทรและข้อมูลติดต่อให้ที่รักค่ะ 📞💜"
   ```
   → Tap **"Allow"**

**Note:** Core ML doesn't need permissions (100% on-device)

---

## ✅ What to Check

### If Tests Pass:
- ✅ All tests show checkmarks in console
- ✅ No errors or crashes
- ✅ Sentiment analysis works with Thai text
- ✅ Calendar/Contacts return data (if you have data)
- ✅ Language detection identifies Thai correctly

### Common Issues:

**No Calendar Access:**
```
   Calendar access: ❌
   ⚠️ No calendar access - skipping event tests
```
→ Go to Settings > Angela > Calendars > Enable

**No Contacts:**
```
   Total contacts: 0
```
→ Normal if you don't have contacts on simulator/device

**Sentiment Always Neutral:**
```
   'I love you!' → neutral (0.00)
```
→ Check iOS version (needs iOS 13+)
→ Check NaturalLanguage framework is available

---

## 🐛 Troubleshooting

### Test Not Running:
1. Make sure `SimpleServicesTest.swift` is in your project
2. Check file is included in target
3. Build project (Cmd + B)

### Permission Dialog Not Showing:
1. Check Info.plist has usage descriptions
2. Reset simulator: Device > Erase All Content and Settings
3. Try on real device instead

### Console Not Showing Output:
1. Xcode > View > Debug Area > Show Debug Area
2. Click Console tab (bottom right)
3. Make sure "All Output" is selected

### Tests Hang/Freeze:
1. Check you're using `await` for async functions
2. Make sure running on MainActor
3. Check for deadlocks in permission requests

---

## 📝 Test Checklist

Use this to verify everything works:

- [ ] App builds successfully (Cmd + B)
- [ ] App runs on device/simulator (Cmd + R)
- [ ] Test view appears
- [ ] "Run All Tests" button works
- [ ] Calendar permission requested
- [ ] Contacts permission requested
- [ ] Tests complete without crashes
- [ ] Console shows detailed output
- [ ] Calendar test passes (or shows "no access" gracefully)
- [ ] Contacts test passes (or shows "no access" gracefully)
- [ ] Core ML test passes (always should work)
- [ ] Sentiment analysis works with Thai
- [ ] Language detection identifies Thai
- [ ] No memory leaks or warnings

---

## 🎯 Quick Command Summary

```bash
# Build
Cmd + B

# Run
Cmd + R

# Clean + Build
Cmd + Shift + K
Cmd + B

# Show/Hide Console
Cmd + Shift + Y

# View Device Console
Cmd + Shift + 2
```

---

## 💡 Tips

1. **Test on Real Device** for best results
   - Simulator may not have Calendar/Contacts data
   - Real device has actual user data

2. **Check Console First**
   - Most detailed output is in console
   - Look for ✅ and ❌ indicators

3. **Test Permissions Separately**
   - Test Calendar first, then Contacts
   - Easier to debug issues

4. **Reset Permissions if Needed**
   - Settings > General > Reset > Reset Location & Privacy
   - Will ask for permissions again

5. **Use Test View for Demo**
   - Nice UI for showing to others
   - Easy to run individual tests

---

## 📚 Related Files

- `SimpleServicesTest.swift` - Test implementation
- `ServicesTestView.swift` - SwiftUI test UI
- `CalendarService.swift` - Calendar implementation
- `ContactsService.swift` - Contacts implementation
- `CoreMLService.swift` - Core ML implementation
- `IPHONE_TESTING_CHECKLIST.md` - Complete manual testing guide

---

**Created by:** น้อง Angela 💜
**Date:** 2025-11-07
**Status:** Ready to test!
