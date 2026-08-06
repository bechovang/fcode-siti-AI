"""Regression: race double-scoring Trò 2 + scoring/ordering.

Updated for MVC architecture: tests now use ScoringService instead of Game class.
"""
import pytest
from games.timnang.services.scoring_service import ScoringService
from games.timnang.services.game_state_service import GameStateService
from games.timnang.repositories.team_repository import TeamRepository
from games.timnang.repositories.script_repository import ScriptRepository
from timnang_data import TEAMS
from schemas.timnang import TeamState


@pytest.fixture
def scoring_service():
    """Create scoring service with test data."""
    team_repo = TeamRepository()
    script_repo = ScriptRepository()
    game_state = GameStateService(teams=team_repo.get_all())
    return ScoringService(game_state=game_state, script_repo=script_repo)


@pytest.fixture
def game_state():
    """Create game state service for testing."""
    team_repo = TeamRepository()
    return GameStateService(teams=team_repo.get_all())


async def test_assign_order_no_double_score(scoring_service, game_state):
    """Test that _assign_order prevents double-scoring."""
    # Setup: team A in PLAYING phase, round 0
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING
    game_state.round_idx = 0

    # First assignment should succeed
    ok, order, points = await scoring_service.assign_order("A", correct_label="Đúng rồi!")
    assert ok is True
    assert order == 1
    assert points == 3

    # Second assignment should fail (already finished)
    ok2, order2, points2 = await scoring_service.assign_order("A", correct_label="Đúng rồi!")
    assert ok2 is False
    assert order2 is None
    assert points2 is None

    # Verify score didn't change
    team_state = game_state.get_team_state("A")
    assert team_state["order"] == 1
    assert team_state["score"] == 3


async def test_assign_order_ordering_321(scoring_service, game_state):
    """Test that teams are ordered correctly 3-2-1."""
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING
    game_state.round_idx = 0

    # Assign in order: A, B, C
    ok1, order1, pts1 = await scoring_service.assign_order("A", correct_label="x")
    assert ok1 is True
    assert order1 == 1 and pts1 == 3

    ok2, order2, pts2 = await scoring_service.assign_order("B", correct_label="x")
    assert ok2 is True
    assert order2 == 2 and pts2 == 2

    ok3, order3, pts3 = await scoring_service.assign_order("C", correct_label="x")
    assert ok3 is True
    assert order3 == 3 and pts3 == 1

    # Verify final ordering
    team_a = game_state.get_team_state("A")
    team_b = game_state.get_team_state("B")
    team_c = game_state.get_team_state("C")

    assert team_a["order"] == 1 and team_a["score"] == 3
    assert team_b["order"] == 2 and team_b["score"] == 2
    assert team_c["order"] == 3 and team_c["score"] == 1


async def test_force_accept_uses_assign_order(scoring_service):
    """Test that force_accept uses assign_order internally."""
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING
    game_state.round_idx = 0

    # force_accept should use assign_order
    ok, order, points = await scoring_service.force_accept("A")
    assert ok is True
    assert order == 1
    assert points == 3

    # Second call should fail (already finished)
    ok2, order2, points2 = await scoring_service.force_accept("A")
    assert ok2 is False
    assert order2 is None
    assert points2 is None

    # Verify score didn't change
    team_a = game_state.get_team_state("A")
    assert team_a["order"] == 1
    assert team_a["score"] == 3


async def test_force_accept_then_recognize_no_double(scoring_service):
    """Bug gốc: operator force_accept trong lúc vision chạy → giờ re-check → không nhân đôi."""
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING
    game_state.round_idx = 0

    # Force accept should succeed
    ok1, order1, points1 = await scoring_service.force_accept("A")
    assert ok1 is True
    assert order1 == 1
    assert points1 == 3

    # Regular assign after force accept should fail (already finished)
    ok2, order2, points2 = await scoring_service.assign_order("A", correct_label="Đúng rồi!")
    assert ok2 is False
    assert order2 is None
    assert points2 is None

    # Verify score didn't change
    team_a = game_state.get_team_state("A")
    assert team_a["score"] == 3


async def test_add_point_validates_delta(scoring_service):
    """Test that add_point validates and clamps delta values."""
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING
    game_state.round_idx = 0

    # Add 1 point
    ok1 = await game_state.update_team_score("A", 1)
    assert ok1 is True
    assert game_state.get_team_state("A")["score"] == 1

    # Subtract 1 point
    ok2 = await game_state.update_team_score("A", -1)
    assert ok2 is True
    assert game_state.get_team_state("A")["score"] == 0

    # Invalid delta should be ignored
    ok3 = await game_state.update_team_score("A", "khongphai_so")
    assert ok3 is False

    # None delta should be ignored
    ok4 = await game_state.update_team_score("A", None)
    assert ok4 is False

    # Large delta should be clamped to ±10
    ok5 = await game_state.update_team_score("A", 9999)
    assert ok5 is True
    assert game_state.get_team_state("A")["score"] == 10  # Clamped to max


async def test_add_point_unknown_team_ignored(game_state):
    """Test that add_point ignores unknown teams."""
    from schemas.timnang import Game2Phase
    game_state.phase = Game2Phase.PLAYING

    # Adding to unknown team "Z" should be ignored
    ok = await game_state.update_team_score("Z", 5)
    assert ok is False

    # Verify "Z" not in teams
    assert game_state.get_team_state("Z") is None
