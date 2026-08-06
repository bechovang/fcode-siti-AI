# Cầu Vồng (Game 1) - MVC Architecture

## Overview
Cầu Vồng is an AI-powered conversation game with the KOON character, featuring 7 rainbow color challenges that children answer to restore colors to a rainbow.

## Architecture (MVC Pattern)

### Controllers (`controllers/`)
- **WebSocketController**: Base class for WebSocket protocol handling
- **CauVongWebSocketController**: Handles `/ws` WebSocket connections and message routing
- **HealthController**: Handles `/health` endpoint

### Services (`services/`)
- **JudgeService**: Answer judging with fuzzy matching + optional LLM
- **TTSService**: Text-to-speech synthesis and audio playback
- **SessionManager**: Session lifecycle and state management
- **GameFlowService**: Orchestrates complete game flow (intro → 7 challenges → rainbow → recap → goodbye)

### Repositories (`repositories/`)
- **ChallengeRepository**: Access to 7 challenge data from `koon_data.py`
- **ScriptRepository**: Access to intro/recap/goodbye scripts and audio keys

### Models (`models/`)
- **SessionState**: Dataclass representing game session state (phase, challenge_index, unlocked_colors, events)

## Data Flow
1. **WebSocket Connection** → `CauVongWebSocketController.handle_connection()`
2. **Session Creation** → `SessionManager` created with WebSocket and TTSService
3. **Game Start** → `GameFlowService.run_full_game()` orchestrates entire game
4. **Answer Judging** → `JudgeService.judge_and_reply()` evaluates answers
5. **TTS Playback** → `TTSService.synthesize_and_play()` generates and plays audio
6. **State Management** → `SessionManager` tracks phase, events, operator controls

## Key Features
- **Answer Judging**: Fast fuzzy matching for known variants, optional LLM for intelligent evaluation
- **TTS System**: Pre-cached audio for instant playback (<200ms), dynamic Kokoro synthesis for flexibility
- **Operator Controls**: R=replay, S=skip, F=force_correct, Esc=restart
- **STT**: Browser Web Speech API (Chrome=Google, Edge=Azure)
- **Live2D Avatar**: Optional Live2D `mao_pro` from submodule, fallback emoji 🦊

## WebSocket Protocol
Client sends:
```json
{"type": "start"}              # Start/restart game
{"type": "audio_ended"}         # Audio playback finished
{"type": "video_ended"}         # Video playback finished
{"type": "answer", "text": "..."} # Submit answer
{"type": "op", "action": "..."}   # Operator control
```

Server sends:
```json
{"type": "ready"}               # Connection ready
{"type": "state", "phase": "...", "idx": 0, "unlocked": [], "total": 7}
{"type": "show_question", "text": "...", "color": "...", "hex": "..."}
{"type": "play_audio", "key": "..."}
{"type": "unlock_color", "hex": "..."}
{"type": "rainbow"}              # Show rainbow animation
{"type": "magic_reveal"}         # KOON flies + magic transition
{"type": "play_video", "url": "..."}
{"type": "game_over"}             # Game complete
```

## Entry Point
- `app/server.py` → `games.cau_vong.app.build_app()` → FastAPI application
- Composition root wires all dependencies (repositories → services → controllers)
