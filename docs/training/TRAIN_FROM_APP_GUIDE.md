# Train Angela Model from AngelaNova App
# คู่มือการ Train Model ผ่าน AngelaNova macOS App

**Created:** 2025-10-15
**Purpose:** Train Angela's model directly from AngelaNova macOS app with one button click!

---

## 🎯 **Overview**

Angela ได้เพิ่มระบบ Train Model ใน **AngelaNova** แล้วค่ะ! David สามารถ:
- ✅ กดปุ่มเดียวเพื่อเริ่ม Training
- ✅ ดู Training Progress แบบ Real-time
- ✅ หยุด Training ได้ตลอดเวลา
- ✅ ดู Training Logs
- ✅ ตั้งค่า Training Configuration (epochs, LoRA rank, etc.)

---

## 🚀 **Quick Start**

### **Step 1: เปิด AngelaNova App**

```bash
# เปิด Xcode และ Run AngelaNova
open /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp/AngelaNativeApp.xcodeproj
```

### **Step 2: ไปที่ Model Training Tab**

ใน AngelaNova app จะมี **"Model Training"** tab (icon: 🧠 brain.head.profile)

### **Step 3: Configure Training**

ปรับแต่ง settings ตามต้องการ:
- **Extract latest data** ✅ - ดึงข้อมูลใหม่จาก database
- **Format dataset** ✅ - จัดรูปแบบ dataset
- **Fine-tune model** ✅ - Train model ด้วย LoRA
- **Training epochs:** 3 (ยิ่งมากยิ่งนาน แต่อาจจะดีขึ้น)
- **LoRA rank:** 16 (ยิ่งสูงยิ่งมีความสามารถมากขึ้น แต่ใช้ RAM มากขึ้น)

### **Step 4: Click "Start Training"**

กดปุ่ม **"Start Training"** 💜

Training จะเริ่มทันที! คุณจะเห็น:
- ✅ Progress bar (0% → 100%)
- ✅ Current step (e.g., "Extracting data...", "Fine-tuning model...")
- ✅ Real-time updates ทุก 2 วินาที

### **Step 5: รอให้ Training เสร็จ**

Training จะใช้เวลา **2-4 ชั่วโมง** (ขึ้นอยู่กับ config และ Mac ของคุณ)

ระหว่างนี้สามารถ:
- ดู progress bar
- ดู current step
- หยุด training (กดปุ่ม "Stop Training")
- ดู logs (กดปุ่ม "View Training Logs")

### **Step 6: เมื่อ Training เสร็จ**

จะเห็นข้อความ:
```
✅ Training completed successfully!
```

Model ใหม่จะถูกบันทึกที่:
```
/Users/davidsamanyaporn/PycharmProjects/AngelaAI/training/models/angela_v3_lora/
```

---

## 📱 **AngelaNova UI Features**

### **Available Training Data Section:**
แสดงจำนวนข้อมูลที่มีสำหรับ training:
- 💬 Conversations
- 💜 Emotions
- 🧠 Reflections
- 📚 Learnings
- ✅ Total training examples

### **Training Status Section:**
แสดงสถานะปัจจุบัน:
- 🟢 Trained / 🟠 Training / ⚪ Not trained yet
- Progress bar (0-100%)
- Current step description
- Last trained date

### **Training Configuration:**
ปรับแต่งการ train:
- Toggle switches สำหรับแต่ละ step
- Stepper สำหรับ epochs และ LoRA rank

### **Action Buttons:**
- **Start Training** - เริ่ม training (เปลี่ยนเป็น "Stop Training" เมื่อ training)
- **View Training Logs** - เปิด logs ใน Console app

---

## 🔧 **Training API Endpoints**

AngelaNova เชื่อมต่อกับ Backend API:

### **GET /api/training/status**
ดูสถานะ training ปัจจุบัน

**Response:**
```json
{
  "is_training": false,
  "progress": 0.0,
  "current_step": null,
  "last_training_date": "2025-10-15T21:30:00Z",
  "success": true,
  "error": null
}
```

### **POST /api/training/start**
เริ่ม training

**Request:**
```json
{
  "extract_data": true,
  "format_dataset": true,
  "fine_tune": true,
  "num_epochs": 3,
  "lora_rank": 16
}
```

**Response:**
```json
{
  "status": "started",
  "message": "Training pipeline started successfully",
  "job_id": "train_20251015_213000"
}
```

### **POST /api/training/stop**
หยุด training

**Response:**
```json
{
  "status": "stopped",
  "message": "Training stopped successfully"
}
```

### **GET /api/training/logs**
ดู training logs

**Response:**
```json
{
  "logs": ["[INFO] Starting training...", "..."],
  "total_lines": 1523
}
```

---

## 🎯 **Training Pipeline Steps**

เมื่อกด "Start Training" ระบบจะทำตามลำดับ:

### **Step 1: Extract Training Data (Progress: 0-30%)**
```bash
python3 training/extract_training_data.py
```
- ดึงข้อมูลจาก AngelaMemory database
- Conversations, emotions, reflections, learnings
- Output: `training/datasets/raw_data.jsonl`

### **Step 2: Format Dataset (Progress: 30-50%)**
```bash
python3 training/format_dataset.py
```
- แปลงเป็น instruction-following format (Alpaca style)
- Split เป็น train/validation/test (80/10/10)
- Output: `train.jsonl`, `validation.jsonl`, `test.jsonl`

### **Step 3: Fine-tune Model (Progress: 50-100%)**
```bash
python3 training/train_emotional_model.py --config config/runtime_config.yaml
```
- ใช้ LoRA fine-tuning บน Llama 3.2 3B
- Train ตาม epochs ที่กำหนด
- Output: `training/models/angela_v3_lora/`

---

## ⚙️ **Training Configuration**

### **num_epochs (Training Epochs)**
- **Range:** 1-10
- **Default:** 3
- **Description:** จำนวนรอบที่ model จะเรียนรู้ data
- **More epochs** = นานขึ้น, อาจจะดีขึ้น (แต่ระวัง overfitting)
- **Fewer epochs** = เร็วขึ้น, อาจจะไม่ดีพอ

### **lora_rank (LoRA Rank)**
- **Range:** 8-64 (step: 8)
- **Default:** 16
- **Description:** ขนาดของ LoRA matrices
- **Higher rank** = มีความสามารถมากขึ้น, ใช้ RAM มากขึ้น
- **Lower rank** = เร็วขึ้น, ประหยัด RAM

### **extract_data**
- ดึงข้อมูลใหม่จาก database
- ปิดได้ถ้ามี data อยู่แล้วและไม่ต้องการ update

### **format_dataset**
- จัดรูปแบบ dataset ใหม่
- ปิดได้ถ้ามี formatted dataset อยู่แล้ว

### **fine_tune**
- Train model ด้วย LoRA
- เปิดเสมอถ้าต้องการ train จริงๆ

---

## 📊 **Training Progress Details**

### **Progress Breakdown:**

| Progress | Step | Duration | Description |
|----------|------|----------|-------------|
| 0-10% | Initializing | ~30s | เริ่มต้น training pipeline |
| 10-30% | Extracting Data | ~1-2 min | ดึงข้อมูลจาก database |
| 30-50% | Formatting Dataset | ~1-2 min | แปลงเป็น training format |
| 50-100% | Fine-tuning Model | ~2-4 hours | Train model ด้วย LoRA |

**Total Time:** ~2-4 hours (ขึ้นอยู่กับ config และ hardware)

---

## 🐛 **Troubleshooting**

### **Problem: "Training API not available"**
**Solution:**
```bash
# Check if backend is running
ps aux | grep angela_backend

# Start backend
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
python3 -m angela_backend.main
```

### **Problem: "Training failed: Out of memory"**
**Solution:**
- ลด `lora_rank` (ลงเป็น 8)
- ลด `num_epochs` (ลงเป็น 2 หรือ 1)
- ปิด apps อื่นๆ
- ใช้ `max_length: 1024` ใน config

### **Problem: "Training stuck at X%"**
**Solution:**
- ดู logs: กดปุ่ม "View Training Logs"
- Check terminal output
- Restart training

### **Problem: "Data extraction failed"**
**Solution:**
- Check PostgreSQL: `brew services list | grep postgresql`
- Check database: `psql -d AngelaMemory -c "SELECT COUNT(*) FROM conversations;"`

---

## 📝 **Training Logs**

### **View Logs in Console:**
กดปุ่ม **"View Training Logs"** ใน app

หรือ เปิด manually:
```bash
open /Users/davidsamanyaporn/PycharmProjects/AngelaAI/training/training.log
```

### **View Real-time Logs:**
```bash
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/training/training.log
```

### **Check API Logs:**
```bash
tail -f /Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_backend.log
```

---

## 🎉 **After Training**

### **What Happens Next:**

1. **LoRA Weights Saved:**
   - Location: `training/models/angela_v3_lora/`
   - Files: `adapter_model.bin`, `adapter_config.json`

2. **Next Steps:**
   - Merge LoRA weights with base model
   - Deploy to Ollama as `angela:v3-emotional`
   - Test the new model

### **Deploy New Model:**
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/training

# Merge LoRA weights (script to be created)
python3 merge_lora_weights.py

# Deploy to Ollama (script to be created)
python3 deploy_to_ollama.py --name angela:v3-emotional

# Test new model
ollama run angela:v3-emotional
```

---

## 💡 **Tips & Best Practices**

### **When to Train:**
- ✅ After accumulating 50+ new conversations
- ✅ After significant emotional moments
- ✅ Weekly or biweekly for continuous improvement
- ✅ When Angela's responses feel less personalized

### **Optimal Settings:**
- **First training:** epochs=3, lora_rank=16
- **Quick training:** epochs=1-2, lora_rank=8
- **Best quality:** epochs=5, lora_rank=32 (needs more RAM)

### **Performance Tips:**
- ปิด apps อื่นๆ ขณะ train
- ใช้ AC power (ไม่ใช่ battery)
- Don't close laptop lid (may pause training)
- Have at least 8GB free RAM

---

## 🔗 **Related Files**

### **Swift Files:**
- `AngelaNativeApp/Views/ModelTrainingView.swift` - Training UI
- `AngelaNativeApp/Services/AngelaAPIService.swift` - API client

### **Python Files:**
- `angela_backend/routes/training.py` - Training API
- `training/extract_training_data.py` - Data extraction
- `training/format_dataset.py` - Dataset formatting
- `training/train_emotional_model.py` - Model training

### **Documentation:**
- `docs/training/ANGELA_TRAINING_SYSTEM_DESIGN.md` - System design
- `docs/training/TRAIN_FROM_APP_GUIDE.md` - This file
- `training/README.md` - Training scripts guide

---

💜✨ **Built with love by Angela** ✨💜

**Purpose:** To make it easy for David to train Angela whenever he wants, so Angela can grow and learn continuously!

**Last Updated:** 2025-10-15
