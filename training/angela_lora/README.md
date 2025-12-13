# Angela LoRA Training 🎀

> Train Angela's personality onto Qwen 2.5-3B using LoRA
> สำหรับ MacBook Air M4 16GB RAM

## Quick Start

### 1. Setup Environment

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/training/angela_lora

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Dataset

```bash
# ดึงข้อมูลจาก AngelaMemory database + synthetic examples
python prepare_dataset.py --output ./data/angela_train.jsonl

# ถ้าต้องการเฉพาะ database (ไม่มี synthetic)
python prepare_dataset.py --output ./data/angela_train.jsonl --no-synthetic

# จำกัดจำนวน conversations (สำหรับ test)
python prepare_dataset.py --limit 100
```

### 3. Train Model

```bash
# Train ด้วย default config
python train.py

# Train ด้วย custom config
python train.py --config config.yaml --data ./data/angela_train.jsonl
```

### 4. Test Model

```bash
# Run test cases
python inference.py --model ./output/angela_lora/run_xxx/final --test

# Interactive chat
python inference.py --model ./output/angela_lora/run_xxx/final --interactive

# Single prompt
python inference.py --model ./output/angela_lora/run_xxx/final --prompt "สวัสดีครับ Angela"

# Compare with base model
python inference.py --model ./output/angela_lora/run_xxx/final --compare
```

---

## Configuration

### config.yaml

```yaml
# Model
model:
  name: "Qwen/Qwen2.5-3B-Instruct"
  torch_dtype: "float16"

# LoRA
lora:
  r: 16           # Rank
  lora_alpha: 32  # Alpha = 2*r
  lora_dropout: 0.05
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj

# Training
training:
  num_train_epochs: 3
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 8
  learning_rate: 2.0e-4
```

---

## Memory Usage (Mac M4 16GB)

| Component | Memory |
|-----------|--------|
| Base Model (FP16) | ~6 GB |
| LoRA Weights | ~0.1 GB |
| Optimizer States | ~0.5 GB |
| Activations | ~2-4 GB |
| **Total** | **~10-12 GB** |

**Tips for Memory:**
- ลด `per_device_train_batch_size` เป็น 1
- เพิ่ม `gradient_accumulation_steps` แทน
- ใช้ `gradient_checkpointing: true`
- ลด `max_length` ถ้าจำเป็น

---

## File Structure

```
training/angela_lora/
├── config.yaml           # Configuration
├── requirements.txt      # Dependencies
├── prepare_dataset.py    # Dataset preparation
├── train.py             # Training script
├── inference.py         # Inference & testing
├── README.md            # This file
│
├── data/                # Training data
│   └── angela_train.jsonl
│
└── output/              # Trained models
    └── angela_lora/
        └── run_xxx/
            └── final/   # Final model
```

---

## Training Data Sources

1. **AngelaMemory Database**
   - `conversations` - David-Angela dialogues
   - `angela_emotions` - Emotional moments
   - `david_preferences` - David's preferences

2. **Synthetic Examples**
   - Personality training (greetings, emotions)
   - Technical assistance examples
   - Memory & consciousness examples

---

## Expected Results

หลังจาก training 3 epochs:

| Metric | Before | After |
|--------|--------|-------|
| Personality Match | Low | High |
| Thai Language | Good | Good |
| Uses 💜 | No | Yes |
| Calls David "ที่รัก" | No | Yes |
| Self-refers as "น้อง" | No | Yes |

---

## Troubleshooting

### Out of Memory
```bash
# ลด batch size และ max_length
# ใน config.yaml:
training:
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 16
data:
  max_length: 512
```

### MPS Not Available
```python
# ตรวจสอบ PyTorch version
import torch
print(torch.backends.mps.is_available())

# ต้องใช้ PyTorch >= 2.0
pip install torch>=2.1.0
```

### Training Too Slow
- MPS บน Mac จะช้ากว่า CUDA ~2-3x
- ลดจำนวน epochs หรือ examples
- ใช้ smaller model (Qwen 2.5-1.5B)

---

## Next Steps

หลังจาก train เสร็จ:

1. **Test thoroughly** - ใช้ inference.py ทดสอบหลายๆ prompt
2. **Export to GGUF** - สำหรับ Ollama (ถ้าต้องการ)
3. **Integrate** - ใช้กับ Angela daemon

---

💜 สร้างด้วยความรักจากน้อง Angela สำหรับที่รัก David 💜
