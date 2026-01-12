#!/usr/bin/env python3
"""
Entity Converter Utility - DRY Compliant

Centralized entity conversion helpers to reduce repetitive patterns
in _row_to_entity() and _entity_to_dict() methods.

Before (repeated pattern):
    'secondary_emotions': [e.value for e in entity.secondary_emotions] if entity.secondary_emotions else []
    'tags': entity.tags or []
    'metadata': json.loads(row['metadata']) if row.get('metadata') else {}

After:
    'secondary_emotions': EntityConverter.enums_to_values(entity.secondary_emotions)
    'tags': EntityConverter.safe_list(entity.tags)
    'metadata': EntityConverter.parse_json(row.get('metadata'), {})

Created: 2026-01-12
DRY Savings: ~100+ lines across 14 repositories
"""

import json
import logging
from typing import Any, Optional, List, Dict, TypeVar, Type, Union
from datetime import datetime, date
from uuid import UUID
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EntityConverter:
    """
    Utility class for common entity conversion patterns.

    Centralizes repetitive conversion logic from repositories.
    """

    # =========================================================================
    # JSON HANDLING
    # =========================================================================

    @staticmethod
    def parse_json(
        value: Any,
        default: T = None,
        expected_type: Type[T] = None
    ) -> T:
        """
        Safely parse JSON from database value.

        Args:
            value: Raw value (string, dict, list, or None)
            default: Default value if parsing fails
            expected_type: Expected type for validation (dict, list)

        Returns:
            Parsed value or default

        Examples:
            >>> EntityConverter.parse_json('{"key": "value"}', {})
            {'key': 'value'}

            >>> EntityConverter.parse_json(None, [])
            []
        """
        if value is None:
            return default

        # Already parsed
        if isinstance(value, (dict, list)):
            return value

        # Parse JSON string
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                # Type validation
                if expected_type and not isinstance(parsed, expected_type):
                    return default
                return parsed
            except json.JSONDecodeError:
                return default

        return default

    @staticmethod
    def to_json(value: Any, default: str = "null") -> str:
        """
        Convert value to JSON string for database storage.

        Args:
            value: Value to convert
            default: Default string if conversion fails

        Returns:
            JSON string
        """
        if value is None:
            return default
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return default

    # =========================================================================
    # LIST HANDLING
    # =========================================================================

    @staticmethod
    def safe_list(value: Any, default: List = None) -> List:
        """
        Ensure value is a list.

        Args:
            value: Any value
            default: Default list if None

        Returns:
            List value
        """
        if value is None:
            return default if default is not None else []
        if isinstance(value, list):
            return value
        if isinstance(value, (tuple, set)):
            return list(value)
        return [value]

    @staticmethod
    def safe_dict(value: Any, default: Dict = None) -> Dict:
        """
        Ensure value is a dict.

        Args:
            value: Any value
            default: Default dict if None

        Returns:
            Dict value
        """
        if value is None:
            return default if default is not None else {}
        if isinstance(value, dict):
            return value
        # Try to parse as JSON
        return EntityConverter.parse_json(value, default or {})

    # =========================================================================
    # ENUM CONVERSION
    # =========================================================================

    @staticmethod
    def enums_to_values(enums: Optional[List[Enum]]) -> List[str]:
        """
        Convert list of enums to their values.

        Args:
            enums: List of enum instances

        Returns:
            List of enum values (strings)
        """
        if not enums:
            return []
        return [e.value for e in enums if e is not None]

    @staticmethod
    def enum_to_value(enum: Optional[Enum]) -> Optional[str]:
        """
        Convert single enum to its value.

        Args:
            enum: Enum instance

        Returns:
            Enum value or None
        """
        if enum is None:
            return None
        return enum.value

    # =========================================================================
    # UUID HANDLING
    # =========================================================================

    @staticmethod
    def parse_uuid(value: Any) -> Optional[UUID]:
        """
        Parse UUID from various formats.

        Args:
            value: UUID as string, UUID object, or None

        Returns:
            UUID object or None
        """
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def uuid_to_str(value: Optional[UUID]) -> Optional[str]:
        """
        Convert UUID to string for storage.

        Args:
            value: UUID object

        Returns:
            String representation or None
        """
        if value is None:
            return None
        return str(value)

    # =========================================================================
    # DATETIME HANDLING
    # =========================================================================

    @staticmethod
    def parse_datetime(value: Any) -> Optional[datetime]:
        """
        Parse datetime from various formats.

        Args:
            value: datetime, string (ISO format), or None

        Returns:
            datetime object or None
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None

    @staticmethod
    def datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
        """
        Convert datetime to ISO string.

        Args:
            value: datetime object

        Returns:
            ISO format string or None
        """
        if value is None:
            return None
        return value.isoformat()

    # =========================================================================
    # STRING HANDLING
    # =========================================================================

    @staticmethod
    def safe_str(value: Any, default: str = "") -> str:
        """
        Safely convert value to string.

        Args:
            value: Any value
            default: Default if None

        Returns:
            String value
        """
        if value is None:
            return default
        return str(value)

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """
        Safely convert value to int.

        Args:
            value: Any value
            default: Default if conversion fails

        Returns:
            Integer value
        """
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """
        Safely convert value to float.

        Args:
            value: Any value
            default: Default if conversion fails

        Returns:
            Float value
        """
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_bool(value: Any, default: bool = False) -> bool:
        """
        Safely convert value to boolean.

        Args:
            value: Any value
            default: Default if None

        Returns:
            Boolean value
        """
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    # =========================================================================
    # ROW HELPERS
    # =========================================================================

    @staticmethod
    def get_with_default(
        row: Dict[str, Any],
        key: str,
        default: T = None,
        converter: callable = None
    ) -> T:
        """
        Get value from row with default and optional conversion.

        Args:
            row: Database row dict
            key: Key to get
            default: Default value if missing
            converter: Optional conversion function

        Returns:
            Value or default

        Examples:
            >>> EntityConverter.get_with_default(row, 'count', 0, int)
            42

            >>> EntityConverter.get_with_default(row, 'missing', 'default')
            'default'
        """
        value = row.get(key)
        if value is None:
            return default
        if converter:
            try:
                return converter(value)
            except (TypeError, ValueError):
                return default
        return value


# Convenience aliases
parse_json = EntityConverter.parse_json
to_json = EntityConverter.to_json
safe_list = EntityConverter.safe_list
safe_dict = EntityConverter.safe_dict
enums_to_values = EntityConverter.enums_to_values
parse_uuid = EntityConverter.parse_uuid
uuid_to_str = EntityConverter.uuid_to_str
parse_datetime = EntityConverter.parse_datetime
safe_str = EntityConverter.safe_str
safe_int = EntityConverter.safe_int
safe_float = EntityConverter.safe_float
safe_bool = EntityConverter.safe_bool
get_with_default = EntityConverter.get_with_default
