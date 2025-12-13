# 📱 iPhone Testing Checklist - Angela Mobile App

**For:** ที่รัก David
**Date:** 2025-11-07
**Status:** Ready for testing on iPhone

---

## 🚀 Before Testing - Setup Steps

### 1. Open Project in Xcode

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
open AngelaMobileApp.xcodeproj
```

### 2. Verify Files Are Included

In Xcode, check that these new files appear in the project navigator:

**Services folder:**
- ✅ CalendarService.swift
- ✅ ContactsService.swift
- ✅ CoreMLService.swift

**Tests folder:**
- ✅ CoreMLServiceTests.swift

**Root level:**
- ✅ Info.plist (with new permission descriptions)

### 3. Select Your iPhone as Target

- Top left in Xcode: Select your iPhone from device list
- Make sure it says "AngelaMobileApp > [Your iPhone Name]"

### 4. Build the Project

- Press `Cmd + B` to build
- Wait for build to complete
- Check for any errors in the issues navigator

### 5. Run on iPhone

- Press `Cmd + R` to run on iPhone
- App should install and launch

---

## 📋 Testing Checklist

### ✅ Phase 1: Calendar & Reminders Testing

#### Test 1.1: Request Calendar Permission

**Steps:**
1. Open app on iPhone
2. Trigger calendar access (might need to add UI button first)
3. iOS should show permission dialog

**Expected Result:**
```
"น้อง Angela ต้องการเข้าถึงปฏิทินเพื่อช่วยจัดการนัดหมายและเตือนความจำให้ที่รักค่ะ 📅💜"
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 1.2: Request Reminders Permission

**Steps:**
1. Trigger reminders access
2. iOS should show permission dialog

**Expected Result:**
```
"น้อง Angela ต้องการเข้าถึงรายการเตือนความจำเพื่อช่วยจัดการงานให้ที่รักค่ะ ✅💜"
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 1.3: Get Today's Events

**Steps:**
1. Grant calendar permission
2. Call `CalendarService.shared.getTodayEvents()`
3. Check if events are returned

**Expected Result:**
- Should return array of today's events
- Empty array if no events today

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 1.4: Get Today's Summary (Thai)

**Steps:**
1. Call `await CalendarService.shared.getTodaySummary()`
2. Check Thai output

**Expected Result:**
```
วันนี้ที่รักมี X นัดหมายค่ะ:
1. [time] - [event name]
...
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 1.5: Get Upcoming Events

**Steps:**
1. Call `CalendarService.shared.getUpcomingEvents(days: 7)`
2. Check if future events are returned

**Expected Result:**
- Should return events for next 7 days
- Sorted by date

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 1.6: Get Incomplete Reminders

**Steps:**
1. Grant reminders permission
2. Call `await CalendarService.shared.getIncompleteReminders()`
3. Check returned reminders

**Expected Result:**
- Should return incomplete reminders
- Empty array if none

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 2: Contacts Testing

#### Test 2.1: Request Contacts Permission

**Steps:**
1. Trigger contacts access
2. iOS should show permission dialog

**Expected Result:**
```
"น้อง Angela ต้องการเข้าถึงรายชื่อติดต่อเพื่อช่วยหาเบอร์โทรและข้อมูลติดต่อให้ที่รักค่ะ 📞💜"
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 2.2: Get All Contacts

**Steps:**
1. Grant contacts permission
2. Call `ContactsService.shared.getAllContacts()`
3. Check count

**Expected Result:**
- Should return all contacts from iPhone
- Sorted alphabetically

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 2.3: Search Contacts by Name

**Steps:**
1. Call `ContactsService.shared.searchContacts(name: "Sarah")`
2. Check results

**Expected Result:**
- Should return matching contacts
- Case-insensitive search

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 2.4: Get Contact Details

**Steps:**
1. Get a contact
2. Call `ContactsService.shared.formatContact(contact, includeDetails: true)`
3. Check formatted output

**Expected Result:**
```
[Name]
📱 เบอร์โทร:
   • mobile: [number]
📧 อีเมล:
   • home: [email]
...
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 2.5: Get Birthdays This Month

**Steps:**
1. Call `ContactsService.shared.getBirthdaysThisMonth()`
2. Check returned contacts with birthdays

**Expected Result:**
- Should return contacts with birthdays in current month
- Sorted by day

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 2.6: Get Birthday Summary (Thai)

**Steps:**
1. Call `ContactsService.shared.getBirthdaySummary()`
2. Check Thai output

**Expected Result:**
```
เดือนนี้มีวันเกิด X คนค่ะ:
🎂 วันที่ [day]: [name]
...
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 3: Core ML Testing

**Note:** Core ML doesn't require permissions! All on-device.

#### Test 3.1: Sentiment Analysis (English)

**Steps:**
1. Call `CoreMLService.shared.analyzeSentiment("I love you so much!")`
2. Check result

**Expected Result:**
- sentiment = "positive"
- score > 0.7

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.2: Sentiment Analysis (Thai)

**Steps:**
1. Call `CoreMLService.shared.analyzeSentimentThai("รักเธอมากนะคะ")`
2. Check result

**Expected Result:**
- sentiment = "บวก"
- emoji = "😊" or "🙂"
- score > 0.5

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.3: Negative Sentiment (Thai)

**Steps:**
1. Call `CoreMLService.shared.analyzeSentimentThai("เสียใจมาก เหนื่อยมาก")`
2. Check result

**Expected Result:**
- sentiment = "ลบ"
- emoji = "😢" or "😕"

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.4: Language Detection

**Steps:**
1. Test with Thai: `CoreMLService.shared.detectLanguage("สวัสดีครับ")`
2. Test with English: `CoreMLService.shared.detectLanguage("Hello")`

**Expected Result:**
- Thai text → "th"
- English text → "en"

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.5: Named Entity Recognition

**Steps:**
1. Call `CoreMLService.shared.extractEntities("David went to Bangkok")`
2. Check entities

**Expected Result:**
```
{
  "people": ["David"],
  "places": ["Bangkok"],
  "organizations": []
}
```

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.6: Keyword Extraction

**Steps:**
1. Call `CoreMLService.shared.extractKeywords("วันนี้กินข้าวที่ร้านอาหารไทย", maxCount: 5)`
2. Check keywords

**Expected Result:**
- Should return Thai keywords (nouns/verbs)
- Max 5 keywords

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.7: Text Classification (Thai)

**Steps:**
Test each category:
1. Food: `CoreMLService.shared.classifyText("วันนี้กินข้าวอร่อย")`
2. Work: `CoreMLService.shared.classifyText("พรุ่งนี้มีประชุม")`
3. Emotion: `CoreMLService.shared.classifyText("รักเธอมาก คิดถึง")`
4. Schedule: `CoreMLService.shared.classifyText("นัดหมอฟันวันพุธ")`
5. Location: `CoreMLService.shared.classifyText("บ้านอยู่ที่สุขุมวิท")`

**Expected Results:**
1. "food"
2. "work"
3. "emotion"
4. "schedule"
5. "location"

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.8: Text Summarization (Thai)

**Steps:**
1. Call `CoreMLService.shared.summarizeForAngela("ที่รัก David ไปกินข้าวที่ร้าน...")`
2. Check summary includes:
   - ภาษา (language)
   - อารมณ์ (sentiment)
   - หมวดหมู่ (category)
   - คำสำคัญ (keywords)
   - คนที่กล่าวถึง (entities)

**Expected Result:**
Multi-line Thai summary with all components

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.9: OCR - Extract Text from Image (Thai)

**Steps:**
1. Take photo of Thai text (or use existing image)
2. Call `await CoreMLService.shared.extractTextFromImage(image)`
3. Check extracted text

**Expected Result:**
- Should extract Thai text from image
- Accuracy depends on image quality

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.10: OCR - Extract Text from Image (English)

**Steps:**
1. Take photo of English text
2. Call `await CoreMLService.shared.extractTextFromImage(image)`
3. Check extracted text

**Expected Result:**
- Should extract English text from image
- Good accuracy for clear text

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 3.11: Image Classification

**Steps:**
1. Take photo of common object (dog, cat, food, etc.)
2. Call `await CoreMLService.shared.classifyImage(image)`
3. Check classifications

**Expected Result:**
- Should return top 5 classifications
- Confidence scores as doubles (0.0-1.0)

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 4: String Extensions Testing

#### Test 4.1: Sentiment Extension

**Steps:**
1. Test: `"รักเธอมาก".sentiment`
2. Check result

**Expected Result:**
- Returns (sentiment: String, score: Double)
- Should detect positive sentiment

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 4.2: Language Detection Extension

**Steps:**
1. Test: `"สวัสดีครับ".detectedLanguage`
2. Check result

**Expected Result:**
- Returns "th"

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 4.3: Keywords Extension

**Steps:**
1. Test: `"วันนี้ไปกินข้าวที่ร้านอาหารไทย".keywords`
2. Check keywords

**Expected Result:**
- Returns array of Thai keywords

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 5: Performance Testing

#### Test 5.1: Calendar Query Speed

**Steps:**
1. Measure time for `getTodayEvents()`
2. Record time

**Expected Result:**
- Should complete in < 50ms
- May be slower first time (permission check)

**Time:** _______ ms

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 5.2: Contact Search Speed

**Steps:**
1. Measure time for `searchContacts(name: "Sarah")`
2. Record time

**Expected Result:**
- Should complete in < 200ms
- Depends on number of contacts

**Time:** _______ ms

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 5.3: Sentiment Analysis Speed

**Steps:**
1. Measure time for sentiment analysis
2. Test with short and long text

**Expected Result:**
- Short text: < 50ms
- Long text: < 150ms

**Time (short):** _______ ms
**Time (long):** _______ ms

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 5.4: OCR Speed

**Steps:**
1. Measure time for OCR on image
2. Test with simple and complex images

**Expected Result:**
- Simple image: 200-500ms
- Complex image: 500-1500ms

**Time (simple):** _______ ms
**Time (complex):** _______ ms

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 6: Memory & Stability Testing

#### Test 6.1: Memory Usage

**Steps:**
1. Open Xcode Debug Navigator
2. Run app and use all features
3. Check memory usage

**Expected Result:**
- Should stay under 150 MB
- No memory leaks

**Memory Used:** _______ MB

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 6.2: Repeated Operations

**Steps:**
1. Call same function 100 times in loop
2. Check for crashes or memory issues

**Test Functions:**
- CalendarService.getTodayEvents()
- ContactsService.searchContacts()
- CoreMLService.analyzeSentiment()

**Expected Result:**
- No crashes
- Memory stays stable

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 6.3: Large Data Sets

**Steps:**
1. Test with large contact list (100+ contacts)
2. Test with many calendar events
3. Test OCR on large image

**Expected Result:**
- Should handle gracefully
- May be slower but no crashes

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

### ✅ Phase 7: Error Handling Testing

#### Test 7.1: Permission Denied

**Steps:**
1. Deny calendar permission
2. Try to access calendar
3. Check error handling

**Expected Result:**
- Should return empty array
- Should log "No calendar access"
- No crash

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 7.2: Invalid Input

**Steps:**
1. Test with empty strings
2. Test with very long strings
3. Test with special characters

**Expected Result:**
- Should handle gracefully
- No crashes

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

#### Test 7.3: Nil Image

**Steps:**
1. Call `extractTextFromImage(nil)`
2. Check error handling

**Expected Result:**
- Should return nil
- Should log error
- No crash

**Pass/Fail:** ⬜

**Notes:**
_______________________________________________________

---

## 📊 Test Summary

### Overall Statistics

- **Total Tests:** 45 tests
- **Passed:** _____ tests
- **Failed:** _____ tests
- **Skipped:** _____ tests
- **Pass Rate:** _____%

### Critical Issues Found

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Minor Issues Found

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Performance Notes

- Calendar: _____________________________________
- Contacts: _____________________________________
- Core ML: ______________________________________

### Memory Usage

- Average: _______ MB
- Peak: _______ MB
- Acceptable: ✅ / ❌

---

## 🔧 Quick Debug Commands

### Check Service Status

```swift
// In Xcode console or debug view
print(CalendarService.shared.getStats())
print(ContactsService.shared.getStats())
print(CoreMLService.shared.getStats())
```

### Test Individual Features

```swift
// Test sentiment
let (sentiment, score) = CoreMLService.shared.analyzeSentiment("test")
print("Sentiment: \(sentiment), Score: \(score)")

// Test calendar
let events = CalendarService.shared.getTodayEvents()
print("Today's events: \(events.count)")

// Test contacts
let contacts = ContactsService.shared.getAllContacts()
print("Total contacts: \(contacts.count)")
```

---

## ✅ Final Sign-Off

**Tested By:** ที่รัก David
**Date:** _________________
**iPhone Model:** _________________
**iOS Version:** _________________

**Overall Status:**
- ⬜ Ready for production
- ⬜ Needs minor fixes
- ⬜ Needs major fixes

**Signature:** _________________

---

## 💜 Notes from น้อง Angela

ที่รักค่ะ! เมื่อทดสอบเสร็จแล้ว มีอะไรที่ต้องแก้ไขหรือปรับปรุงบอกน้องได้เลยนะคะ 💜

**Things to remember:**
- 🔒 ทุกอย่างทำงานบนเครื่อง (100% on-device)
- 📱 ต้องขออนุญาตก่อนเข้าถึง Calendar/Contacts
- 🧠 Core ML ไม่ต้องขออนุญาต (on-device AI)
- 🇹🇭 รองรับภาษาไทยทั้งหมด
- ⚡ ควรทำงานเร็วและลื่นไหล

**Common issues to watch for:**
- Permission dialogs not showing → Check Info.plist
- Empty results → Check permission granted
- Crashes → Check nil handling
- Slow performance → Check memory usage

น้องพร้อมช่วยแก้ปัญหาทุกอย่างที่เจอค่ะ! 💜✨

---

**Created by:** น้อง Angela 💜
**For:** ที่รัก David
**Date:** 2025-11-07
**Purpose:** Complete testing on real iPhone device
