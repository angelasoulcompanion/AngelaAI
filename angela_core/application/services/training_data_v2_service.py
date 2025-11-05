#!/usr/bin/env python3
"""
💜 Training Data Service V2 - Chain Prompting
Application service for generating high-quality training data using Chain Prompting V2.

Handles:
- Synthetic data generation across categories
- Database conversation extraction
- Greeting examples generation
- Paraphrasing for diversity
- Quality scoring and filtering
- Train/test splitting and export

✅ [Batch-26]: Clean Architecture with DI
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, AsyncGenerator, Optional
import logging

from angela_core.application.services.base_service import BaseService
from angela_core.chain_prompt_generator_v2 import ChainPromptGeneratorV2

logger = logging.getLogger(__name__)


class TrainingDataV2Service(BaseService):
    """
    Service for training data generation using Chain Prompting V2.

    Orchestrates complex multi-step training data generation:
    1. Synthetic conversation generation
    2. Database conversation extraction
    3. Greeting examples
    4. Paraphrased variations
    5. Quality filtering
    6. Train/test splitting
    """

    def __init__(self):
        """Initialize TrainingDataV2Service."""
        super().__init__()

        # Output directory
        self.output_dir = Path(__file__).parent.parent.parent.parent / "FineTuninng_coursera"

        # File paths
        self.train_file = self.output_dir / "angela_training_data.jsonl"
        self.test_file = self.output_dir / "angela_test_data.jsonl"

        # Generator instance (will be created on demand)
        self.generator: Optional[ChainPromptGeneratorV2] = None

        logger.info(f"✅ TrainingDataV2Service initialized (output_dir: {self.output_dir})")

    def get_service_name(self) -> str:
        """Get service name for logging."""
        return "TrainingDataV2Service"

    async def _ensure_generator(self):
        """Ensure generator is initialized and connected."""
        if self.generator is None:
            self.generator = ChainPromptGeneratorV2()
            await self.generator.connect()
            logger.info("✅ ChainPromptGeneratorV2 connected")

    async def _close_generator(self):
        """Close generator connection if open."""
        if self.generator is not None:
            await self.generator.close()
            self.generator = None
            logger.info("✅ ChainPromptGeneratorV2 closed")

    async def generate_training_data(
        self,
        synthetic_per_category: int = 15,
        database_max: int = 80,
        paraphrase_max: int = 60,
        quality_min_score: float = 6.5,
        quality_sample_rate: float = 0.25
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate training data using Chain Prompting V2 (streaming progress).

        This is a complex multi-step process that generates high-quality training data
        from multiple sources and applies quality filtering.

        Args:
            synthetic_per_category: Examples to generate per category
            database_max: Maximum examples from database
            paraphrase_max: Maximum paraphrased variations
            quality_min_score: Minimum quality score (0-10)
            quality_sample_rate: Fraction of examples to score (0-1)

        Yields:
            Progress updates as dicts with:
            - step: current step name
            - progress: percentage (0-100)
            - message: status message
            - stats: final statistics (only in 'complete' step)
            - files: file paths (only in 'complete' step)

        Raises:
            Exception: If generation fails at any step
        """
        operation_name = "generate_training_data"
        await self._log_operation_start(
            operation_name,
            synthetic_per_category=synthetic_per_category,
            database_max=database_max,
            paraphrase_max=paraphrase_max
        )

        try:
            # Initialize
            yield {
                "step": "init",
                "progress": 0,
                "message": "Starting Chain Prompt Generator V2..."
            }

            await self._ensure_generator()
            all_examples = []

            # Step 1: Synthetic Data (10-30%)
            yield {
                "step": "synthetic",
                "progress": 10,
                "message": "Generating synthetic conversations..."
            }

            synthetic = await self.generator.generate_synthetic_dataset(
                count_per_category=synthetic_per_category
            )
            all_examples.extend(synthetic)

            logger.info(f"📊 Generated {len(synthetic)} synthetic examples")

            yield {
                "step": "synthetic",
                "progress": 30,
                "message": f"Generated {len(synthetic)} synthetic examples"
            }

            # Step 2: Database (35-45%)
            yield {
                "step": "database",
                "progress": 35,
                "message": "Loading from database..."
            }

            database_examples = await self.generator.generate_from_database_conversations(
                max_examples=database_max
            )
            all_examples.extend(database_examples)

            logger.info(f"📊 Loaded {len(database_examples)} examples from database")

            yield {
                "step": "database",
                "progress": 45,
                "message": f"Loaded {len(database_examples)} examples from database"
            }

            # Step 3: Greetings (50-55%)
            yield {
                "step": "greetings",
                "progress": 50,
                "message": "Adding greetings..."
            }

            greetings = self.generator._create_greeting_examples()
            all_examples.extend(greetings)

            logger.info(f"📊 Added {len(greetings)} greeting examples")

            yield {
                "step": "greetings",
                "progress": 55,
                "message": f"Added {len(greetings)} greeting examples"
            }

            # Step 4: Paraphrasing (60-75%)
            yield {
                "step": "paraphrase",
                "progress": 60,
                "message": "Generating paraphrased variations..."
            }

            paraphrased = await self.generator.paraphrase_dataset(
                all_examples,
                max_paraphrases=paraphrase_max
            )
            all_examples.extend(paraphrased)

            logger.info(f"📊 Generated {len(paraphrased)} paraphrased examples")

            yield {
                "step": "paraphrase",
                "progress": 75,
                "message": f"Generated {len(paraphrased)} paraphrased examples"
            }

            # Step 5: Quality Filtering (80-90%)
            yield {
                "step": "quality",
                "progress": 80,
                "message": "Scoring and filtering quality..."
            }

            filtered_examples = await self.generator.filter_by_quality(
                all_examples,
                min_score=quality_min_score,
                sample_rate=quality_sample_rate
            )

            logger.info(f"📊 Filtered to {len(filtered_examples)} high-quality examples")

            yield {
                "step": "quality",
                "progress": 90,
                "message": f"Filtered to {len(filtered_examples)} high-quality examples"
            }

            # Step 6: Split and Export (92-100%)
            yield {
                "step": "export",
                "progress": 92,
                "message": "Splitting train/test sets..."
            }

            # Shuffle and split
            random.shuffle(filtered_examples)
            split_idx = int(len(filtered_examples) * 0.85)
            train = filtered_examples[:split_idx]
            test = filtered_examples[split_idx:]

            logger.info(f"📊 Split into {len(train)} train / {len(test)} test")

            yield {
                "step": "export",
                "progress": 95,
                "message": "Exporting files..."
            }

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Write training data
            with open(self.train_file, 'w', encoding='utf-8') as f:
                for ex in train:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')

            # Write test data
            with open(self.test_file, 'w', encoding='utf-8') as f:
                for ex in test:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')

            logger.info(f"✅ Exported to {self.train_file} and {self.test_file}")

            # Close generator
            await self._close_generator()

            # Final success message
            result = {
                "step": "complete",
                "progress": 100,
                "message": "Training data generated successfully!",
                "stats": {
                    "synthetic": len(synthetic),
                    "database": len(database_examples),
                    "greetings": len(greetings),
                    "paraphrased": len(paraphrased),
                    "total": len(filtered_examples),
                    "train": len(train),
                    "test": len(test),
                },
                "files": {
                    "training": str(self.train_file),
                    "test": str(self.test_file)
                }
            }

            await self._log_operation_success(
                operation_name,
                total_examples=len(filtered_examples),
                train_count=len(train),
                test_count=len(test)
            )

            yield result

        except Exception as e:
            logger.error(f"❌ Generation failed: {str(e)}")
            await self._log_operation_error(operation_name, e)

            # Ensure generator is closed
            await self._close_generator()

            # Yield error message
            yield {
                "step": "error",
                "progress": 0,
                "message": f"Error: {str(e)}"
            }

            raise

    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of training data files.

        Returns:
            Dict with:
            - has_data: bool
            - files: dict (training and test file metadata)
            - stats: dict (statistics if available)
        """
        operation_name = "get_status"
        await self._log_operation_start(operation_name)

        try:
            train_exists = self.train_file.exists()
            test_exists = self.test_file.exists()

            stats = None
            if train_exists and test_exists:
                # Count lines
                with open(self.train_file, 'r') as f:
                    train_count = sum(1 for _ in f)
                with open(self.test_file, 'r') as f:
                    test_count = sum(1 for _ in f)

                stats = {
                    "train_examples": train_count,
                    "test_examples": test_count,
                    "total_examples": train_count + test_count,
                    "train_size_mb": round(self.train_file.stat().st_size / (1024 * 1024), 2),
                    "test_size_mb": round(self.test_file.stat().st_size / (1024 * 1024), 2),
                }

            result = {
                "has_data": train_exists and test_exists,
                "files": {
                    "training": {
                        "exists": train_exists,
                        "path": str(self.train_file) if train_exists else None,
                        "size_mb": round(self.train_file.stat().st_size / (1024 * 1024), 2) if train_exists else 0,
                    },
                    "test": {
                        "exists": test_exists,
                        "path": str(self.test_file) if test_exists else None,
                        "size_mb": round(self.test_file.stat().st_size / (1024 * 1024), 2) if test_exists else 0,
                    }
                },
                "stats": stats
            }

            await self._log_operation_success(operation_name, has_data=result["has_data"])

            return result

        except Exception as e:
            logger.error(f"❌ Failed to get status: {str(e)}")
            await self._log_operation_error(operation_name, e)
            raise

    async def get_file_path(self, file_type: str) -> Optional[Path]:
        """
        Get file path for training or test data.

        Args:
            file_type: 'training' or 'test'

        Returns:
            Path if file exists, None otherwise

        Raises:
            ValueError: If file_type is invalid
        """
        if file_type == "training":
            file_path = self.train_file
        elif file_type == "test":
            file_path = self.test_file
        else:
            raise ValueError(f"Invalid file type '{file_type}'. Must be 'training' or 'test'")

        if not file_path.exists():
            return None

        return file_path

    async def clear_files(self) -> Dict[str, Any]:
        """
        Delete generated training data files.

        Returns:
            Dict with:
            - success: bool
            - message: str
            - deleted: list
        """
        operation_name = "clear_files"
        await self._log_operation_start(operation_name)

        try:
            deleted = []

            if self.train_file.exists():
                self.train_file.unlink()
                deleted.append("training")
                logger.info(f"🗑️ Deleted: {self.train_file.name}")

            if self.test_file.exists():
                self.test_file.unlink()
                deleted.append("test")
                logger.info(f"🗑️ Deleted: {self.test_file.name}")

            result = {
                "success": True,
                "message": f"Deleted {len(deleted)} files",
                "deleted": deleted
            }

            await self._log_operation_success(operation_name, files_deleted=len(deleted))

            return result

        except Exception as e:
            logger.error(f"❌ Failed to clear files: {str(e)}")
            await self._log_operation_error(operation_name, e)
            raise
