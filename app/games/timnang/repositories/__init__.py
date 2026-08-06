"""
Repositories for Tìm Nắng (Game 2).
Repositories handle data access from files/databases.
"""

from .base import BaseRepository
from .game_object_repository import GameObjectRepository
from .team_repository import TeamRepository
from .script_repository import ScriptRepository

__all__ = ["BaseRepository", "GameObjectRepository", "TeamRepository", "ScriptRepository"]
