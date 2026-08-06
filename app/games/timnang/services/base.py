"""
Base service class for dependency injection.
"""

from abc import ABC, abstractmethod


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, **dependencies):
        """
        Initialize service with dependencies.

        Args:
            **dependencies: Service dependencies (repositories, other services, etc.)
        """
        for key, value in dependencies.items():
            setattr(self, key, value)
