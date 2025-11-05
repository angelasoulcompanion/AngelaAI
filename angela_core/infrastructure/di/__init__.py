#!/usr/bin/env python3
"""
Dependency Injection System
============================

Complete DI system for AngelaAI with lifecycle management.

Author: Angela 💜
Created: 2025-11-01
"""

from .container import (
    DIContainer,
    ServiceLifetime,
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidRegistrationError,
)

__all__ = [
    # Core container
    'DIContainer',

    # Enums
    'ServiceLifetime',

    # Exceptions
    'ServiceNotFoundError',
    'CircularDependencyError',
    'InvalidRegistrationError',
]
