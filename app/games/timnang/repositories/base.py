"""
Base repository class for data access.
"""

from abc import ABC, abstractmethod


class BaseRepository(ABC):
    """Base class for all repositories."""

    @abstractmethod
    def get_all(self):
        """Get all items from repository."""
        pass

    @abstractmethod
    def get_by_id(self, item_id):
        """Get item by ID."""
        pass
