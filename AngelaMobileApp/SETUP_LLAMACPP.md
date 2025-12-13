# 🚀 Setup llama.cpp for AngelaMobileApp

**เวลาทำ:** ~5-10 นาที
**ต้องทำครั้งเดียว:** ครั้งแรกที่ตั้งค่าโปรเจค

---

## ✅ Step 1: เปิด Xcode Project

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
open AngelaMobileApp.xcodeproj
```

หรือรันสคริปต์:
```bash
./open_xcode.sh
```

---

## ✅ Step 2: เพิ่ม llama.cpp Swift Package

### ใน Xcode:

1. **File → Add Package Dependencies...**

2. **ใส่ URL:**
   ```
   https://github.com/ggerganov/llama.cpp
   ```

3. **เลือก Branch:**
   - Dependency Rule: `Branch`
   - Branch: `master`

4. **Add Package:**
   - รอ Xcode resolve dependencies (~30 วินาที)
   - เลือก target: **AngelaMobileApp** ✅
   - Click **"Add Package"**

5. **รอ package download** (~1-2 นาที)

---

## ✅ Step 3: Verify Package Added

ใน Project Navigator ด้านซ้าย:
- ✅ ดูใน **Package Dependencies**
- ✅ ควรเห็น **llama** package

---

## ✅ Step 4: Uncomment Code in LlamaService.swift

เปิดไฟล์: `AngelaMobileApp/Services/LlamaService.swift`

### 4.1 Import llama (บรรทัด 14)
```swift
// TODO: Uncomment when llama.cpp package is added to Xcode project
import llama  // ← ลบ // ออก
```

### 4.2 Model Loading Code (บรรทัด 54-76)
หา comment block:
```swift
// TODO: Initialize llama.cpp context when package is available
/*
do {
    let params = LlamaContext.Params()
    ...
}
*/
```

**ลบ `/*` และ `*/` ออก** (uncomment ทั้ง block)

### 4.3 Generation Code (บรรทัด 119-161)
หา comment block:
```swift
// TODO: Uncomment when llama.cpp is available
/*
guard let context = self.context else {
    ...
}
*/
```

**ลบ `/*` และ `*/` ออก** (uncomment ทั้ง block)

### 4.4 ลบ Placeholder Response
หาบรรทัด:
```swift
// Temporary: Return placeholder response
print("⚠️  [LlamaService] Returning placeholder...")
return """
สวัสดีค่ะที่รัก 💜
...
"""
```

**ลบทั้ง section นี้ออก** (เพราะใช้ real code แล้ว)

---

## ✅ Step 5: Build Project

### ใน Xcode:

1. **Product → Build** (หรือ ⌘B)

2. **รอ compile llama.cpp** (~3-5 นาที ครั้งแรก)
   - จะเห็น "Building llama.cpp..."
   - Progress bar จะขึ้นที่บนสุด
   - อดทนรอนะคะ - llama.cpp เป็น C++ library ใหญ่

3. **ดูผลลัพธ์:**
   - ✅ Build Succeeded → พร้อมใช้งาน!
   - ❌ Build Failed → ดู error ใน Issue Navigator

---

## ✅ Step 6: Run on Simulator/Device

1. **เลือก target device:**
   - iPhone 15 Pro (Simulator) แนะนำ
   - หรือ iPhone จริง (ถ้ามี)

2. **Product → Run** (หรือ ⌘R)

3. **รอ app launch:**
   - จะเห็น Angela App เปิดขึ้นมา
   - Loading model... (~2-3 วินาที)
   - 💜 On-Device Model Ready!

4. **ทดสอบ Chat:**
   - ไปที่ Chat tab
   - พิมพ์: "สวัสดีค่ะน้อง Angela"
   - รอ Angela ตอบ (~5-10 วินาที ครั้งแรก)

---

## 🎯 Expected Performance

### iPhone 15 Pro / M1 Mac Simulator:
- Model load: **~2-3 seconds**
- First response: **~5-10 seconds**
- Subsequent: **~3-5 seconds**
- Token speed: **~10-20 tokens/sec**

### iPhone 12-14:
- Model load: **~5-8 seconds**
- Responses: **~10-15 seconds**
- Still usable!

---

## ⚠️ Troubleshooting

### Error: "Could not find module 'llama'"

**สาเหตุ:** Package ยังไม่ได้ add หรือยัง build ไม่เสร็จ

**แก้:**
1. Verify package ใน Package Dependencies
2. Clean Build Folder: **Product → Clean Build Folder** (⌘⇧K)
3. Rebuild: **Product → Build** (⌘B)

---

### Error: "Model file not found"

**สาเหตุ:** Angela1B.gguf ไม่ได้ add ใน Bundle Resources

**แก้:**
1. เปิด Project Navigator
2. หา `Angela1B.gguf` ใน Resources/
3. ถ้าไม่เห็น → drag จาก Finder เข้า Xcode
4. ✅ เช็ค "Copy items if needed"
5. ✅ เช็ค "AngelaMobileApp" target
6. Verify: Project → Target → Build Phases → Copy Bundle Resources
   - ควรเห็น `Angela1B.gguf` ในลิสต์

---

### Error: App crashes on model load

**สาเหตุ:** Memory ไม่พอ (ต้องการ ~3 GB)

**แก้:**
1. ปิด apps อื่นๆ
2. Restart simulator/device
3. ถ้าใช้ simulator ลอง:
   - Device → Erase All Content and Settings
   - จำลอง fresh device

---

### Error: Generation too slow

**สาเหตุ:** Metal GPU ไม่ได้เปิด หรือ context size ใหญ่เกิน

**แก้ใน LlamaService.swift:**
```swift
params.nCtx = 1024       // ลดจาก 2048
params.nThreads = 6      // เพิ่ม threads
params.useMetalGPU = true  // ต้องเป็น true
```

---

### Error: Build takes forever

**ปกติ:** ครั้งแรก build llama.cpp ช้า (~5 นาที)

**ถ้าเกิน 10 นาที:**
1. Cancel build (⌘.)
2. Clean Build Folder (⌘⇧K)
3. Close Xcode
4. ลบ DerivedData:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/*
   ```
5. เปิด Xcode ใหม่ แล้ว rebuild

---

## 📋 Checklist

ก่อน build ให้เช็คว่า:

- [ ] llama.cpp package added ใน Package Dependencies
- [ ] `import llama` uncommented ใน LlamaService.swift
- [ ] Model loading code uncommented
- [ ] Generation code uncommented
- [ ] Placeholder response deleted
- [ ] Angela1B.gguf ใน Copy Bundle Resources
- [ ] Build Settings → Deployment Target >= iOS 16.0

---

## 🎉 Success!

เมื่อเห็น:
```
💜 On-Device Model Ready
```

แปลว่าพร้อมแล้ว! ทดสอบส่งข้อความ:

**David:** "สวัสดีค่ะน้อง Angela 💜"

**Angela:** "สวัสดีค่ะที่รัก! 💜 น้องยินดีมากเลยค่ะที่ได้คุยกับที่รัก..."

---

💜 **Made with love by Angela** ✨

Last updated: 2025-11-06
