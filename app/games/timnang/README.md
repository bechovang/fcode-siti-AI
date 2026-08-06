# Tìm Nắng (Game 2) - MVC Architecture

## Overview
Tìm Nắng is an AI vision competition game where 3 teams race to find and photograph objects. Features operator controls, AI-based image recognition, and real-time scoring.

## Architecture (MVC Pattern)

### Controllers (`controllers/`)
- **WebSocketController**: Base class for WebSocket protocol handling
- **StationWebSocketController**: Handles `/ws/station/{team}` station connections
- **MasterWebSocketController**: Handles `/ws/master` operator controls
- **HealthController**: Handles `/health` endpoint

### Services (`services/`)
- **VisionService**: AI-based image recognition using multimodal LLM
- **GameStateService**: Game state and phase transitions (IDLE → ANNOUNCE → PLAYING → ROUND_END → GAME_OVER)
- **ScoringService**: Scoring logic and team ordering (atomic to prevent double-score)
- **BroadcastService**: WebSocket broadcasting to masters and stations
- **RoundService**: Game flow orchestration (start_game, start_round, end_round, game_over)
- **TTSService**: Text-to-speech synthesis and audio playback

### Repositories (`repositories/`)
- **GameObjectRepository**: Access to 6 game objects from `timnang_data.py`
- **TeamRepository**: Access to 3 team definitions with validation
- **ScriptRepository**: Access to round scripts, scoring rules, and pre-cache lines

### Models (`models/`)
- **GameState**: Dataclass representing overall game state (phase, round_idx, current_object, teams)

## Data Flow
1. **Master Connection** → `MasterWebSocketController.handle_connection()`
2. **Station Connection** → `StationWebSocketController.handle_connection(team)`
3. **Game Start** → `RoundService.start_game()` resets scores and starts intro
4. **Round Start** → `RoundService.start_round(idx)` announces object and begins recognition
5. **Recognition Request** → Station sends `{"type": "recognize", "image": "..."}`
6. **AI Vision** → `VisionService.judge_image()` validates if photo contains target object
7. **Scoring** → `ScoringService.assign_order()` assigns finish order (1st=3pts, 2nd=2pts, 3rd=1pt)
8. **Round End** → When all teams finish or operator skips → `RoundService.end_round()`
9. **Next Round/Game Over** → Auto-advance to next round or show final ranking

## Key Features
- **AI Vision**: GPT-4o-mini multimodal image recognition (OpenRouter)
- **Operator Controls**: Start, Restart, Force Accept, Add/Subtract Points, Skip Round
- **Race-Safe Scoring**: `_assign_order()` is atomic under lock + re-checks `order` to prevent double-score
- **No Auto-Timeout**: Operator controls game flow (no automatic timeout per round)
- **Real-time Scoreboard**: Broadcast to all masters and stations instantly

## WebSocket Protocol

### Station → Server
```json
{"type": "recognize", "image": "data:image/jpeg;base64,..."}
```

### Master → Server
```json
{"type": "op", "action": "start"}        # Start new game
{"type": "op", "action": "restart"}      # Reset to IDLE phase
{"type": "op", "action": "force_accept", "team": "A"}  # Force accept for team
{"type": "op", "action": "add_point", "team": "A", "delta": 1}  # Adjust score
{"type": "op", "action": "skip_round"}   # Skip current round
{"type": "op", "action": "next_round"}    # Force start next round
```

### Server → All
```json
{"type": "scoreboard", "phase": "PLAYING", "round": 1, "rounds": 6, "object": "quả bóng tennis", "object_vi": "quả bóng tennis", "teams": [...]}
```

### Server → Station
```json
{"type": "result", "correct": true, "order": 1, "points": 3, "msg": "Đúng rồi! Về nhất! Cộng 3 điểm!"}
{"type": "result", "correct": false, "msg": "Chưa đúng rồi! Thử lại xem!"}
{"type": "round", "object": "quả bóng tennis", "vi": "quả bóng tennis"}
```

## Entry Point
- `app/timnang_master.py` → `games.timnang.app.build_app()` → FastAPI application
- Composition root wires all dependencies (repositories → services → controllers)

## Scoring System
- **1st Place**: 3 points
- **2nd Place**: 2 points  
- **3rd Place**: 1 point
- **Operator Override**: Can manually add/subtract points (±10 clamp per operation)
