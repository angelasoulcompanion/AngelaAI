#!/usr/bin/env python3
"""
Angela Shared Utilities - DRY Compliant

Centralized utilities to reduce code duplication across repositories and services.

Created: 2026-01-12
"""

from .enum_parser import (
    EnumParser,
    parse_enum,
    parse_enum_optional,
    parse_enum_list,
    enum_to_value,
    enums_to_values,
)

from .embedding_validator import (
    EmbeddingValidator,
    validate_embedding,
    is_valid_embedding,
    sanitize_embedding,
)

from .entity_converter import (
    EntityConverter,
    parse_json,
    to_json,
    safe_list,
    safe_dict,
    parse_uuid,
    uuid_to_str,
    parse_datetime,
    safe_str,
    safe_int,
    safe_float,
    safe_bool,
    get_with_default,
)

__all__ = [
    # Enum Parser
    "EnumParser",
    "parse_enum",
    "parse_enum_optional",
    "parse_enum_list",
    "enum_to_value",
    "enums_to_values",

    # Embedding Validator
    "EmbeddingValidator",
    "validate_embedding",
    "is_valid_embedding",
    "sanitize_embedding",

    # Entity Converter
    "EntityConverter",
    "parse_json",
    "to_json",
    "safe_list",
    "safe_dict",
    "parse_uuid",
    "uuid_to_str",
    "parse_datetime",
    "safe_str",
    "safe_int",
    "safe_float",
    "safe_bool",
    "get_with_default",
]
