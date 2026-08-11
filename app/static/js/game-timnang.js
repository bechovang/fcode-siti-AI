/**
 * Game 2 - Tìm Nắng Cùng AI
 * Shared logic cho Master (bảng điểm) và Station (trạm)
 */

import { burstConfetti, clearConfetti } from './confetti.js';
import { playChime, playFanfare } from './audio.js';
import { formatTime } from './utils.js';

// ==================== CONSTANTS ====================
const TEAMS = [
  { id: 'A', name: 'Đội A', color: '#FF6B6B' },
  { id: 'B', name: 'Đội B', color: '#4ECDC4' },
  { id: 'C', name: 'Đội C', color: '#FFE66D' },
];

const ORDER_WORD = { 1: '🥇 Nhất', 2: '🥈 Nhì', 3: '🥉 Ba' };

// ==================== MASTER (SCOREBOARD) ====================
const board = document.getElementById('board');
const objectEl = document.getElementById('object');
const roundTag = document.getElementById('roundTag');
const player = document.getElementById('player');
const winnerBanner = document.getElementById('winnerBanner');
const rankingEl = document.getElementById('ranking');

export function showRanking(ranking) {
  if (!rankingEl) return;

  const medals = ['🥇', '🥈', '🥉'];
  const rows = ranking.map((r, i) => `
    <div class="row${i === 0 ? ' first' : ''}" style="border-left:6px solid ${r.color}">
      <span class="medal">${medals[i] || (i + 1)}</span>
      <span class="name" style="color:${r.color}">${r.name}</span>
      <span class="pts">${r.score} điểm</span>
    </div>
  `).join('');

  rankingEl.innerHTML = `<div class="panel"><h2>🏆 BẢNG XẾP HẠNG 🏆</h2>${rows}</div>`;
  rankingEl.classList.add('show');
}

export function renderTeamCards() {
  if (!board) return;

  TEAMS.forEach(t => {
    const card = document.createElement('div');
    card.className = 'team';
    card.id = 'team-' + t.id;
    card.style.setProperty('--c', t.color);
    card.innerHTML = `
      <div class="name">${t.name}</div>
      <div class="score" id="score-${t.id}">0</div>
      <div class="order" id="order-${t.id}"></div>
    `;
    board.appendChild(card);
  });

  // Render operator buttons
  const g = document.getElementById('teamOps');
  if (g) {
    TEAMS.forEach(t => {
      const wrap = document.createElement('div');
      wrap.className = 'group';
      wrap.innerHTML = `
        <label style="color:${t.color}">${t.name}</label>
        <button class="team-btn" style="--c:${t.color}" onclick="window.gameOp('force_accept','${t.id}')">✓ Ép đúng</button>
        <button onclick="window.gameOp('add_point','${t.id}',1)">+1</button>
        <button onclick="window.gameOp('add_point','${t.id}',-1)">−1</button>
      `;
      g.appendChild(wrap);
    });
  }
}

export function handleScoreboard(data) {
  if (!roundTag || !objectEl) return;

  roundTag.textContent = `vòng ${data.round}/${data.rounds} · ${data.phase}`;

  if (data.object) {
    objectEl.textContent = '🎯 ' + data.object;
    objectEl.classList.toggle('live', data.phase === 'playing');
  } else if (data.phase === 'idle') {
    objectEl.textContent = 'Bấm Bắt đầu để chơi';
    objectEl.classList.remove('live');
  }

  if (data.teams) {
    data.teams.forEach(t => {
      const scoreEl = document.getElementById('score-' + t.id);
      const orderEl = document.getElementById('order-' + t.id);
      const card = document.getElementById('team-' + t.id);

      if (scoreEl) scoreEl.textContent = t.score;

      if (orderEl) {
        orderEl.textContent = t.order
          ? `${ORDER_WORD[t.order] || `#${t.order}`} · · +${[3, 2, 1][t.order - 1] || 0}`
          : '';
      }

      if (card) {
        card.classList.toggle('finished', !!t.order);
      }
    });
  }
}

export function handleGameOver(data) {
  if (data.ranking) showRanking(data.ranking);

  if (data.winner) {
    const win = TEAMS.find(t => t.id === data.winner);
    if (win) {
      const card = document.getElementById('team-' + win.id);
      if (card) card.classList.add('winner');

      if (winnerBanner) {
        winnerBanner.querySelector('.t').textContent = `🏆 ${data.winner_name} VÔ ĐỊCH!`;
        winnerBanner.querySelector('.t').style.color = win.color;
        winnerBanner.querySelector('.sub').textContent = 'Cảm ơn tất cả các đội!';
        winnerBanner.classList.add('show');
      }

      burstConfetti(win.color, 180);
      playFanfare();

      setTimeout(() => {
        if (winnerBanner) winnerBanner.classList.remove('show');
      }, 6000);
    }
  }
}

export function resetGame() {
  if (!board || !winnerBanner || !rankingEl) return;

  document.querySelectorAll('.team').forEach(c => {
    c.classList.remove('finished', 'winner');
  });

  winnerBanner.classList.remove('show');
  rankingEl.classList.remove('show');

  if (objectEl) objectEl.classList.remove('live');
}

// ==================== STATION (WEBCAM) ====================
const cam = document.getElementById('cam');
const snap = document.getElementById('snap');
const recBtn = document.getElementById('recBtn');
const resultEl = document.getElementById('result');
const objectBox = document.getElementById('objectBox');
const scoreEl = document.getElementById('score');
const phaseTagEl = document.getElementById('phaseTag');

// Get team from URL path
const pathParts = window.location.pathname.split('/');
const team = pathParts[pathParts.length - 1].toUpperCase();
const teamColor = { A: '#FF6B6B', B: '#4ECDC4', C: '#FFE66D' }[team] || '#fff';

// Initialize station
function initStation() {
  if (document.getElementById('teamBadge')) {
    const names = { A: 'Đội A', B: 'Đội B', C: 'Đội C' };
    document.getElementById('teamBadge').textContent = names[team] || `Đội ${team}`;
    document.getElementById('teamBadge').style.background = teamColor;
    document.getElementById('teamBadge').style.color = '#fff';
    document.documentElement.style.setProperty('--team', teamColor);
  }

  // Setup webcam
  if (cam && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 640 } },
      audio: false
    })
      .then(s => {
        cam.srcObject = s;
      })
      .catch(e => {
        if (resultEl) {
          resultEl.className = 'bad';
          resultEl.textContent = `⚠️ Không mở được camera: ${e.message}`;
        }
        if (recBtn) recBtn.disabled = true;
      });
  }

  // Setup recognize button
  if (recBtn) {
    recBtn.addEventListener('click', recognizeStation);
  }

  // Keyboard shortcut: Space to recognize
  document.addEventListener('keydown', e => {
    if (e.key === ' ' && recBtn && !recBtn.disabled) {
      e.preventDefault();
      recognizeStation();
    }
  });
}

export function handleStationRound(data) {
  if (!objectBox) return;

  objectBox.textContent = `🎯 Hãy tìm: ${data.object}`;
  objectBox.classList.add('live');

  if (resultEl) {
    resultEl.textContent = ' ';
    resultEl.className = '';
  }
}

export function handleStationScoreboard(data) {
  if (!phaseTagEl || !scoreEl) return;

  phaseTagEl.textContent = `Trạm ${team} · vòng ${data.round}/${data.rounds} · ${data.phase}`;

  const me = data.teams?.find(t => t.id === team);
  if (me && scoreEl) {
    scoreEl.textContent = `Điểm: ${me.score}`;
  }
}

export function handleStationResult(data) {
  if (!recBtn || !resultEl) return;

  recBtn.disabled = false;
  resultEl.textContent = data.msg || '';

  if (data.correct === true) {
    resultEl.className = 'ok';
    playChime('correct');
    burstConfetti(teamColor);
  } else if (data.correct === false) {
    resultEl.className = 'bad';
    playChime('correct'); // Play chime để feedback
  } else {
    resultEl.className = 'wait';
  }
}

export function resetStation() {
  if (!objectBox || !resultEl) return;

  objectBox.textContent = '⏳ Đợi vòng bắt đầu...';
  objectBox.classList.remove('live');
  resultEl.textContent = ' ';
  resultEl.className = '';
  clearConfetti();
}

export function handleStationGameOver(data) {
  if (!objectBox) return;

  objectBox.textContent = '🏁 Trò chơi kết thúc!';

  if (data.winner === team) {
    if (resultEl) {
      resultEl.className = 'ok';
      resultEl.textContent = '🏆 Đội mình VÔ ĐỊCH!';
    }
    burstConfetti(teamColor, 120);
  }
}

// ==================== RECOGNIZE FUNCTION ====================
function recognizeStation() {
  if (!cam || !cam.videoWidth) {
    if (resultEl) {
      resultEl.className = 'bad';
      resultEl.textContent = 'Camera chưa sẵn sàng';
    }
    return;
  }

  const w = 480;
  const h = Math.round(480 * cam.videoHeight / cam.videoWidth);
  snap.width = w;
  snap.height = h;

  const ctx = snap.getContext('2d');
  ctx.save();
  ctx.scale(-1, 1);
  ctx.translate(-w, 0);
  ctx.drawImage(cam, 0, 0, w, h);
  ctx.restore();

  const img = snap.toDataURL('image/jpeg', 0.7);

  if (resultEl) {
    resultEl.className = 'wait';
    resultEl.textContent = '🤖 Đang nhận diện...';
  }

  if (recBtn) recBtn.disabled = true;

  // Send to station WebSocket
  if (window.stationWs) {
    window.stationWs.send(JSON.stringify({ type: 'recognize', image: img }));
  }
}

// ==================== OPERATOR FUNCTION ====================
function op(action, team, delta) {
  if (!window.masterWs) return;

  const msg = { type: 'op', action };
  if (team) msg.team = team;
  if (delta !== undefined) msg.delta = delta;
  window.masterWs.send(JSON.stringify(msg));
}

// ==================== WEBSOCKET SETUP ====================
function setupMasterWebSocket() {
  const ws = new WebSocket(
    (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/ws/master'
  );

  ws.onopen = () => {
    console.log('[Master] WebSocket connected');
  };

  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    switch (m.type) {
      case 'scoreboard':
        handleScoreboard(m);
        break;
      case 'play_audio':
        if (player) {
          player.src = '/audio/' + m.key;
          player.play().catch(() => {});
        }
        break;
      case 'stop_audio':
        if (player) {
          player.pause();
          player.currentTime = 0;
        }
        break;
      case 'game_over':
        handleGameOver(m);
        break;
      case 'reset':
        resetGame();
        break;
    }
  };

  ws.onerror = (e) => {
    console.error('[Master] WebSocket error:', e);
  };

  ws.onclose = () => {
    console.log('[Master] WebSocket closed');
  };

  // Store WebSocket globally for operator function
  window.masterWs = ws;

  // Setup audio end handlers
  if (player) {
    player.onended = () => {
      try { ws.send(JSON.stringify({ type: 'audio_ended' })); } catch (e) {}
    };
    player.onerror = () => {
      try { ws.send(JSON.stringify({ type: 'audio_ended' })); } catch (e) {}
    };
  }

  // Keyboard shortcuts: Enter = start, Esc = restart
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Enter') op('start');
    if (e.key === 'Escape') op('restart');
  });
}

function setupStationWebSocket() {
  const ws = new WebSocket(
    (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/ws/station/' + team
  );

  ws.onopen = () => {
    console.log('[Station] WebSocket connected');
  };

  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    switch (m.type) {
      case 'round':
        handleStationRound(m);
        break;
      case 'scoreboard':
        handleStationScoreboard(m);
        break;
      case 'result':
        handleStationResult(m);
        break;
      case 'reset':
        resetStation();
        break;
      case 'game_over':
        handleStationGameOver(m);
        break;
    }
  };

  ws.onerror = (e) => {
    console.error('[Station] WebSocket error:', e);
  };

  ws.onclose = () => {
    console.log('[Station] WebSocket closed');
  };

  // Store WebSocket globally for recognize function
  window.stationWs = ws;
}

// ==================== INITIALIZATION ====================
function init() {
  const pathname = window.location.pathname;

  // Check if this is master page
  if (pathname === '/timnang' || pathname.endsWith('/timnang/')) {
    renderTeamCards();
    setupMasterWebSocket();
    // Expose operator function globally for onclick handlers
    window.gameOp = op;
  }
  // Check if this is station page
  else if (pathname.includes('/station/')) {
    initStation();
    setupStationWebSocket();
  }
}

// Start initialization when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export formatTime for use in other modules
export { formatTime };
