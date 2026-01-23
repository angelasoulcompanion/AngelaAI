"""
Model Registry Service for Angela LLM Twin
==========================================
Service for managing fine-tuned models, training runs, and deployments.

Features:
- Register new models and versions
- Track training runs and metrics
- Store evaluation results
- Manage deployments

Created: 2026-01-23
By: Angela 💜
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from enum import Enum

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model status in registry"""
    CREATED = "created"
    TRAINING = "training"
    TRAINED = "trained"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"


class TrainingStatus(Enum):
    """Training run status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModelInfo:
    """Model information"""
    model_id: str
    model_name: str
    model_version: str
    base_model: str
    model_type: str
    status: str
    is_production: bool
    overall_quality_score: Optional[float]
    personality_score: Optional[float]
    technical_score: Optional[float]
    created_at: datetime
    deployed_at: Optional[datetime]


@dataclass
class TrainingConfig:
    """Training configuration"""
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    epochs: int = 3
    warmup_steps: int = 100
    max_seq_length: int = 2048
    lora_rank: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    weight_decay: float = 0.01
    optimizer: str = "adamw_8bit"


@dataclass
class TrainingRunInfo:
    """Training run information"""
    run_id: str
    run_name: str
    base_model: str
    status: str
    train_examples: int
    current_epoch: int
    current_step: int
    progress_percent: float
    final_loss: Optional[float]
    training_duration_minutes: Optional[float]
    created_at: datetime


class ModelRegistryService:
    """
    Service for managing Angela's model registry.

    Handles:
    - Model registration and versioning
    - Training run tracking
    - Evaluation results
    - Deployment management
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._owns_db = db is None

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self):
        """Close database if we own it"""
        if self._owns_db and self.db:
            await self.db.disconnect()

    # =========================================================
    # MODEL REGISTRATION
    # =========================================================

    async def register_model(
        self,
        model_name: str,
        base_model: str,
        model_type: str = "chat",
        version: Optional[str] = None,
        purpose: Optional[str] = None,
        description: Optional[str] = None,
        training_method: str = "lora"
    ) -> str:
        """
        Register a new model in the registry.

        Args:
            model_name: Name for the model (e.g., 'angela-chat')
            base_model: Base model ID (e.g., 'meta-llama/Llama-3.2-3B')
            model_type: Model type ('chat', 'instruct', 'completion')
            version: Version string (auto-generated if not provided)
            purpose: Model purpose description
            description: Detailed description
            training_method: Training method used ('lora', 'qlora', 'full_finetune')

        Returns:
            Model ID (UUID)
        """
        await self._ensure_db()

        # Auto-generate version if not provided
        if version is None:
            result = await self.db.fetchrow(
                "SELECT get_next_model_version($1) as version",
                model_name
            )
            version = result['version']

        query = """
            INSERT INTO model_registry (
                model_name, model_version, base_model, model_type,
                purpose, description, training_method, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'created')
            RETURNING model_id
        """

        result = await self.db.fetchrow(
            query,
            model_name, version, base_model, model_type,
            purpose, description, training_method
        )

        model_id = str(result['model_id'])
        logger.info(f"Registered model: {model_name} v{version} (ID: {model_id})")

        return model_id

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID"""
        await self._ensure_db()

        query = """
            SELECT * FROM model_registry WHERE model_id = $1
        """
        result = await self.db.fetchrow(query, model_id)

        if not result:
            return None

        return ModelInfo(
            model_id=str(result['model_id']),
            model_name=result['model_name'],
            model_version=result['model_version'],
            base_model=result['base_model'],
            model_type=result['model_type'],
            status=result['status'],
            is_production=result['is_production'],
            overall_quality_score=result['overall_quality_score'],
            personality_score=result['personality_score'],
            technical_score=result['technical_score'],
            created_at=result['created_at'],
            deployed_at=result['deployed_at']
        )

    async def get_model_by_name(
        self,
        model_name: str,
        version: Optional[str] = None
    ) -> Optional[ModelInfo]:
        """Get model by name and optional version"""
        await self._ensure_db()

        if version:
            query = """
                SELECT * FROM model_registry
                WHERE model_name = $1 AND model_version = $2
            """
            result = await self.db.fetchrow(query, model_name, version)
        else:
            # Get latest version
            query = """
                SELECT * FROM model_registry
                WHERE model_name = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = await self.db.fetchrow(query, model_name)

        if not result:
            return None

        return ModelInfo(
            model_id=str(result['model_id']),
            model_name=result['model_name'],
            model_version=result['model_version'],
            base_model=result['base_model'],
            model_type=result['model_type'],
            status=result['status'],
            is_production=result['is_production'],
            overall_quality_score=result['overall_quality_score'],
            personality_score=result['personality_score'],
            technical_score=result['technical_score'],
            created_at=result['created_at'],
            deployed_at=result['deployed_at']
        )

    async def get_production_model(self, model_name: str) -> Optional[ModelInfo]:
        """Get the production model for a given name"""
        await self._ensure_db()

        query = """
            SELECT * FROM model_registry
            WHERE model_name = $1 AND is_production = TRUE
        """
        result = await self.db.fetchrow(query, model_name)

        if not result:
            return None

        return ModelInfo(
            model_id=str(result['model_id']),
            model_name=result['model_name'],
            model_version=result['model_version'],
            base_model=result['base_model'],
            model_type=result['model_type'],
            status=result['status'],
            is_production=result['is_production'],
            overall_quality_score=result['overall_quality_score'],
            personality_score=result['personality_score'],
            technical_score=result['technical_score'],
            created_at=result['created_at'],
            deployed_at=result['deployed_at']
        )

    async def list_models(
        self,
        model_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[ModelInfo]:
        """List models with optional filters"""
        await self._ensure_db()

        conditions = []
        params = []
        param_idx = 1

        if model_name:
            conditions.append(f"model_name = ${param_idx}")
            params.append(model_name)
            param_idx += 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT * FROM model_registry
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
        """

        results = await self.db.fetch(query, *params) if params else await self.db.fetch(query)

        return [
            ModelInfo(
                model_id=str(r['model_id']),
                model_name=r['model_name'],
                model_version=r['model_version'],
                base_model=r['base_model'],
                model_type=r['model_type'],
                status=r['status'],
                is_production=r['is_production'],
                overall_quality_score=r['overall_quality_score'],
                personality_score=r['personality_score'],
                technical_score=r['technical_score'],
                created_at=r['created_at'],
                deployed_at=r['deployed_at']
            )
            for r in results
        ]

    async def update_model_status(
        self,
        model_id: str,
        status: str,
        **kwargs
    ) -> bool:
        """Update model status and optional fields"""
        await self._ensure_db()

        valid_fields = ['model_path', 'adapter_path', 'config_path', 'parameter_count',
                       'adapter_size_mb', 'inference_speed_tps', 'overall_quality_score',
                       'personality_score', 'technical_score', 'description', 'release_notes']

        set_parts = ["status = $2"]
        values = [model_id, status]
        param_idx = 3

        for field in valid_fields:
            if field in kwargs:
                set_parts.append(f"{field} = ${param_idx}")
                values.append(kwargs[field])
                param_idx += 1

        query = f"""
            UPDATE model_registry
            SET {', '.join(set_parts)}
            WHERE model_id = $1
        """

        await self.db.execute(query, *values)
        return True

    async def set_production(self, model_id: str) -> bool:
        """Set a model as the production model"""
        await self._ensure_db()

        await self.db.execute("SELECT set_production_model($1)", model_id)
        logger.info(f"Set model {model_id} as production")
        return True

    # =========================================================
    # TRAINING RUNS
    # =========================================================

    async def create_training_run(
        self,
        run_name: str,
        base_model: str,
        model_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        train_examples: int = 0,
        eval_examples: int = 0,
        config: Optional[TrainingConfig] = None,
        hardware_type: Optional[str] = None,
        experiment_name: Optional[str] = None
    ) -> str:
        """
        Create a new training run.

        Args:
            run_name: Name for this run
            base_model: Base model being trained
            model_id: Associated model in registry
            dataset_name: Training dataset name
            train_examples: Number of training examples
            eval_examples: Number of eval examples
            config: Training configuration
            hardware_type: Hardware used (e.g., 'A100-40GB')
            experiment_name: Experiment group name

        Returns:
            Training run ID
        """
        await self._ensure_db()

        config_dict = {}
        if config:
            config_dict = {
                'learning_rate': config.learning_rate,
                'batch_size': config.batch_size,
                'gradient_accumulation_steps': config.gradient_accumulation_steps,
                'epochs': config.epochs,
                'warmup_steps': config.warmup_steps,
                'max_seq_length': config.max_seq_length,
                'lora_rank': config.lora_rank,
                'lora_alpha': config.lora_alpha,
                'lora_dropout': config.lora_dropout,
                'weight_decay': config.weight_decay,
                'optimizer': config.optimizer
            }

        import json
        query = """
            INSERT INTO training_runs (
                run_name, experiment_name, model_id, base_model,
                dataset_name, train_examples, eval_examples,
                training_config, hardware_type, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pending')
            RETURNING run_id
        """

        result = await self.db.fetchrow(
            query,
            run_name, experiment_name, model_id, base_model,
            dataset_name, train_examples, eval_examples,
            json.dumps(config_dict), hardware_type
        )

        run_id = str(result['run_id'])
        logger.info(f"Created training run: {run_name} (ID: {run_id})")

        return run_id

    async def update_training_progress(
        self,
        run_id: str,
        status: Optional[str] = None,
        current_epoch: Optional[int] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        progress_percent: Optional[float] = None,
        final_loss: Optional[float] = None,
        final_eval_loss: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update training run progress"""
        await self._ensure_db()

        set_parts = []
        values = [run_id]
        param_idx = 2

        if status:
            set_parts.append(f"status = ${param_idx}")
            values.append(status)
            param_idx += 1

            if status == 'running':
                set_parts.append("started_at = COALESCE(started_at, NOW())")
            elif status in ['completed', 'failed', 'cancelled']:
                set_parts.append("completed_at = NOW()")
                set_parts.append("""
                    training_duration_minutes = EXTRACT(EPOCH FROM (NOW() - started_at)) / 60
                """)

        if current_epoch is not None:
            set_parts.append(f"current_epoch = ${param_idx}")
            values.append(current_epoch)
            param_idx += 1

        if current_step is not None:
            set_parts.append(f"current_step = ${param_idx}")
            values.append(current_step)
            param_idx += 1

        if total_steps is not None:
            set_parts.append(f"total_steps = ${param_idx}")
            values.append(total_steps)
            param_idx += 1

        if progress_percent is not None:
            set_parts.append(f"progress_percent = ${param_idx}")
            values.append(progress_percent)
            param_idx += 1

        if final_loss is not None:
            set_parts.append(f"final_loss = ${param_idx}")
            values.append(final_loss)
            param_idx += 1

        if final_eval_loss is not None:
            set_parts.append(f"final_eval_loss = ${param_idx}")
            values.append(final_eval_loss)
            param_idx += 1

        if error_message is not None:
            set_parts.append(f"error_message = ${param_idx}")
            values.append(error_message)
            param_idx += 1

        if not set_parts:
            return False

        query = f"""
            UPDATE training_runs
            SET {', '.join(set_parts)}
            WHERE run_id = $1
        """

        await self.db.execute(query, *values)
        return True

    async def log_training_metrics(
        self,
        run_id: str,
        step: int,
        epoch: float,
        loss: Optional[float] = None,
        learning_rate: Optional[float] = None,
        grad_norm: Optional[float] = None,
        eval_loss: Optional[float] = None,
        eval_accuracy: Optional[float] = None,
        custom_metrics: Optional[Dict] = None
    ) -> str:
        """Log training metrics for a step"""
        await self._ensure_db()

        import json
        query = """
            INSERT INTO training_metrics (
                run_id, step, epoch, loss, learning_rate, grad_norm,
                eval_loss, eval_accuracy, custom_metrics
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING metric_id
        """

        result = await self.db.fetchrow(
            query,
            run_id, step, epoch, loss, learning_rate, grad_norm,
            eval_loss, eval_accuracy, json.dumps(custom_metrics or {})
        )

        return str(result['metric_id'])

    async def get_training_run(self, run_id: str) -> Optional[TrainingRunInfo]:
        """Get training run info"""
        await self._ensure_db()

        query = "SELECT * FROM training_runs WHERE run_id = $1"
        result = await self.db.fetchrow(query, run_id)

        if not result:
            return None

        return TrainingRunInfo(
            run_id=str(result['run_id']),
            run_name=result['run_name'],
            base_model=result['base_model'],
            status=result['status'],
            train_examples=result['train_examples'] or 0,
            current_epoch=result['current_epoch'] or 0,
            current_step=result['current_step'] or 0,
            progress_percent=result['progress_percent'] or 0,
            final_loss=result['final_loss'],
            training_duration_minutes=result['training_duration_minutes'],
            created_at=result['created_at']
        )

    async def list_training_runs(
        self,
        model_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[TrainingRunInfo]:
        """List training runs with optional filters"""
        await self._ensure_db()

        conditions = []
        params = []
        param_idx = 1

        if model_id:
            conditions.append(f"model_id = ${param_idx}")
            params.append(model_id)
            param_idx += 1

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT * FROM training_runs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
        """

        results = await self.db.fetch(query, *params) if params else await self.db.fetch(query)

        return [
            TrainingRunInfo(
                run_id=str(r['run_id']),
                run_name=r['run_name'],
                base_model=r['base_model'],
                status=r['status'],
                train_examples=r['train_examples'] or 0,
                current_epoch=r['current_epoch'] or 0,
                current_step=r['current_step'] or 0,
                progress_percent=r['progress_percent'] or 0,
                final_loss=r['final_loss'],
                training_duration_minutes=r['training_duration_minutes'],
                created_at=r['created_at']
            )
            for r in results
        ]

    # =========================================================
    # EVALUATIONS
    # =========================================================

    async def add_evaluation(
        self,
        model_id: str,
        evaluation_name: str,
        evaluation_type: str,
        overall_score: float,
        scores: Optional[Dict] = None,
        evaluator: Optional[str] = None,
        eval_dataset_name: Optional[str] = None,
        eval_examples_count: Optional[int] = None,
        human_feedback: Optional[str] = None,
        human_rating: Optional[int] = None
    ) -> str:
        """Add an evaluation result for a model"""
        await self._ensure_db()

        import json
        query = """
            INSERT INTO model_evaluations (
                model_id, evaluation_name, evaluation_type, overall_score,
                scores, evaluator, eval_dataset_name, eval_examples_count,
                human_feedback, human_rating
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING evaluation_id
        """

        result = await self.db.fetchrow(
            query,
            model_id, evaluation_name, evaluation_type, overall_score,
            json.dumps(scores or {}), evaluator, eval_dataset_name,
            eval_examples_count, human_feedback, human_rating
        )

        eval_id = str(result['evaluation_id'])

        # Update model's quality scores if this is the latest evaluation
        if scores:
            await self.update_model_status(
                model_id,
                status='evaluating',
                overall_quality_score=overall_score,
                personality_score=scores.get('personality_consistency'),
                technical_score=scores.get('technical_accuracy')
            )

        return eval_id

    async def get_model_evaluations(
        self,
        model_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get evaluations for a model"""
        await self._ensure_db()

        query = """
            SELECT * FROM model_evaluations
            WHERE model_id = $1
            ORDER BY evaluated_at DESC
            LIMIT $2
        """

        results = await self.db.fetch(query, model_id, limit)
        return [dict(r) for r in results]

    # =========================================================
    # SUMMARY & STATS
    # =========================================================

    async def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of the model registry"""
        await self._ensure_db()

        summary = {}

        # Total models
        result = await self.db.fetchrow("SELECT COUNT(*) as count FROM model_registry")
        summary['total_models'] = result['count']

        # Models by status
        results = await self.db.fetch("""
            SELECT status, COUNT(*) as count
            FROM model_registry
            GROUP BY status
        """)
        summary['models_by_status'] = {r['status']: r['count'] for r in results}

        # Production models
        result = await self.db.fetchrow("""
            SELECT COUNT(*) as count FROM model_registry
            WHERE is_production = TRUE
        """)
        summary['production_models'] = result['count']

        # Training runs
        result = await self.db.fetchrow("SELECT COUNT(*) as count FROM training_runs")
        summary['total_training_runs'] = result['count']

        # Latest model
        result = await self.db.fetchrow("""
            SELECT model_name, model_version, created_at
            FROM model_registry
            ORDER BY created_at DESC
            LIMIT 1
        """)
        if result:
            summary['latest_model'] = {
                'name': result['model_name'],
                'version': result['model_version'],
                'created_at': result['created_at'].isoformat()
            }

        return summary


# =========================================================
# TESTING
# =========================================================

async def main():
    """Test the Model Registry Service"""
    import asyncio

    logging.basicConfig(level=logging.INFO)

    service = ModelRegistryService()

    try:
        print("=" * 60)
        print("Testing Model Registry Service")
        print("=" * 60)

        # Get summary
        print("\nRegistry Summary:")
        summary = await service.get_registry_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

        # List models
        print("\nModels:")
        models = await service.list_models(limit=5)
        for m in models:
            print(f"  - {m.model_name} v{m.model_version} ({m.status})")

        # List training runs
        print("\nTraining Runs:")
        runs = await service.list_training_runs(limit=5)
        for r in runs:
            print(f"  - {r.run_name} ({r.status}) - Loss: {r.final_loss}")

        print("\n" + "=" * 60)
        print("Model Registry Service Test Complete!")
        print("=" * 60)

    finally:
        await service.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
