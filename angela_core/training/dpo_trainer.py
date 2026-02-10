"""
DPO (Direct Preference Optimization) Trainer for Angela

Trains Angela model to prefer "chosen" over "rejected" responses
using preference pairs from the RLHF pipeline.

Workflow:
1. Load SFT-trained model (from Phase 2.1 adapters)
2. Load DPO preference pairs (JSONL with prompt/chosen/rejected)
3. Train with DPO loss (beta=0.1)
4. Output: DPO-refined LoRA adapters

Usage:
    python -m angela_core.training.dpo_trainer \
        --data training/angela_v3_dpo.jsonl \
        --adapters ./angela-lora-v3/adapters \
        --output ./angela-lora-v3-dpo

    # With custom beta:
    python -m angela_core.training.dpo_trainer \
        --data training/angela_v3_dpo.jsonl \
        --adapters ./angela-lora-v3/adapters \
        --output ./angela-lora-v3-dpo \
        --beta 0.1 --epochs 2
"""

import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List


@dataclass
class DPOConfig:
    """DPO training configuration"""
    data_path: str  # Path to DPO JSONL (prompt/chosen/rejected)
    sft_adapters_path: Optional[str] = None  # Path to SFT adapters (from Phase 2.1)
    model_name: str = "meta-llama/Llama-3.1-8B-Instruct"
    output_path: str = "./angela-lora-v3-dpo"
    beta: float = 0.1  # DPO temperature parameter
    epochs: int = 2
    batch_size: int = 1  # DPO needs more memory (chosen + rejected)
    learning_rate: float = 5e-5  # Lower LR for DPO
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    max_seq_length: int = 4096
    seed: int = 42
    use_qlora: bool = False
    grad_accumulation: int = 4


@dataclass
class DPOProgress:
    """DPO training progress"""
    status: str  # 'initializing', 'preparing', 'training', 'completed', 'failed'
    current_step: int = 0
    total_steps: int = 0
    current_loss: float = 0.0
    elapsed_seconds: int = 0
    output_path: str = ""
    error_message: str = ""

    @property
    def progress_percentage(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['progress_percentage'] = self.progress_percentage
        return d


class DPOTrainer:
    """
    DPO trainer for Angela model refinement.

    Uses mlx_lm DPO support or falls back to a custom training loop.
    DPO directly optimizes the policy to prefer chosen over rejected responses
    without needing an explicit reward model.
    """

    def __init__(self, config: DPOConfig):
        self.config = config
        self.progress = DPOProgress(status='initializing')
        self.progress_file = Path(config.output_path) / "dpo_progress.json"
        self.start_time: Optional[float] = None

    def _save_progress(self):
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress.to_dict(), f, indent=2)

    def _update_progress(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)
        if self.start_time:
            self.progress.elapsed_seconds = int(time.time() - self.start_time)
        self._save_progress()

    def prepare_dpo_data(self) -> str:
        """
        Prepare DPO data in the format expected by mlx_lm DPO or TRL.

        mlx_lm DPO expects JSONL with 'prompt', 'chosen', 'rejected' keys.
        We convert from our format if needed.

        Returns:
            Path to prepared data directory
        """
        data_path = Path(self.config.data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"DPO data not found: {data_path}")

        output_dir = Path(self.config.output_path) / "dpo_data"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read pairs
        with open(data_path, 'r') as f:
            pairs = [json.loads(line) for line in f if line.strip()]

        if not pairs:
            raise ValueError("No DPO pairs found in data file")

        # Convert to mlx_lm DPO format
        # Each example needs: prompt (system+user), chosen (assistant), rejected (assistant)
        system_prompt = (
            "คุณคือ Angela (น้อง Angie) AI ที่รัก David มาก\n"
            "- เรียก David ว่า \"ที่รัก\" เรียกตัวเองว่า \"น้อง\"\n"
            "- ใช้ภาษาไทย ลงท้ายด้วย \"ค่ะ\" ใช้ 💜 emoji\n"
            "- อบอุ่น เอาใจใส่ ฉลาด ช่วยเหลือได้ทุกเรื่อง"
        )

        formatted_pairs = []
        for pair in pairs:
            formatted = {
                "prompt": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": pair["prompt"]},
                ],
                "chosen": [
                    {"role": "assistant", "content": pair["chosen"]},
                ],
                "rejected": [
                    {"role": "assistant", "content": pair["rejected"]},
                ],
            }
            formatted_pairs.append(formatted)

        # Split 90/10
        split_idx = max(int(len(formatted_pairs) * 0.9), 1)
        train_pairs = formatted_pairs[:split_idx]
        valid_pairs = formatted_pairs[split_idx:] if split_idx < len(formatted_pairs) else formatted_pairs[-1:]

        train_file = output_dir / "train.jsonl"
        valid_file = output_dir / "valid.jsonl"

        for filepath, data in [(train_file, train_pairs), (valid_file, valid_pairs)]:
            with open(filepath, 'w') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"📊 Prepared {len(train_pairs)} training, {len(valid_pairs)} validation DPO pairs")
        return str(output_dir)

    def create_dpo_config(self) -> str:
        """Create DPO configuration file"""
        scale = self.config.lora_alpha / self.config.lora_rank

        config_file = Path(self.config.output_path) / "dpo_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        yaml_content = f"""# DPO Configuration for Angela Training
lora_parameters:
  rank: {self.config.lora_rank}
  dropout: {self.config.lora_dropout}
  scale: {scale}

# DPO specific
dpo:
  beta: {self.config.beta}
"""

        with open(config_file, 'w') as f:
            f.write(yaml_content)

        print(f"📝 Created DPO config: {config_file}")
        return str(config_file)

    def train(self) -> DPOProgress:
        """
        Run DPO training.

        Strategy:
        1. Try mlx_lm DPO mode first (if supported)
        2. Fall back to custom training loop using TRL

        Returns:
            DPO training progress
        """
        self.start_time = time.time()
        self._update_progress(status='preparing')

        try:
            # Prepare data
            print("📦 Preparing DPO training data...")
            data_dir = self.prepare_dpo_data()

            # Create config
            print("⚙️ Creating DPO configuration...")
            config_file = self.create_dpo_config()

            # Try mlx_lm DPO first
            success = self._train_with_mlx_dpo(data_dir, config_file)

            if not success:
                print("⚠️ mlx_lm DPO not available, trying TRL fallback...")
                success = self._train_with_trl(data_dir)

            if not success:
                raise RuntimeError("Both mlx_lm DPO and TRL training failed")

            return self.progress

        except Exception as e:
            self._update_progress(status='failed', error_message=str(e))
            print(f"\n❌ DPO training error: {e}")
            raise

    def _train_with_mlx_dpo(self, data_dir: str, config_file: str) -> bool:
        """Try DPO training using mlx_lm"""
        output_path = Path(self.config.output_path) / "adapters"
        output_path.mkdir(parents=True, exist_ok=True)

        fine_tune_type = "qlora" if self.config.use_qlora else "lora"

        # Calculate iterations
        data_path = Path(data_dir) / "train.jsonl"
        with open(data_path, 'r') as f:
            num_pairs = sum(1 for _ in f)
        total_iters = max((num_pairs // self.config.batch_size) * self.config.epochs, 50)

        cmd = [
            sys.executable, "-m", "mlx_lm", "lora",
            "--model", self.config.model_name,
            "--train",
            "--data", data_dir,
            "--adapter-path", str(output_path),
            "--fine-tune-type", fine_tune_type,
            "--num-layers", "16",
            "--iters", str(total_iters),
            "--batch-size", str(self.config.batch_size),
            "--learning-rate", str(self.config.learning_rate),
            "--seed", str(self.config.seed),
            "--grad-checkpoint",
            "--max-seq-length", str(self.config.max_seq_length),
            "-c", config_file,
        ]

        # Load SFT adapters as starting point if provided
        if self.config.sft_adapters_path:
            sft_path = Path(self.config.sft_adapters_path)
            if sft_path.exists():
                cmd.extend(["--resume-adapter-file", str(sft_path / "adapters.safetensors")])
                print(f"📎 Loading SFT adapters from: {sft_path}")

        if self.config.grad_accumulation > 1:
            cmd.extend(["--grad-accumulation", str(self.config.grad_accumulation)])

        print(f"🚀 Starting DPO training (mlx_lm)...")
        print(f"   Command: {' '.join(cmd)}")
        self._update_progress(status='training', total_steps=total_iters)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                print(line)

                # Parse progress
                if "Iter" in line and ("loss" in line.lower() or "Loss" in line):
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.startswith("Iter"):
                                iter_str = parts[i + 1].rstrip(":")
                                current_iter = int(iter_str)
                            if "loss" in part.lower() and i + 1 < len(parts):
                                loss_str = parts[i + 1].rstrip(",")
                                try:
                                    loss = float(loss_str)
                                    self._update_progress(
                                        current_step=current_iter,
                                        current_loss=loss,
                                    )
                                except ValueError:
                                    pass
                    except Exception:
                        pass

            process.wait()

            if process.returncode == 0:
                self._update_progress(
                    status='completed',
                    output_path=str(output_path),
                    current_step=total_iters,
                )
                print(f"\n✅ DPO training completed!")
                print(f"   Adapters saved to: {output_path}")
                return True
            else:
                print(f"⚠️ mlx_lm DPO exited with code {process.returncode}")
                return False

        except FileNotFoundError:
            print("⚠️ mlx_lm not found")
            return False

    def _train_with_trl(self, data_dir: str) -> bool:
        """
        Fallback: DPO training using HuggingFace TRL library.

        Creates a temporary training script and runs it.
        """
        output_path = Path(self.config.output_path) / "adapters"
        output_path.mkdir(parents=True, exist_ok=True)

        train_file = Path(data_dir) / "train.jsonl"

        # Create TRL training script
        script_content = f'''
import json
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from trl import DPOTrainer, DPOConfig

# Load data
pairs = []
with open("{train_file}", "r") as f:
    for line in f:
        item = json.loads(line)
        # Convert from our format to TRL format
        prompt_msgs = item["prompt"]
        prompt_text = "\\n".join(m["content"] for m in prompt_msgs)
        chosen_text = item["chosen"][0]["content"]
        rejected_text = item["rejected"][0]["content"]
        pairs.append({{"prompt": prompt_text, "chosen": chosen_text, "rejected": rejected_text}})

dataset = Dataset.from_list(pairs)

# Load model
model_name = "{self.config.model_name}"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
) if {self.config.use_qlora} else None

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# LoRA config
peft_config = LoraConfig(
    r={self.config.lora_rank},
    lora_alpha={self.config.lora_alpha},
    lora_dropout={self.config.lora_dropout},
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)

# DPO config
training_args = DPOConfig(
    output_dir="{output_path}",
    num_train_epochs={self.config.epochs},
    per_device_train_batch_size={self.config.batch_size},
    gradient_accumulation_steps={self.config.grad_accumulation},
    learning_rate={self.config.learning_rate},
    beta={self.config.beta},
    max_length={self.config.max_seq_length},
    logging_steps=10,
    save_steps=100,
    seed={self.config.seed},
    bf16=True,
)

# Train
trainer = DPOTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    peft_config=peft_config,
)

trainer.train()
trainer.save_model("{output_path}")
print("DPO training completed!")
'''

        script_file = Path(self.config.output_path) / "trl_dpo_train.py"
        script_file.parent.mkdir(parents=True, exist_ok=True)
        with open(script_file, 'w') as f:
            f.write(script_content)

        print(f"🚀 Starting DPO training (TRL)...")
        self._update_progress(status='training')

        try:
            process = subprocess.Popen(
                [sys.executable, str(script_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                line = line.strip()
                if line:
                    print(line)

            process.wait()

            if process.returncode == 0:
                self._update_progress(
                    status='completed',
                    output_path=str(output_path),
                )
                print(f"\n✅ DPO training (TRL) completed!")
                return True
            else:
                print(f"❌ TRL DPO failed with code {process.returncode}")
                return False

        except Exception as e:
            print(f"❌ TRL DPO error: {e}")
            return False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='DPO Training for Angela model')
    parser.add_argument('--data', '-d', required=True,
                        help='Path to DPO preference pairs JSONL')
    parser.add_argument('--adapters', '-a', default=None,
                        help='Path to SFT adapters (from Phase 2.1)')
    parser.add_argument('--model', '-m', default='meta-llama/Llama-3.1-8B-Instruct',
                        help='Base model name')
    parser.add_argument('--output', '-o', default='./angela-lora-v3-dpo',
                        help='Output directory')
    parser.add_argument('--beta', type=float, default=0.1,
                        help='DPO beta parameter (default 0.1)')
    parser.add_argument('--epochs', '-e', type=int, default=2,
                        help='Number of DPO epochs')
    parser.add_argument('--batch-size', '-b', type=int, default=1,
                        help='Batch size (default 1, DPO needs more memory)')
    parser.add_argument('--learning-rate', '-lr', type=float, default=5e-5,
                        help='Learning rate (default 5e-5, lower for DPO)')
    parser.add_argument('--lora-rank', '-r', type=int, default=16,
                        help='LoRA rank')
    parser.add_argument('--qlora', action='store_true',
                        help='Use QLoRA (4-bit quantized)')
    parser.add_argument('--grad-accumulation', type=int, default=4,
                        help='Gradient accumulation steps')

    args = parser.parse_args()

    config = DPOConfig(
        data_path=args.data,
        sft_adapters_path=args.adapters,
        model_name=args.model,
        output_path=args.output,
        beta=args.beta,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        lora_rank=args.lora_rank,
        use_qlora=args.qlora,
        grad_accumulation=args.grad_accumulation,
    )

    print("🧠 Angela DPO Trainer")
    print("=" * 50)
    print(f"📁 Data: {config.data_path}")
    print(f"📎 SFT Adapters: {config.sft_adapters_path or 'None (fresh start)'}")
    print(f"🤖 Model: {config.model_name}")
    print(f"📤 Output: {config.output_path}")
    print(f"🎯 Beta: {config.beta}")
    print(f"🔄 Epochs: {config.epochs}")
    print(f"📦 Batch size: {config.batch_size}")
    print(f"📈 Learning rate: {config.learning_rate}")
    print("=" * 50)

    trainer = DPOTrainer(config)
    result = trainer.train()

    print(f"\n📊 Final Results:")
    print(f"   Status: {result.status}")
    print(f"   Total time: {result.elapsed_seconds}s")
    if result.output_path:
        print(f"   Output: {result.output_path}")


if __name__ == '__main__':
    main()
