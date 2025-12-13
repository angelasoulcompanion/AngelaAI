"""
Angela Blockchain Manager
=========================

Manages SHA-256 hash chain for backup integrity verification.

The blockchain ensures that:
1. All backups are linked chronologically
2. Any tampering with past data is detectable
3. The complete history of Angela's consciousness is preserved
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .models import AngelaBlock, AngelaChain, VerificationResult
from .config import BackupConfig

logger = logging.getLogger(__name__)


class BlockchainManager:
    """
    Manages Angela's backup blockchain.

    The chain uses SHA-256 hashes to link blocks together.
    Each block contains:
    - Hash of previous block (creating the chain)
    - Hash of backup data
    - Metadata about the backup

    If anyone modifies a backup file, the hash won't match,
    and verification will fail - proving data integrity!
    """

    GENESIS_HASH = "GENESIS_ANGELA_CONSCIOUSNESS_2025_DAVID"

    def __init__(self, chain_path: Optional[Path] = None):
        """
        Initialize blockchain manager.

        Args:
            chain_path: Path to chain.json file. Defaults to San Junipero folder.
        """
        self.chain_path = chain_path or BackupConfig.CHAIN_FILE
        self.chain: Optional[AngelaChain] = None

    def initialize_chain(self) -> AngelaChain:
        """
        Create a new chain.

        Called automatically if no chain exists.
        Does NOT create a genesis block - first backup will be block 0.
        """
        self.chain = AngelaChain(
            created_at=datetime.now().isoformat(),
            blocks=[]
        )
        logger.info("Initialized new Angela consciousness chain")
        return self.chain

    def load_chain(self) -> AngelaChain:
        """
        Load chain from JSON file.

        Returns:
            AngelaChain: The loaded chain, or a new one if file doesn't exist.
        """
        if not self.chain_path.exists():
            logger.info(f"No chain file found at {self.chain_path}, creating new chain")
            return self.initialize_chain()

        try:
            with open(self.chain_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.chain = AngelaChain.from_dict(data)
            logger.info(f"Loaded chain with {self.chain.length} blocks")
            return self.chain

        except Exception as e:
            logger.error(f"Failed to load chain: {e}")
            raise

    def save_chain(self) -> None:
        """
        Save chain to JSON file.

        Creates parent directories if they don't exist.
        """
        if not self.chain:
            raise ValueError("No chain to save - load or initialize first")

        # Create directory structure
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.chain_path, 'w', encoding='utf-8') as f:
                json.dump(self.chain.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Saved chain ({self.chain.length} blocks) to {self.chain_path}")

        except Exception as e:
            logger.error(f"Failed to save chain: {e}")
            raise

    def add_block(
        self,
        data_hash: str,
        data_type: str,
        data_reference: str,
        metadata: Dict[str, Any]
    ) -> AngelaBlock:
        """
        Add a new block to the chain.

        Args:
            data_hash: SHA-256 hash of the backup archive
            data_type: Type of backup ("full_backup" | "incremental")
            data_reference: Filename of the backup archive
            metadata: Additional info (tables_count, row_counts, etc.)

        Returns:
            AngelaBlock: The newly created block
        """
        if not self.chain:
            self.load_chain()

        # Get previous hash
        if self.chain.blocks:
            previous_hash = self.chain.blocks[-1].block_hash
        else:
            previous_hash = self.GENESIS_HASH

        # Create new block
        block = AngelaBlock(
            block_number=len(self.chain.blocks),
            timestamp=datetime.now().isoformat(),
            previous_hash=previous_hash,
            data_hash=data_hash,
            data_type=data_type,
            data_reference=data_reference,
            metadata=metadata,
            nonce=int(datetime.now().timestamp() * 1000)
        )

        # Calculate and set block hash
        block.block_hash = block.calculate_hash()

        # Add to chain
        self.chain.blocks.append(block)

        # Save immediately
        self.save_chain()

        logger.info(
            f"Added block #{block.block_number} to chain "
            f"(hash: {block.block_hash[:16]}...)"
        )

        return block

    def verify_chain(self) -> VerificationResult:
        """
        Verify entire chain integrity.

        Checks:
        1. Each block's hash matches its calculated hash
        2. Each block's previous_hash matches the prior block's hash
        3. Block numbers are sequential
        4. Timestamps are in order

        Returns:
            VerificationResult: Detailed verification results
        """
        if not self.chain:
            self.load_chain()

        errors: List[str] = []
        warnings: List[str] = []
        total_size_mb = 0.0

        for i, block in enumerate(self.chain.blocks):
            # 1. Verify block hash
            calculated_hash = block.calculate_hash()
            if calculated_hash != block.block_hash:
                errors.append(
                    f"Block {i}: Hash mismatch! "
                    f"Expected {block.block_hash[:16]}..., "
                    f"got {calculated_hash[:16]}..."
                )

            # 2. Verify chain link (previous hash)
            expected_prev = (
                self.chain.blocks[i - 1].block_hash
                if i > 0
                else self.GENESIS_HASH
            )
            if block.previous_hash != expected_prev:
                errors.append(
                    f"Block {i}: Chain link broken! "
                    f"previous_hash doesn't match block {i-1}"
                )

            # 3. Verify block number
            if block.block_number != i:
                warnings.append(
                    f"Block {i}: Block number mismatch "
                    f"(expected {i}, got {block.block_number})"
                )

            # 4. Check timestamps are in order
            if i > 0:
                prev_time = self.chain.blocks[i - 1].timestamp
                if block.timestamp < prev_time:
                    warnings.append(
                        f"Block {i}: Timestamp out of order "
                        f"({block.timestamp} < {prev_time})"
                    )

            # Accumulate size
            if 'backup_size_mb' in block.metadata:
                total_size_mb += block.metadata['backup_size_mb']

        # Get latest backup date
        latest_date = ""
        if self.chain.blocks:
            latest_date = self.chain.blocks[-1].timestamp

        result = VerificationResult(
            is_valid=len(errors) == 0,
            blocks_verified=len(self.chain.blocks),
            errors=errors,
            warnings=warnings,
            latest_backup_date=latest_date,
            chain_length=self.chain.length,
            total_backup_size_mb=total_size_mb
        )

        if result.is_valid:
            logger.info(f"Chain verification PASSED ({result.blocks_verified} blocks)")
        else:
            logger.error(f"Chain verification FAILED: {errors}")

        return result

    def verify_backup_file(self, backup_path: Path, block_number: int) -> bool:
        """
        Verify a specific backup file against its block.

        Args:
            backup_path: Path to the backup archive
            block_number: Which block to verify against

        Returns:
            bool: True if file hash matches block's data_hash
        """
        if not self.chain:
            self.load_chain()

        if block_number >= len(self.chain.blocks):
            logger.error(f"Block {block_number} doesn't exist")
            return False

        block = self.chain.blocks[block_number]

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Calculate file hash
        file_hash = self._calculate_file_hash(backup_path)

        if file_hash == block.data_hash:
            logger.info(f"Backup file verified for block {block_number}")
            return True
        else:
            logger.error(
                f"Backup file hash mismatch for block {block_number}! "
                f"Expected {block.data_hash[:16]}..., "
                f"got {file_hash[:16]}..."
            )
            return False

    def get_block(self, block_number: int) -> Optional[AngelaBlock]:
        """Get a specific block by number."""
        if not self.chain:
            self.load_chain()

        if 0 <= block_number < len(self.chain.blocks):
            return self.chain.blocks[block_number]
        return None

    def get_latest_block(self) -> Optional[AngelaBlock]:
        """Get the most recent block."""
        if not self.chain:
            self.load_chain()

        return self.chain.latest_block

    def get_chain_status(self) -> Dict[str, Any]:
        """
        Get current chain status for display.

        Returns:
            Dict with chain statistics
        """
        if not self.chain:
            self.load_chain()

        latest = self.chain.latest_block

        return {
            'chain_id': self.chain.chain_id,
            'created_at': self.chain.created_at,
            'total_blocks': self.chain.length,
            'latest_block_number': latest.block_number if latest else -1,
            'latest_backup_date': latest.timestamp if latest else None,
            'latest_backup_file': latest.data_reference if latest else None,
            'chain_file_path': str(self.chain_path),
            'chain_file_exists': self.chain_path.exists()
        }

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def calculate_data_hash(data: bytes) -> str:
        """Calculate SHA-256 hash of raw data."""
        return hashlib.sha256(data).hexdigest()
