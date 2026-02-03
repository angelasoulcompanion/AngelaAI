"""
MLX LoRA Trainer for Angela

Uses Apple's MLX framework to fine-tune language models with LoRA adapters.
Optimized for Apple Silicon (M1/M2/M3) with unified memory.

Updated for mlx_lm 2024+ format:
- Uses "mlx_lm lora" command (not mlx_lm.lora)
- Uses --num-layers instead of --lora-layers
- Uses -c config for lora_parameters (rank, scale, dropout)
- Uses --fine-tune-type lora

Usage:
    python -m angela_core.training.mlx_lora_trainer \
        --data training_data.jsonl \
        --model Qwen/Qwen2.5-3B-Instruct \
        --output ./angela-lora

    # Or with all options:
    python -m angela_core.training.mlx_lora_trainer \
        --data training_data.jsonl \
        --model Qwen/Qwen2.5-3B-Instruct \
        --output ./angela-lora \
        --epochs 3 \
        --batch-size 4 \
        --lora-rank 16 \
        --learning-rate 1e-4
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import threading


@dataclass
class TrainingConfig:
    """Training configuration"""
    data_path: str
    model_name: str = "Qwen/Qwen2.5-3B-Instruct"
    output_path: str = "./angela-lora"
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 1e-4
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    warmup_steps: int = 100
    save_every: int = 100
    test_batches: int = 10
    max_seq_length: int = 2048
    seed: int = 42


@dataclass
class TrainingProgress:
    """Training progress update"""
    status: str  # 'initializing', 'training', 'completed', 'failed'
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    current_loss: float = 0.0
    learning_rate: float = 0.0
    tokens_per_second: float = 0.0
    elapsed_seconds: int = 0
    estimated_remaining: int = 0
    recent_log: str = ""
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


class MLXLoRATrainer:
    """
    MLX-based LoRA fine-tuning trainer.

    Uses mlx-lm library for efficient training on Apple Silicon.
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.progress = TrainingProgress(status='initializing')
        self.progress_file = Path(config.output_path) / "progress.json"
        self.start_time = None
        self._stop_requested = False

    def _save_progress(self):
        """Save current progress to file"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress.to_dict(), f, indent=2)

    def _update_progress(self, **kwargs):
        """Update progress and save to file"""
        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)

        if self.start_time:
            self.progress.elapsed_seconds = int(time.time() - self.start_time)

            # Estimate remaining time
            if self.progress.current_step > 0 and self.progress.total_steps > 0:
                time_per_step = self.progress.elapsed_seconds / self.progress.current_step
                remaining_steps = self.progress.total_steps - self.progress.current_step
                self.progress.estimated_remaining = int(time_per_step * remaining_steps)

        self._save_progress()

    def prepare_training_data(self) -> str:
        """
        Prepare training data in the format expected by mlx-lm.

        Returns:
            Path to prepared training data file
        """
        data_path = Path(self.config.data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")

        # mlx-lm expects JSONL with 'text' field or 'messages' for chat format
        # Our export format already has 'messages', so we just need to verify

        output_dir = Path(self.config.output_path) / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        train_file = output_dir / "train.jsonl"
        valid_file = output_dir / "valid.jsonl"

        # Read and split data
        with open(data_path, 'r') as f:
            examples = [json.loads(line) for line in f]

        # 90/10 train/valid split
        split_idx = int(len(examples) * 0.9)
        train_examples = examples[:split_idx]
        valid_examples = examples[split_idx:]

        # Write train file
        with open(train_file, 'w') as f:
            for ex in train_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')

        # Write valid file
        with open(valid_file, 'w') as f:
            for ex in valid_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')

        print(f"📊 Prepared {len(train_examples)} training, {len(valid_examples)} validation examples")

        return str(output_dir)

    def create_lora_config(self) -> str:
        """Create LoRA configuration file for mlx-lm (YAML format)"""
        # New mlx_lm format uses lora_parameters with rank, dropout, scale
        # scale = alpha / rank (default is 20.0 for rank 8)
        scale = self.config.lora_alpha / self.config.lora_rank

        config_file = Path(self.config.output_path) / "lora_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write as YAML format (mlx_lm expects YAML, not JSON)
        yaml_content = f"""# LoRA Configuration for Angela Training
lora_parameters:
  rank: {self.config.lora_rank}
  dropout: {self.config.lora_dropout}
  scale: {scale}
"""

        with open(config_file, 'w') as f:
            f.write(yaml_content)

        print(f"📝 Created LoRA config: {config_file}")
        return str(config_file)

    def train(self) -> TrainingProgress:
        """
        Run LoRA fine-tuning using mlx-lm.

        Returns:
            Final training progress
        """
        self.start_time = time.time()
        self._update_progress(status='initializing', total_epochs=self.config.epochs)

        try:
            # Prepare data
            print("📦 Preparing training data...")
            data_dir = self.prepare_training_data()

            # Create config
            print("⚙️ Creating LoRA configuration...")
            config_file = self.create_lora_config()

            # Build mlx-lm command
            output_path = Path(self.config.output_path) / "adapters"
            output_path.mkdir(parents=True, exist_ok=True)

            # New mlx_lm format (2024+):
            # - Use "mlx_lm lora" instead of "mlx_lm.lora"
            # - Use --num-layers instead of --lora-layers
            # - Use -c config for lora_parameters (rank, scale, dropout)
            # - Use --fine-tune-type lora
            # - Use --grad-checkpoint to reduce memory usage
            cmd = [
                sys.executable, "-m", "mlx_lm", "lora",
                "--model", self.config.model_name,
                "--train",
                "--data", data_dir,
                "--adapter-path", str(output_path),
                "--fine-tune-type", "lora",
                "--num-layers", "8",  # Fewer layers = less memory
                "--iters", str(self._calculate_total_iters()),
                "--batch-size", str(self.config.batch_size),
                "--learning-rate", str(self.config.learning_rate),
                "--save-every", str(self.config.save_every),
                "--test-batches", str(self.config.test_batches),
                "--seed", str(self.config.seed),
                "--grad-checkpoint",  # Reduce memory usage
                "-c", config_file,  # Pass LoRA config (rank, scale, dropout)
            ]

            print(f"🚀 Starting training...")
            print(f"   Command: {' '.join(cmd)}")
            self._update_progress(status='training')

            # Run training with output parsing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            total_iters = self._calculate_total_iters()
            current_iter = 0

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                print(line)  # Echo to console

                # Parse progress from mlx-lm output
                if "Iter" in line and "Loss" in line:
                    # Example: "Iter 100: Train loss 2.345, Val loss 2.567, It/s 12.34"
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
                                        total_steps=total_iters,
                                        current_loss=loss,
                                        recent_log=line[:100]
                                    )
                                except ValueError:
                                    pass
                    except Exception as e:
                        pass

                # Check for stop request
                if self._stop_requested:
                    process.terminate()
                    self._update_progress(status='stopped')
                    return self.progress

            process.wait()

            if process.returncode == 0:
                self._update_progress(
                    status='completed',
                    output_path=str(output_path),
                    current_step=total_iters,
                    recent_log="Training completed successfully!"
                )
                print(f"\n✅ Training completed!")
                print(f"   Adapters saved to: {output_path}")
            else:
                error_msg = f"Training failed with exit code {process.returncode}"
                self._update_progress(
                    status='failed',
                    error_message=error_msg
                )
                print(f"\n❌ {error_msg}")
                # IMPORTANT: Raise exception so Swift knows training failed
                raise RuntimeError(error_msg)

        except Exception as e:
            self._update_progress(
                status='failed',
                error_message=str(e)
            )
            print(f"\n❌ Training error: {e}")
            raise

        return self.progress

    def _calculate_total_iters(self) -> int:
        """Calculate total training iterations"""
        data_path = Path(self.config.data_path)
        with open(data_path, 'r') as f:
            num_examples = sum(1 for _ in f)

        # Split 90/10
        train_examples = int(num_examples * 0.9)
        iters_per_epoch = train_examples // self.config.batch_size
        total_iters = iters_per_epoch * self.config.epochs

        return max(total_iters, 100)  # Minimum 100 iterations

    def stop(self):
        """Request training stop"""
        self._stop_requested = True


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Train Angela LoRA model with MLX')
    parser.add_argument('--data', '-d', required=True,
                        help='Path to training data JSONL file')
    parser.add_argument('--model', '-m', default='Qwen/Qwen2.5-3B-Instruct',
                        help='Base model name (HuggingFace)')
    parser.add_argument('--output', '-o', default='./angela-lora',
                        help='Output directory for adapters')
    parser.add_argument('--epochs', '-e', type=int, default=3,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', '-b', type=int, default=4,
                        help='Training batch size')
    parser.add_argument('--learning-rate', '-lr', type=float, default=1e-4,
                        help='Learning rate')
    parser.add_argument('--lora-rank', '-r', type=int, default=16,
                        help='LoRA rank')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show configuration without training')

    args = parser.parse_args()

    config = TrainingConfig(
        data_path=args.data,
        model_name=args.model,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        lora_rank=args.lora_rank
    )

    print("🧠 Angela LoRA Trainer (MLX)")
    print("=" * 50)
    print(f"📁 Data: {config.data_path}")
    print(f"🤖 Model: {config.model_name}")
    print(f"📤 Output: {config.output_path}")
    print(f"🔄 Epochs: {config.epochs}")
    print(f"📦 Batch size: {config.batch_size}")
    print(f"📈 Learning rate: {config.learning_rate}")
    print(f"🎯 LoRA rank: {config.lora_rank}")
    print("=" * 50)

    if args.dry_run:
        print("\n🔍 Dry run - not training")
        trainer = MLXLoRATrainer(config)
        total_iters = trainer._calculate_total_iters()
        print(f"   Total iterations: {total_iters}")
        return

    trainer = MLXLoRATrainer(config)
    result = trainer.train()

    print("\n📊 Final Results:")
    print(f"   Status: {result.status}")
    print(f"   Total time: {result.elapsed_seconds}s")
    if result.output_path:
        print(f"   Output: {result.output_path}")


if __name__ == '__main__':
    main()
