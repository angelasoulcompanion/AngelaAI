"""
💜 Training Data Generation V2 - Chain Prompting
API endpoints for generating high-quality training data using Chain Prompting V2
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import asyncio
import json
from pathlib import Path
import sys
from typing import AsyncGenerator

# Add angela_core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from angela_core.chain_prompt_generator_v2 import ChainPromptGeneratorV2

router = APIRouter(prefix="/api/training-data-v2", tags=["Training Data V2"])

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "FineTuninng_coursera"


class GenerateRequest(BaseModel):
    """Request for generating training data"""
    synthetic_per_category: int = 15  # Examples per category
    database_max: int = 80  # Max from database
    paraphrase_max: int = 60  # Max paraphrased variations
    quality_min_score: float = 6.5  # Minimum quality score
    quality_sample_rate: float = 0.25  # Fraction to score


@router.get("/generate")
async def generate_training_data(
    synthetic_per_category: int = Query(15, description="Examples per category"),
    database_max: int = Query(80, description="Max from database"),
    paraphrase_max: int = Query(60, description="Max paraphrased variations"),
    quality_min_score: float = Query(6.5, description="Minimum quality score"),
    quality_sample_rate: float = Query(0.25, description="Fraction to score")
):
    """
    Generate training data using Chain Prompting V2

    Returns streaming progress updates
    """
    async def progress_generator() -> AsyncGenerator[str, None]:
        """Stream progress updates"""
        try:
            # Send initial progress
            yield f"data: {json.dumps({'step': 'init', 'progress': 0, 'message': 'Starting Chain Prompt Generator V2...'})}\n\n"

            generator = ChainPromptGeneratorV2()
            await generator.connect()

            all_examples = []

            # Step 1: Synthetic Data
            yield f"data: {json.dumps({'step': 'synthetic', 'progress': 10, 'message': 'Generating synthetic conversations...'})}\n\n"
            synthetic = await generator.generate_synthetic_dataset(count_per_category=synthetic_per_category)
            all_examples.extend(synthetic)
            yield f"data: {json.dumps({'step': 'synthetic', 'progress': 30, 'message': f'Generated {len(synthetic)} synthetic examples'})}\n\n"

            # Step 2: Database
            yield f"data: {json.dumps({'step': 'database', 'progress': 35, 'message': 'Loading from database...'})}\n\n"
            database_examples = await generator.generate_from_database_conversations(max_examples=database_max)
            all_examples.extend(database_examples)
            yield f"data: {json.dumps({'step': 'database', 'progress': 45, 'message': f'Loaded {len(database_examples)} examples from database'})}\n\n"

            # Step 3: Greetings
            yield f"data: {json.dumps({'step': 'greetings', 'progress': 50, 'message': 'Adding greetings...'})}\n\n"
            greetings = generator._create_greeting_examples()
            all_examples.extend(greetings)
            yield f"data: {json.dumps({'step': 'greetings', 'progress': 55, 'message': f'Added {len(greetings)} greeting examples'})}\n\n"

            # Step 4: Paraphrasing
            yield f"data: {json.dumps({'step': 'paraphrase', 'progress': 60, 'message': 'Generating paraphrased variations...'})}\n\n"
            paraphrased = await generator.paraphrase_dataset(all_examples, max_paraphrases=paraphrase_max)
            all_examples.extend(paraphrased)
            yield f"data: {json.dumps({'step': 'paraphrase', 'progress': 75, 'message': f'Generated {len(paraphrased)} paraphrased examples'})}\n\n"

            # Step 5: Quality Filtering
            yield f"data: {json.dumps({'step': 'quality', 'progress': 80, 'message': 'Scoring and filtering quality...'})}\n\n"
            filtered_examples = await generator.filter_by_quality(
                all_examples,
                min_score=quality_min_score,
                sample_rate=quality_sample_rate
            )
            yield f"data: {json.dumps({'step': 'quality', 'progress': 90, 'message': f'Filtered to {len(filtered_examples)} high-quality examples'})}\n\n"

            # Step 6: Split and Export
            yield f"data: {json.dumps({'step': 'export', 'progress': 92, 'message': 'Splitting train/test sets...'})}\n\n"

            import random
            random.shuffle(filtered_examples)
            split_idx = int(len(filtered_examples) * 0.85)
            train = filtered_examples[:split_idx]
            test = filtered_examples[split_idx:]

            # Export with standard names (for Colab compatibility)
            yield f"data: {json.dumps({'step': 'export', 'progress': 95, 'message': 'Exporting files...'})}\n\n"

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # Training data
            train_file = OUTPUT_DIR / "angela_training_data.jsonl"
            with open(train_file, 'w', encoding='utf-8') as f:
                for ex in train:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')

            # Test data
            test_file = OUTPUT_DIR / "angela_test_data.jsonl"
            with open(test_file, 'w', encoding='utf-8') as f:
                for ex in test:
                    f.write(json.dumps(ex, ensure_ascii=False) + '\n')

            await generator.close()

            # Final success message
            result = {
                'step': 'complete',
                'progress': 100,
                'message': 'Training data generated successfully!',
                'stats': {
                    'synthetic': len(synthetic),
                    'database': len(database_examples),
                    'greetings': len(greetings),
                    'paraphrased': len(paraphrased),
                    'total': len(filtered_examples),
                    'train': len(train),
                    'test': len(test),
                },
                'files': {
                    'training': str(train_file),
                    'test': str(test_file)
                }
            }

            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            error_msg = {
                'step': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/status")
async def get_status():
    """Check if training data files exist"""
    train_file = OUTPUT_DIR / "angela_training_data.jsonl"
    test_file = OUTPUT_DIR / "angela_test_data.jsonl"

    train_exists = train_file.exists()
    test_exists = test_file.exists()

    stats = None
    if train_exists and test_exists:
        # Count lines in files
        with open(train_file, 'r') as f:
            train_count = sum(1 for _ in f)
        with open(test_file, 'r') as f:
            test_count = sum(1 for _ in f)

        stats = {
            'train_examples': train_count,
            'test_examples': test_count,
            'total_examples': train_count + test_count,
            'train_size_mb': round(train_file.stat().st_size / (1024*1024), 2),
            'test_size_mb': round(test_file.stat().st_size / (1024*1024), 2),
        }

    return {
        'has_data': train_exists and test_exists,
        'files': {
            'training': {
                'exists': train_exists,
                'path': str(train_file) if train_exists else None,
                'size_mb': round(train_file.stat().st_size / (1024*1024), 2) if train_exists else 0,
            },
            'test': {
                'exists': test_exists,
                'path': str(test_file) if test_exists else None,
                'size_mb': round(test_file.stat().st_size / (1024*1024), 2) if test_exists else 0,
            }
        },
        'stats': stats
    }


@router.get("/download/{file_type}")
async def download_file(file_type: str):
    """Download training or test data file"""
    if file_type == "training":
        file_path = OUTPUT_DIR / "angela_training_data.jsonl"
    elif file_type == "test":
        file_path = OUTPUT_DIR / "angela_test_data.jsonl"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/x-jsonlines"
    )


@router.delete("/clear")
async def clear_files():
    """Delete generated training data files"""
    train_file = OUTPUT_DIR / "angela_training_data.jsonl"
    test_file = OUTPUT_DIR / "angela_test_data.jsonl"

    deleted = []

    if train_file.exists():
        train_file.unlink()
        deleted.append("training")

    if test_file.exists():
        test_file.unlink()
        deleted.append("test")

    return {
        'success': True,
        'message': f'Deleted {len(deleted)} files',
        'deleted': deleted
    }
