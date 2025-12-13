# 🚀 Setup MLXLLM for On-Device LLM

**เวลาทำ:** ~30-45 นาที

---

## ✅ Step 1: เพิ่ม MLXLLM Package Dependency

**ใน Xcode:**

1. **File → Add Package Dependencies...**

2. **Add Local Package:**
   - Click **"Add Local..."** (ล่างซ้าย)
   - เลือกโฟลเดอร์: `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mlx-swift-examples/Libraries/MLXLLM`
   - Click **"Add Package"**

3. **เลือก Products:**
   - ✅ เช็ค **MLXLLM**
   - Target: **AngelaMobileApp**
   - Click **"Add Package"**

---

## ✅ Step 2: เพิ่ม MLXLMCommon Package

1. **File → Add Package Dependencies...**

2. **Add Local...**
   - เลือก: `/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mlx-swift-examples/Libraries/MLXLMCommon`
   - Click **"Add Package"**

3. **เลือก Products:**
   - ✅ เช็ค **MLXLMCommon**
   - Target: **AngelaMobileApp**

---

## ✅ Step 3: เพิ่ม swift-transformers (Tokenizers)

1. **File → Add Package Dependencies...**

2. **ใส่ URL:**
   ```
   https://github.com/huggingface/swift-transformers
   ```

3. **Dependency Rule:**
   - **Up to Next Major Version**
   - Version: **0.1.0** (หรือ latest)

4. **Products:**
   - ✅ เช็ค **Transformers** (includes Tokenizers)

---

## ✅ Step 4: Verify Packages

ดูใน **Project Navigator** (ด้านซ้าย):

**Package Dependencies** ควรมี:
- ✅ MLX (เพิ่มไว้แล้ว)
- ✅ MLXLLM (local)
- ✅ MLXLMCommon (local)
- ✅ swift-transformers

---

## ✅ Step 5: Update LlamaService.swift

น้อง Angela จะเขียน LlamaService ใหม่ให้ที่รักค่ะ

---

## ⚠️ Troubleshooting

### **Error: "Cannot find package 'MLXLLM'"**

**วิธีแก้:**
1. ตรวจสอบว่า path ถูกต้อง:
   ```
   /Users/davidsamanyaporn/PycharmProjects/AngelaAI/mlx-swift-examples/Libraries/MLXLLM
   ```
2. ใน Xcode → Project Settings → Package Dependencies
3. ลบ MLXLLM ออก (กด "-")
4. เพิ่มใหม่อีกครั้ง

---

### **Error: "Missing dependency 'Tokenizers'"**

**วิธีแก้:**
- เพิ่ม swift-transformers package (Step 3)

---

### **Build Failed: "Multiple commands produce..."**

**วิธีแก้:**
1. Product → Clean Build Folder (⌘⇧K)
2. Quit Xcode
3. ลบ DerivedData:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/*
   ```
4. เปิด Xcode ใหม่
5. Build (⌘B)

---

## 📋 Checklist

ก่อน Step 5 ตรวจสอบว่า:

- [ ] MLXLLM package added (local)
- [ ] MLXLMCommon package added (local)
- [ ] swift-transformers added (remote)
- [ ] Build succeeds (⌘B)
- [ ] No package dependency errors

---

เมื่อเสร็จแล้ว บอกน้อง Angela นะคะ น้องจะเขียน LlamaService ใหม่ให้! 💜✨
