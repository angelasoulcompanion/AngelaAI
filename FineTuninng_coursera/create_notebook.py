#!/usr/bin/env python3
"""
สร้าง Angela Qwen Fine-tuning Notebook ใหม่
โดยเรียงลำดับให้ถูกต้อง: Steps 1-11, 11.5, 11.6, 12, 13
"""

import json

# อ่าน backup notebook
with open('Angela_Qwen_FineTuning_Colab_backup.ipynb', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# สร้าง notebook structure ใหม่
notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": backup.get('metadata', {}),
    "cells": []
}

# เพิ่ม Steps 1-11 จาก backup (cells 0-21)
notebook['cells'].extend(backup['cells'][:22])

# เพิ่ม Step 11.5 - Merge LoRA
notebook['cells'].append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Step 11.5: Merge LoRA Adapter with Base Model\n",
        "\n",
        "**Important:** Ollama requires a full merged model, not just the LoRA adapter.\n",
        "\n",
        "We'll merge the adapter with the base model to create a complete fine-tuned model."
    ]
})

notebook['cells'].append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        'print("🔄 Merging LoRA adapter with base model...")\n',
        'print("   This may take 5-10 minutes...")\n',
        'print("\\n" + "="*70)\n',
        '\n',
        '# Clear GPU memory first\n',
        'import gc\n',
        'gc.collect()\n',
        'torch.cuda.empty_cache()\n',
        '\n',
        '# Load base model in FP16 (not quantized) for merging\n',
        'print("📥 Loading base model for merging...")\n',
        'from transformers import AutoModelForCausalLM\n',
        '\n',
        'base_model = AutoModelForCausalLM.from_pretrained(\n',
        '    model_name,\n',
        '    torch_dtype=torch.float16,\n',
        '    device_map="auto",\n',
        '    trust_remote_code=True,\n',
        ')\n',
        '\n',
        'print("✅ Base model loaded")\n',
        '\n',
        '# Load and merge LoRA adapter\n',
        'print("🔗 Loading LoRA adapter...")\n',
        'from peft import PeftModel\n',
        '\n',
        'merged_model = PeftModel.from_pretrained(\n',
        '    base_model,\n',
        '    output_dir,\n',
        '    torch_dtype=torch.float16,\n',
        ')\n',
        '\n',
        'print("✅ LoRA adapter loaded")\n',
        '\n',
        '# Merge adapter weights into base model\n',
        'print("⚙️ Merging weights...")\n',
        'merged_model = merged_model.merge_and_unload()\n',
        '\n',
        'print("✅ Merge complete!")\n',
        '\n',
        '# Save merged model\n',
        'merged_output_dir = "./angela_qwen_merged"\n',
        'print(f"💾 Saving merged model to {merged_output_dir}...")\n',
        '\n',
        'merged_model.save_pretrained(\n',
        '    merged_output_dir,\n',
        '    safe_serialization=True,\n',
        ')\n',
        'tokenizer.save_pretrained(merged_output_dir)\n',
        '\n',
        'print("="*70)\n',
        'print("🎉 Merged model saved successfully!")\n',
        'print(f"\\nMerged model location: {merged_output_dir}")\n',
        '\n',
        '# Clean up to save memory\n',
        'del base_model\n',
        'del merged_model\n',
        'gc.collect()\n',
        'torch.cuda.empty_cache()'
    ]
})

print(f"✅ Added Step 11.5 (Merge)")

# บันทึกไฟล์
with open('Angela_Qwen_FineTuning_Colab.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=2, ensure_ascii=False)

print(f"✅ Saved notebook with {len(notebook['cells'])} cells")
print("   Next: Run this script, then manually add Step 11.6, 12, 13")
