#!/usr/bin/env python3
"""
Enum Parser Utility - DRY Compliant

Centralized enum parsing logic to replace 15+ duplicated try-catch patterns
across repositories.

Before (repeated in every repository):
    try:
        speaker = Speaker(row['speaker'])
    except ValueError:
        speaker = Speaker.DAVID

After:
    speaker = EnumParser.safe_parse(row['speaker'], Speaker, Speaker.DAVID)

Created: 2026-01-12
DRY Savings: ~75 lines across 6 repositories
"""

from typing import Any, Optional, Type, TypeVar, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

E = TypeVar('E', bound=Enum)


class EnumParser:
    """
    Safe enum parsing utility.

    Replaces duplicated try-catch patterns in _row_to_entity() methods.
    """

    @staticmethod
    def safe_parse(
        value: Any,
        enum_class: Type[E],
        fallback: Optional[E] = None,
        lowercase: bool = True
    ) -> Optional[E]:
        """
        Safely parse a value to an enum with optional fallback.

        Args:
            value: The value to parse (string, int, or None)
            enum_class: The enum class to parse into
            fallback: Value to return if parsing fails (default: first enum member)
            lowercase: Whether to lowercase string values before parsing

        Returns:
            Parsed enum value or fallback

        Examples:
            >>> EnumParser.safe_parse('david', Speaker)
            <Speaker.DAVID: 'david'>

            >>> EnumParser.safe_parse('INVALID', Speaker, Speaker.ANGELA)
            <Speaker.ANGELA: 'angela'>

            >>> EnumParser.safe_parse(None, Speaker)
            <Speaker.DAVID: 'david'>  # First member as fallback
        """
        if value is None:
            return fallback or EnumParser._get_first_member(enum_class)

        try:
            # Handle string values
            if isinstance(value, str):
                parse_value = value.lower() if lowercase else value
                return enum_class(parse_value)

            # Handle int values (for IntEnum)
            if isinstance(value, int):
                return enum_class(value)

            # Already an enum instance
            if isinstance(value, enum_class):
                return value

            # Try direct conversion
            return enum_class(value)

        except (ValueError, KeyError, TypeError) as e:
            if fallback is not None:
                return fallback

            # Return first enum member as default
            first = EnumParser._get_first_member(enum_class)
            logger.debug(f"EnumParser: Could not parse '{value}' to {enum_class.__name__}, using fallback: {first}")
            return first

    @staticmethod
    def safe_parse_optional(
        value: Any,
        enum_class: Type[E],
        lowercase: bool = True
    ) -> Optional[E]:
        """
        Parse value to enum, returning None if invalid.

        Use this when None is a valid result (e.g., optional fields).

        Args:
            value: The value to parse
            enum_class: The enum class to parse into
            lowercase: Whether to lowercase string values

        Returns:
            Parsed enum value or None

        Examples:
            >>> EnumParser.safe_parse_optional('happy', EmotionType)
            <EmotionType.HAPPY: 'happy'>

            >>> EnumParser.safe_parse_optional('INVALID', EmotionType)
            None
        """
        if value is None:
            return None

        try:
            if isinstance(value, str):
                parse_value = value.lower() if lowercase else value
                return enum_class(parse_value)
            return enum_class(value)
        except (ValueError, KeyError, TypeError):
            return None

    @staticmethod
    def safe_parse_list(
        values: Optional[List[Any]],
        enum_class: Type[E],
        skip_invalid: bool = True,
        lowercase: bool = True
    ) -> List[E]:
        """
        Parse a list of values to enums.

        Args:
            values: List of values to parse
            enum_class: The enum class to parse into
            skip_invalid: If True, skip invalid values; if False, use first member
            lowercase: Whether to lowercase string values

        Returns:
            List of parsed enum values

        Examples:
            >>> EnumParser.safe_parse_list(['happy', 'sad', 'INVALID'], EmotionType)
            [<EmotionType.HAPPY>, <EmotionType.SAD>]
        """
        if not values:
            return []

        result = []
        for value in values:
            parsed = EnumParser.safe_parse_optional(value, enum_class, lowercase)
            if parsed is not None:
                result.append(parsed)
            elif not skip_invalid:
                result.append(EnumParser._get_first_member(enum_class))

        return result

    @staticmethod
    def to_value(enum_val: Optional[E]) -> Optional[str]:
        """
        Convert enum to its value (for database storage).

        Args:
            enum_val: Enum instance or None

        Returns:
            The enum's value or None

        Examples:
            >>> EnumParser.to_value(Speaker.DAVID)
            'david'

            >>> EnumParser.to_value(None)
            None
        """
        if enum_val is None:
            return None
        return enum_val.value

    @staticmethod
    def to_values(enum_list: Optional[List[E]]) -> List[str]:
        """
        Convert list of enums to their values.

        Args:
            enum_list: List of enum instances

        Returns:
            List of enum values

        Examples:
            >>> EnumParser.to_values([EmotionType.HAPPY, EmotionType.SAD])
            ['happy', 'sad']
        """
        if not enum_list:
            return []
        return [e.value for e in enum_list]

    @staticmethod
    def _get_first_member(enum_class: Type[E]) -> Optional[E]:
        """Get the first member of an enum class."""
        try:
            return next(iter(enum_class))
        except StopIteration:
            return None


# Convenience aliases for common patterns
parse_enum = EnumParser.safe_parse
parse_enum_optional = EnumParser.safe_parse_optional
parse_enum_list = EnumParser.safe_parse_list
enum_to_value = EnumParser.to_value
enums_to_values = EnumParser.to_values
