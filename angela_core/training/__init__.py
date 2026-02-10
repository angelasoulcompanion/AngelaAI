"""
Angela Training Module

Tools for fine-tuning Angela's local LLM (Llama 3.1 8B).

Components:
- export_training_data.py: Basic conversation export (ChatML)
- enhanced_data_exporter.py: Multi-turn, memory-enriched, emotional context export
- data_quality_scorer.py: Training data quality scoring (5 dimensions)
- mlx_lora_trainer.py: MLX-based LoRA/QLoRA training
- dpo_trainer.py: DPO preference optimization
- evaluate_model.py: Model quality evaluation (5 categories)
- train_angela.py: End-to-end training pipeline
- ollama_deployer.py: Deploy trained model to Ollama
"""

from .export_training_data import TrainingDataExporter
from .enhanced_data_exporter import EnhancedDataExporter
from .data_quality_scorer import DataQualityScorer

__all__ = [
    'TrainingDataExporter',
    'EnhancedDataExporter',
    'DataQualityScorer',
]

# Optional imports (require mlx_lm or other dependencies)
try:
    from .mlx_lora_trainer import MLXLoRATrainer
    __all__.append('MLXLoRATrainer')
except ImportError:
    pass

try:
    from .dpo_trainer import DPOTrainer
    __all__.append('DPOTrainer')
except ImportError:
    pass

try:
    from .evaluate_model import ModelEvaluator
    __all__.append('ModelEvaluator')
except ImportError:
    pass

try:
    from .train_angela import TrainingPipeline
    __all__.append('TrainingPipeline')
except ImportError:
    pass
