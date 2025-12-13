"""
Angela Training Module

This module provides tools for training Angela's local model using LoRA.

Components:
- export_training_data.py: Export conversations for training
- mlx_lora_trainer.py: MLX-based LoRA training
- model_merger.py: Merge LoRA adapters with base model
- ollama_deployer.py: Deploy trained model to Ollama
"""

from .export_training_data import TrainingDataExporter

__all__ = ['TrainingDataExporter']

# Optional imports (may not be available yet)
try:
    from .mlx_lora_trainer import MLXLoRATrainer
    __all__.append('MLXLoRATrainer')
except ImportError:
    pass
