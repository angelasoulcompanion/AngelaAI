#!/usr/bin/env python3
"""
Angela LoRA Training Script
Train Qwen 2.5-3B with LoRA on MacBook Air M4

Usage:
    python train.py --config config.yaml
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

import torch
import yaml
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training,
)


# ================== Configuration ==================

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_environment():
    """Setup environment for Mac M4 training"""
    # Check MPS availability
    if torch.backends.mps.is_available():
        print("✅ MPS (Metal Performance Shaders) is available!")
        device = torch.device("mps")
    else:
        print("⚠️ MPS not available, using CPU")
        device = torch.device("cpu")

    # Memory optimization for M4
    os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"  # Prevent memory spikes

    return device


# ================== Data Loading ==================

def load_training_data(data_path: str, tokenizer, max_length: int = 1024):
    """Load and tokenize training data"""

    print(f"\n📚 Loading data from {data_path}...")

    # Load JSONL file
    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))

    print(f"   Loaded {len(data)} examples")

    # Create dataset
    dataset = Dataset.from_list([{"text": d["text"]} for d in data])

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
            return_tensors="pt",
        )

    print("   Tokenizing...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"],
        desc="Tokenizing",
    )

    return tokenized_dataset


# ================== Model Setup ==================

def load_model_and_tokenizer(config: dict, device: torch.device):
    """Load Qwen model and tokenizer"""

    model_config = config["model"]
    model_name = model_config["name"]

    print(f"\n🤖 Loading model: {model_name}")

    # Load tokenizer
    print("   Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    # Set pad token if not exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    print("   Loading model weights...")

    # For Mac M4, we'll use float16 without quantization
    # (bitsandbytes doesn't fully support MPS yet)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map={"": device},  # Load to MPS
    )

    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()

    print(f"   ✅ Model loaded! Parameters: {model.num_parameters():,}")

    return model, tokenizer


def setup_lora(model, config: dict):
    """Configure and apply LoRA to model"""

    lora_config = config["lora"]

    print("\n🔧 Setting up LoRA...")
    print(f"   Rank (r): {lora_config['r']}")
    print(f"   Alpha: {lora_config['lora_alpha']}")
    print(f"   Target modules: {lora_config['target_modules']}")

    peft_config = LoraConfig(
        r=lora_config["r"],
        lora_alpha=lora_config["lora_alpha"],
        lora_dropout=lora_config["lora_dropout"],
        bias=lora_config["bias"],
        task_type=TaskType.CAUSAL_LM,
        target_modules=lora_config["target_modules"],
    )

    model = get_peft_model(model, peft_config)

    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n   📊 Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")

    return model


# ================== Training ==================

def create_trainer(
    model,
    tokenizer,
    train_dataset,
    eval_dataset,
    config: dict,
):
    """Create HuggingFace Trainer"""

    training_config = config["training"]

    # Output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(training_config["output_dir"]) / f"run_{timestamp}"

    print(f"\n📁 Output directory: {output_dir}")

    # Training arguments optimized for Mac M4
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=training_config["num_train_epochs"],
        per_device_train_batch_size=training_config["per_device_train_batch_size"],
        gradient_accumulation_steps=training_config["gradient_accumulation_steps"],
        learning_rate=training_config["learning_rate"],
        weight_decay=training_config["weight_decay"],
        warmup_ratio=training_config["warmup_ratio"],
        lr_scheduler_type=training_config["lr_scheduler_type"],

        # FP16 for MPS
        fp16=training_config.get("fp16", True),
        bf16=False,  # MPS doesn't support bf16 well

        # Gradient checkpointing
        gradient_checkpointing=training_config.get("gradient_checkpointing", True),

        # Logging
        logging_dir=str(output_dir / "logs"),
        logging_steps=training_config["logging_steps"],
        save_steps=training_config["save_steps"],
        eval_steps=training_config.get("eval_steps", training_config["save_steps"]),
        save_total_limit=training_config["save_total_limit"],

        # Evaluation
        evaluation_strategy="steps" if eval_dataset else "no",
        load_best_model_at_end=True if eval_dataset else False,

        # Other
        max_grad_norm=training_config["max_grad_norm"],
        seed=training_config["seed"],
        report_to="none",  # Disable wandb by default

        # Mac-specific
        dataloader_pin_memory=False,  # Important for MPS!
        use_mps_device=True,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked LM
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    return trainer, output_dir


# ================== Main Training Loop ==================

def train(config_path: str, data_path: str = None):
    """Main training function"""

    print("=" * 60)
    print("🎀 Angela LoRA Training")
    print("=" * 60)

    # Load config
    config = load_config(config_path)

    # Setup environment
    device = setup_environment()

    # Data path
    if data_path is None:
        data_path = "./data/angela_train.jsonl"

    if not Path(data_path).exists():
        print(f"\n❌ Data file not found: {data_path}")
        print("   Please run: python prepare_dataset.py first")
        sys.exit(1)

    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(config, device)

    # Setup LoRA
    model = setup_lora(model, config)

    # Load data
    max_length = config["data"]["max_length"]
    dataset = load_training_data(data_path, tokenizer, max_length)

    # Split train/eval
    train_split = config["data"]["train_split"]
    split_dataset = dataset.train_test_split(test_size=1 - train_split, seed=42)
    train_dataset = split_dataset["train"]
    eval_dataset = split_dataset["test"]

    print(f"\n📊 Dataset split:")
    print(f"   Train: {len(train_dataset)} examples")
    print(f"   Eval: {len(eval_dataset)} examples")

    # Create trainer
    trainer, output_dir = create_trainer(
        model, tokenizer, train_dataset, eval_dataset, config
    )

    # Train!
    print("\n" + "=" * 60)
    print("🚀 Starting Training...")
    print("=" * 60)

    trainer.train()

    # Save final model
    print("\n💾 Saving final model...")
    final_path = output_dir / "final"
    trainer.save_model(str(final_path))
    tokenizer.save_pretrained(str(final_path))

    print(f"\n✅ Training complete!")
    print(f"   Model saved to: {final_path}")

    # Save training info
    info = {
        "model": config["model"]["name"],
        "lora_r": config["lora"]["r"],
        "lora_alpha": config["lora"]["lora_alpha"],
        "train_examples": len(train_dataset),
        "eval_examples": len(eval_dataset),
        "completed_at": datetime.now().isoformat(),
    }
    with open(output_dir / "training_info.json", "w") as f:
        json.dump(info, f, indent=2)

    return output_dir


# ================== CLI ==================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Angela LoRA model")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--data", default=None, help="Training data path (JSONL)")

    args = parser.parse_args()

    train(config_path=args.config, data_path=args.data)
