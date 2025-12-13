"""
Supabase Client Wrapper
Handles connection to Supabase Cloud PostgreSQL.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import asyncpg

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Async client for Supabase PostgreSQL.
    Uses direct PostgreSQL connection (not REST API) for better performance.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize Supabase client.
        
        Args:
            database_url: Supabase PostgreSQL connection string
                         Format: postgresql://user:pass@host:port/db
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self._connected = False
    
    async def connect(self, max_retries: int = 3) -> bool:
        """
        Establish connection pool to Supabase.
        
        Returns:
            True if connected successfully
        """
        for attempt in range(1, max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=60,
                    ssl='require'  # Supabase requires SSL
                )
                self._connected = True
                logger.info("✅ Connected to Supabase PostgreSQL")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Supabase connection attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"❌ Failed to connect to Supabase after {max_retries} attempts")
                    return False
        
        return False
    
    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self._connected = False
            logger.info("Disconnected from Supabase")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Supabase."""
        return self._connected and self.pool is not None
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self.is_connected:
            raise ConnectionError("Not connected to Supabase")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def upsert_batch(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        primary_key: str,
        columns: List[str]
    ) -> int:
        """
        Upsert a batch of records to Supabase.
        
        Args:
            table_name: Target table
            records: List of records to upsert
            primary_key: Primary key column name
            columns: Column names to upsert
            
        Returns:
            Number of records upserted
        """
        if not records:
            return 0
        
        # Build UPSERT query
        col_names = ", ".join(columns)
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        update_set = ", ".join([
            f"{col} = EXCLUDED.{col}" 
            for col in columns 
            if col != primary_key
        ])
        
        query = f"""
            INSERT INTO {table_name} ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({primary_key}) DO UPDATE SET
            {update_set}
        """
        
        count = 0
        async with self.acquire() as conn:
            for record in records:
                try:
                    values = [record.get(col) for col in columns]
                    await conn.execute(query, *values)
                    count += 1
                except Exception as e:
                    logger.error(f"Error upserting to {table_name}: {e}")
                    raise
        
        return count
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def test_connection(self) -> bool:
        """Test if connection is working."""
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
