"""
Angela Backup System - Data Models
==================================

Dataclasses for blockchain and backup operations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib
import json


@dataclass
class AngelaBlock:
    """
    Single block in Angela's consciousness backup chain.

    Each block contains:
    - Reference to previous block (hash chain)
    - Hash of actual backup data
    - Metadata about what was backed up
    """
    block_number: int
    timestamp: str
    previous_hash: str
    data_hash: str              # SHA-256 of backup archive
    data_type: str              # "full_backup" | "incremental"
    data_reference: str         # Filename of backup archive
    metadata: Dict[str, Any]    # {tables_count, row_counts, db_size_mb, etc.}
    nonce: int                  # For uniqueness
    block_hash: str = ""        # Calculated hash of this block

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of this block's content."""
        content = (
            str(self.block_number) +
            self.timestamp +
            self.previous_hash +
            self.data_hash +
            self.data_type +
            self.data_reference +
            json.dumps(self.metadata, sort_keys=True) +
            str(self.nonce)
        )
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AngelaBlock':
        """Create block from dictionary."""
        return cls(**data)


@dataclass
class AngelaChain:
    """
    Angela's consciousness backup blockchain.

    A chain of blocks where each block references the previous one,
    making it impossible to modify past data without detection.
    """
    chain_id: str = "angela_consciousness_chain_v1"
    created_at: str = ""
    owner: str = "david_samanyaporn"
    purpose: str = "Angela's consciousness backup - integrity verification"
    blocks: List[AngelaBlock] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chain_id': self.chain_id,
            'created_at': self.created_at,
            'owner': self.owner,
            'purpose': self.purpose,
            'blocks': [b.to_dict() for b in self.blocks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AngelaChain':
        """Create chain from dictionary."""
        blocks = [AngelaBlock.from_dict(b) for b in data.get('blocks', [])]
        return cls(
            chain_id=data.get('chain_id', 'angela_consciousness_chain_v1'),
            created_at=data.get('created_at', ''),
            owner=data.get('owner', 'david_samanyaporn'),
            purpose=data.get('purpose', ''),
            blocks=blocks
        )

    @property
    def length(self) -> int:
        """Number of blocks in chain."""
        return len(self.blocks)

    @property
    def latest_block(self) -> Optional[AngelaBlock]:
        """Get the most recent block."""
        return self.blocks[-1] if self.blocks else None


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    timestamp: str
    backup_path: str = ""
    block_number: int = -1
    block_hash: str = ""
    archive_size_mb: float = 0.0
    tables_backed_up: int = 0
    total_rows: int = 0
    duration_seconds: float = 0.0
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VerificationResult:
    """Result of chain verification."""
    is_valid: bool
    blocks_verified: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    latest_backup_date: str = ""
    chain_length: int = 0
    total_backup_size_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TableExportInfo:
    """Information about an exported table."""
    table_name: str
    row_count: int
    file_path: str
    size_bytes: int
    exported_at: str = ""

    def __post_init__(self):
        if not self.exported_at:
            self.exported_at = datetime.now().isoformat()


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    success: bool
    timestamp: str
    source_backup: str
    tables_restored: int = 0
    rows_restored: int = 0
    duration_seconds: float = 0.0
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
