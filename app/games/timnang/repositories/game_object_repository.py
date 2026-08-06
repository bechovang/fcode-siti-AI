"""
Repository for accessing game object data.
"""

from typing import List, Optional
from schemas.timnang import GameObject
import timnang_data as data_source


class GameObjectRepository:
    """Repository for accessing game object data from timnang_data.py."""

    def __init__(self):
        """Initialize repository with data source."""
        self._objects = data_source.OBJECTS

    def get_all(self) -> List[GameObject]:
        """
        Get all game objects.

        Returns:
            List of all 6 game objects
        """
        return self._objects

    def get_by_id(self, obj_id: str) -> Optional[GameObject]:
        """
        Get game object by ID.

        Args:
            obj_id: Object ID (e.g., "ball", "lavie")

        Returns:
            GameObject or None if not found
        """
        for obj in self._objects:
            if obj.id == obj_id:
                return obj
        return None

    def get_by_index(self, idx: int) -> Optional[GameObject]:
        """
        Get game object by index.

        Args:
            idx: Object index (0-5)

        Returns:
            GameObject at index or None if out of range
        """
        if 0 <= idx < len(self._objects):
            return self._objects[idx]
        return None

    def count(self) -> int:
        """
        Get total number of game objects.

        Returns:
            Number of game objects (always 6)
        """
        return len(self._objects)
