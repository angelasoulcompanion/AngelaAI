"""
BaseDBService — eliminates repeated DB connection boilerplate.

Services that create their own AngelaDatabase() and manage
connect/disconnect can inherit from this instead.

Usage:
    class MyService(BaseDBService):
        async def do_something(self):
            await self.connect()
            return await self.db.fetch("SELECT 1")
"""

from typing import Optional
from angela_core.database import AngelaDatabase


class BaseDBService:
    """Base class for services that manage their own DB connection."""

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db or AngelaDatabase()
        self._owns_db = db is None
        self._connected = False

    async def connect(self):
        if not self._connected:
            await self.db.connect()
            self._connected = True

    async def disconnect(self):
        if self._connected and self._owns_db:
            await self.db.disconnect()
            self._connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False
