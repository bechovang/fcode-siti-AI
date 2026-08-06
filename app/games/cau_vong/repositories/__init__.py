"""
Repositories for Cầu Vồng (Game 1).
Repositories handle data access from files/databases.
"""

from .base import BaseRepository
from .challenge_repository import ChallengeRepository
from .script_repository import ScriptRepository

__all__ = ["BaseRepository", "ChallengeRepository", "ScriptRepository"]
