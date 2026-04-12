"""
Dataset Service — Upload, validate, preview, and analyze training datasets.
Supports JSONL, JSON, CSV, Parquet formats.
Dataset types: SFT, DPO, ORPO, Chat.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Required columns per dataset type
# ============================================================

REQUIRED_COLUMNS = {
    "sft": {
        "any_of": [
            ["instruction", "output"],       # Instruction-output pairs
            ["messages"],                     # Chat format
            ["prompt", "completion"],         # Simple format
            ["text"],                         # Pre-formatted text
        ],
    },
    "dpo": {
        "required": ["prompt", "chosen", "rejected"],
    },
    "orpo": {
        "required": ["prompt", "chosen", "rejected"],
    },
    "chat": {
        "required": ["messages"],
    },
}


# ============================================================
# Dataset Resolution
# ============================================================

async def _resolve_dataset(dataset_id: str) -> tuple[dict, Path]:
    """Resolve dataset_id to metadata + file path."""
    try:
        from services.db_service import list_datasets as db_list
        datasets = await db_list()
        for d in datasets:
            if str(d.get("id")) == dataset_id:
                path = Path(d["file_path"])
                if path.exists():
                    return d, path
                raise FileNotFoundError(f"Dataset file not found: {path}")
        raise FileNotFoundError(f"Dataset {dataset_id} not found in DB")
    except ImportError:
        raise FileNotFoundError("DB service unavailable")


def _read_dataset(path: Path, limit: int = None) -> list[dict]:
    """Read dataset file into list of dicts."""
    ext = path.suffix.lower()

    if ext == ".jsonl":
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    elif ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[:limit] if limit else data
        return [data]

    elif ext == ".csv":
        import csv
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                rows.append(dict(row))
        return rows

    elif ext == ".parquet":
        try:
            import pandas as pd
            df = pd.read_parquet(path)
            if limit:
                df = df.head(limit)
            return df.to_dict(orient="records")
        except ImportError:
            raise ValueError("pandas required for Parquet files — pip install pandas pyarrow")

    else:
        raise ValueError(f"Unsupported format: {ext}")


# ============================================================
# Validation
# ============================================================

async def validate_dataset(dataset_id: str) -> dict:
    """Validate a dataset for training readiness."""
    meta, path = await _resolve_dataset(dataset_id)
    dataset_type = meta.get("dataset_type", "sft")

    rows = _read_dataset(path)
    if not rows:
        return _validation_result(False, ["Dataset is empty"], dataset_type=dataset_type)

    errors = []
    warnings = []

    # Check columns
    columns = set()
    for row in rows:
        columns.update(row.keys())

    rules = REQUIRED_COLUMNS.get(dataset_type, {})
    if "required" in rules:
        missing = [c for c in rules["required"] if c not in columns]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
    elif "any_of" in rules:
        found = False
        for col_set in rules["any_of"]:
            if all(c in columns for c in col_set):
                found = True
                break
        if not found:
            options = " OR ".join([str(c) for c in rules["any_of"]])
            errors.append(f"Need one of: {options}")

    # Check for empty rows
    empty_count = sum(1 for r in rows if not any(r.values()))
    if empty_count > 0:
        warnings.append(f"{empty_count} empty rows found")

    # DPO/ORPO specific: check chosen != rejected
    if dataset_type in ("dpo", "orpo") and "chosen" in columns:
        same_count = sum(1 for r in rows if r.get("chosen") == r.get("rejected"))
        if same_count > len(rows) * 0.1:
            warnings.append(f"{same_count} rows have identical chosen/rejected")

    # Min rows check
    if len(rows) < 10:
        warnings.append(f"Only {len(rows)} examples — consider adding more for better results")
    if dataset_type in ("dpo", "orpo") and len(rows) < 20:
        errors.append(f"DPO/ORPO needs >= 20 preference pairs, got {len(rows)}")

    # Calculate stats
    stats = _compute_stats(rows, dataset_type)

    # Update DB
    is_valid = len(errors) == 0
    try:
        from services.db_service import update_dataset_validation
        await update_dataset_validation(
            dataset_id=dataset_id,
            total_examples=len(rows),
            avg_input_length=stats.get("avg_input_length", 0),
            avg_output_length=stats.get("avg_output_length", 0),
            is_validated=is_valid,
            validation_errors=errors + warnings,
            file_hash=_file_hash(path),
            status="ready" if is_valid else "error",
        )
    except Exception as e:
        logger.warning(f"Failed to update validation in DB: {e}")

    return _validation_result(
        is_valid, errors, warnings, len(rows), stats, dataset_type
    )


def _validation_result(is_valid: bool, errors: list = None, warnings: list = None,
                        total: int = 0, stats: dict = None, dataset_type: str = "sft") -> dict:
    return {
        "is_valid": is_valid,
        "errors": errors or [],
        "warnings": warnings or [],
        "total_examples": total,
        "dataset_type": dataset_type,
        "statistics": stats or {},
    }


# ============================================================
# Preview
# ============================================================

async def preview_dataset(dataset_id: str, limit: int = 10) -> dict:
    """Preview first N rows of a dataset."""
    meta, path = await _resolve_dataset(dataset_id)
    rows = _read_dataset(path, limit=limit)

    # Get total count
    total = 0
    ext = path.suffix.lower()
    if ext == ".jsonl":
        with open(path) as f:
            total = sum(1 for line in f if line.strip())
    elif ext == ".csv":
        with open(path) as f:
            total = sum(1 for _ in f) - 1
    elif ext == ".json":
        with open(path) as f:
            data = json.load(f)
            total = len(data) if isinstance(data, list) else 1
    elif ext == ".parquet":
        try:
            import pandas as pd
            total = len(pd.read_parquet(path))
        except ImportError:
            total = len(rows)

    columns = list(rows[0].keys()) if rows else []

    # Truncate long values for preview
    preview_rows = []
    for row in rows:
        preview = {}
        for k, v in row.items():
            if isinstance(v, str) and len(v) > 200:
                preview[k] = v[:200] + "..."
            elif isinstance(v, list) and len(str(v)) > 200:
                preview[k] = str(v)[:200] + "..."
            else:
                preview[k] = v
        preview_rows.append(preview)

    return {
        "columns": columns,
        "rows": preview_rows,
        "total_rows": total,
        "showing": len(preview_rows),
        "format": ext.lstrip("."),
        "dataset_type": meta.get("dataset_type", "sft"),
    }


# ============================================================
# Statistics
# ============================================================

async def get_statistics(dataset_id: str) -> dict:
    """Compute detailed statistics for a dataset."""
    meta, path = await _resolve_dataset(dataset_id)
    rows = _read_dataset(path)
    dataset_type = meta.get("dataset_type", "sft")

    stats = _compute_stats(rows, dataset_type)
    stats["total_examples"] = len(rows)
    stats["file_size_bytes"] = path.stat().st_size
    stats["format"] = path.suffix.lstrip(".")
    stats["dataset_type"] = dataset_type
    stats["columns"] = list(rows[0].keys()) if rows else []
    stats["file_hash"] = _file_hash(path)

    return stats


def _compute_stats(rows: list[dict], dataset_type: str) -> dict:
    """Compute input/output length statistics."""
    input_lengths = []
    output_lengths = []

    for row in rows:
        if dataset_type in ("dpo", "orpo"):
            prompt = row.get("prompt", "")
            if isinstance(prompt, list):
                prompt = json.dumps(prompt)
            input_lengths.append(len(str(prompt)))
            chosen = row.get("chosen", "")
            if isinstance(chosen, list):
                chosen = json.dumps(chosen)
            output_lengths.append(len(str(chosen)))
        elif "messages" in row:
            msgs = row["messages"]
            if isinstance(msgs, list):
                user_len = sum(len(m.get("content", "")) for m in msgs if m.get("role") == "user")
                asst_len = sum(len(m.get("content", "")) for m in msgs if m.get("role") == "assistant")
                input_lengths.append(user_len)
                output_lengths.append(asst_len)
        elif "instruction" in row:
            input_lengths.append(len(str(row.get("instruction", ""))))
            output_lengths.append(len(str(row.get("output", ""))))
        elif "text" in row:
            input_lengths.append(len(str(row.get("text", ""))))

    return {
        "avg_input_length": int(sum(input_lengths) / max(len(input_lengths), 1)),
        "avg_output_length": int(sum(output_lengths) / max(len(output_lengths), 1)),
        "max_input_length": max(input_lengths, default=0),
        "max_output_length": max(output_lengths, default=0),
        "min_input_length": min(input_lengths, default=0),
        "min_output_length": min(output_lengths, default=0),
    }


def _file_hash(path: Path) -> str:
    """Compute SHA-256 hash of file (first 1MB for speed)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(1024 * 1024))  # First 1MB
    return h.hexdigest()[:16]
