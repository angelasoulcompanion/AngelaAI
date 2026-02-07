"""Message repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class IMessageRepository(IRepository):
    """
    Extended interface for Angela Message repository operations.

    Table: angela_messages
    Purpose: Store Angela's thoughts, reflections, and important messages

    Added: Batch-24 (Conversations & Messages Migration)
    """

    @abstractmethod
    async def find_by_filters(
        self,
        message_type: Optional[str] = None,
        category: Optional[str] = None,
        is_important: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Find messages by multiple filters.

        Args:
            message_type: Filter by message type (thought, reflection, note, etc.)
            category: Filter by category
            is_important: Filter by importance flag
            is_pinned: Filter by pinned flag
            limit: Maximum number of results

        Returns:
            List of messages matching filters
        """
        ...

    @abstractmethod
    async def get_pinned(self, limit: int = 50) -> List[Any]:
        """
        Get all pinned messages.

        Args:
            limit: Maximum number of results

        Returns:
            List of pinned messages, ordered by created_at DESC
        """
        ...

    @abstractmethod
    async def get_important(self, limit: int = 50) -> List[Any]:
        """
        Get all important messages.

        Args:
            limit: Maximum number of results

        Returns:
            List of important messages, ordered by created_at DESC
        """
        ...

    @abstractmethod
    async def get_by_type(
        self,
        message_type: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get messages by type.

        Args:
            message_type: Type of message (thought, reflection, note, etc.)
            limit: Maximum number of results

        Returns:
            List of messages of specified type
        """
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get messages by category.

        Args:
            category: Message category
            limit: Maximum number of results

        Returns:
            List of messages in category
        """
        ...

    @abstractmethod
    async def search_by_text(
        self,
        query_text: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Search messages by text content.

        Args:
            query_text: Search query
            limit: Maximum number of results

        Returns:
            List of messages matching search query
        """
        ...

    @abstractmethod
    async def toggle_pin(self, message_id: UUID) -> bool:
        """
        Toggle pin status of a message.

        Args:
            message_id: Message UUID

        Returns:
            New pin status (True if pinned, False if unpinned)

        Raises:
            EntityNotFoundError: If message not found
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """
        Count total messages.

        Returns:
            Total number of messages
        """
        ...

    @abstractmethod
    async def count_pinned(self) -> int:
        """
        Count pinned messages.

        Returns:
            Number of pinned messages
        """
        ...

    @abstractmethod
    async def count_important(self) -> int:
        """
        Count important messages.

        Returns:
            Number of important messages
        """
        ...

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get message statistics.

        Returns:
            Dictionary with statistics:
            - total_messages: Total count
            - pinned_messages: Count of pinned
            - important_messages: Count of important
            - by_type: List of {type, count} dicts
            - by_category: List of {category, count} dicts
            - recent_emotions: List of recent emotion values
        """
        ...
