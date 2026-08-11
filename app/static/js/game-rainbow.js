/**
 * Game 1 - Cùng Koon Đi Tìm Cầu Vồng
 * Main game logic
 */

import { burstConfetti } from './confetti.js';
import { playChime, playMagic } from './audio.js';
import { toggleMic, stopSTT } from './stt.js';
import { browserName, engineLabel, getSpeechRecognition } from './utils.js';

// ==================== CONSTANTS ====================
const RAINBOW_HEX = ["#FF6B6B","#FFA500","#FFD93D","#6BCF7F","#4ECDC4","#A78BFA","#F06595"];
const RAINBOW_NAMES = ["Đỏ","Cam","Vàng","Xanh lá","Xanh lăm","Tím","Hồng"];
const MAGIC_COLORS = ['#FF6B6B','#FFA500','#FFD93D','#6BCF7F','#4ECDC4','#A78BFA','#F06595','#fff','#FFD700'];

// ==================== DOM ELEMENTS ====================
const player = document.getElementById('player');
const koon = document.getElementById('koon');
const qEl = document.getElementById('question');
const statusEl = document.getElementById('status');
const phaseTag = document.getElementById('phaseTag');
const sttHeardEl = document.getElementById('sttHeard');
const finaleEl = document.getElementById('finale');

// ==================== RAINBOW SVG ====================
(function initRainbow() {
  const svg = document.getElementById('rainbow');
  RAINBOW_HEX.forEach((hex, i) => {
    const r = 320 - i * 26;
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', `M ${350-r} 380 A ${r} ${r} 0 0 1 ${350+r} 380`);
    p.setAttribute('stroke', hex);
    p.style.color = hex;
    p.dataset.hex = hex;
    svg.appendChild(p);
  });
})();

export function unlockHex(hex) {
  document.querySelectorAll('#rainbow path').forEach(p => {
    if (p.dataset.hex === hex) p.classList.add('on');
  });
}

export function clearRainbow() {
  document.querySelectorAll('#rainbow path').forEach(p => p.classList.remove('on'));
}

// ==================== PROGRESS BAR ====================
(function initProgressBar() {
  const bar = document.getElementById('progressBar');
  RAINBOW_HEX.forEach((hex, i) => {
    const orb = document.createElement('div');
    orb.className = 'orb';
    orb.id = 'orb-' + i;
    orb.style.setProperty('--orb-color', hex);
    bar.appendChild(orb);
  });
})();

export function orbDone(i) {
  const el = document.getElementById('orb-' + i);
  if (el) el.classList.add('done');
}

// ==================== STARS ====================
(function initStars() {
  const stars = document.getElementById('stars');
  for (let i = 0; i < 30; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    s.style.left = Math.random() * 100 + '%';
    s.style.top = Math.random() * 60 + '%';
    s.style.setProperty('--dur', (2 + Math.random() * 3) + 's');
    s.style.animationDelay = Math.random() * 3 + 's';
    s.style.width = s.style.height = (1 + Math.random() * 2) + 'px';
    stars.appendChild(s);
  }
})();

// ==================== CONFETTI ====================
export { burstConfetti };

// ==================== CHIME SOUND ====================
export { playChime };

// ==================== WEBSOCKET ====================
let ws = null;

export function connectWebSocket() {
  ws = new WebSocket((location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/ws');

  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    handleMessage(m);
  };

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };
}

function handleMessage(m) {
  switch (m.type) {
    case 'play_audio':
      playAudio(m.key);
      break;
    case 'stop_audio':
      try {
        player.pause();
        player.currentTime = 0;
      } catch (e) {}
      koon.classList.remove('speaking');
      lipPcm = null;
      lipOffset = 0;
      lipTotal = 0;
      break;
    case 'show_question':
      qEl.textContent = m.text;
      qEl.style.setProperty('--q-color', m.hex || 'transparent');
      qEl.classList.add('show', 'has-color');
      break;
    case 'await_answer':
      statusEl.textContent = '👂 KOON đang nghe... (bé nói đáp án)';
      break;
    case 'unlock_color':
      unlockHex(m.hex);
      koonHappy();
      const ui = RAINBOW_HEX.indexOf(m.hex);
      if (ui >= 0) orbDone(ui);
      statusEl.textContent = '✅ ĐÚNG! Mảnh màu đã được tìm thấy!';
      burstConfetti(60, [m.hex, '#FFD700', '#fff']);
      playChime('correct');
      break;
    case 'rainbow':
      statusEl.textContent = '🌈 Cầu vồng rực rỡ!';
      qEl.classList.remove('show', 'has-color');
      clearRainbow();
      RAINBOW_HEX.forEach((h, i) => {
        unlockHex(h);
        orbDone(i);
      });
      finaleEl.classList.add('show');
      burstConfetti(150, RAINBOW_HEX);
      playChime('finale');
      setTimeout(() => {
        finaleEl.classList.remove('show');
      }, 3500);
      break;
    case 'magic_reveal':
      koonMagicIn();
      break;
    case 'play_video':
      doFlash(() => {
        showRecapVideo(m.url);
        koonMagicOut();
      });
      break;
    case 'show_recap_overlay':
      doFlash(() => {
        showRecapOverlay();
        koonMagicOut();
      });
      break;
    case 'reset':
      clearRainbow();
      qEl.classList.remove('show', 'has-color');
      qEl.textContent = '';
      statusEl.textContent = '';
      finaleEl.classList.remove('show');
      sttHeardEl.classList.remove('show');
      hideRecap();
      koonMagicOut();
      flashEl.classList.remove('on');
      document.querySelectorAll('.orb').forEach(o => o.classList.remove('done', 'active'));
      break;
    case 'state':
      phaseTag.textContent = `${m.phase} · ${m.idx + 1}/${m.total} · mở ${m.unlocked.length}`;
      document.querySelectorAll('.orb').forEach(o => o.classList.remove('active'));
      const cur = document.getElementById('orb-' + m.idx);
      if (cur && m.phase === 'ask') cur.classList.add('active');
      break;
  }
}

// ==================== START ====================
export function startShow() {
  document.getElementById('startOverlay').style.display = 'none';
  ensureLipCtx();
  player.muted = true;
  player.play().then(() => {
    player.muted = false;
  }).catch(() => {
    player.muted = false;
  });
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify({ type: 'start' }));
  }
}

// ==================== AUDIO ====================
function playAudio(key) {
  koon.classList.add('speaking');
  const url = `/audio/${key}`;
  player.src = url;
  player.play().catch(err => console.warn('play err', err));
  decodeForLipSync(url);
}

player.onended = () => {
  koon.classList.remove('speaking');
  if (ws) ws.send(JSON.stringify({ type: 'audio_ended' }));
};

// ==================== RECAP VIDEO ====================
const recapVideo = document.getElementById('recapVideo');
const recapOverlay = document.getElementById('recapOverlay');
const recapStage = document.getElementById('stage');
const rvPlay = document.getElementById('rvPlay');
const rvSeek = document.getElementById('rvSeek');
const rvTime = document.getElementById('rvTime');
const rvMute = document.getElementById('rvMute');
let recapTimer = null;
let rvSeeking = false;

function hideRecap() {
  try {
    recapVideo.pause();
    recapVideo.removeAttribute('src');
    recapVideo.load();
  } catch (e) {}
  recapStage.classList.remove('video-active', 'recap-video', 'recap-overlay', 'has-video');
  if (recapTimer) {
    clearTimeout(recapTimer);
    recapTimer = null;
  }
  magicCanvas.classList.remove('on');
  stopMagicParticles();
}

function showRecapVideo(url) {
  hideRecap();
  recapVideo.src = url;
  recapStage.classList.add('video-active', 'recap-video', 'has-video');
  recapVideo.play().catch(() => {});
  recapVideo.onended = () => {
    hideRecap();
    if (ws) ws.send(JSON.stringify({ type: 'video_ended' }));
  };
  recapVideo.onerror = () => {
    hideRecap();
    if (ws) ws.send(JSON.stringify({ type: 'video_ended' }));
  };
}

function showRecapOverlay() {
  hideRecap();
  recapStage.classList.add('video-active', 'recap-overlay');
  recapTimer = setTimeout(() => {
    hideRecap();
    if (ws) ws.send(JSON.stringify({ type: 'overlay_ended' }));
  }, 15000);
}

// Recap video controls
rvPlay.onclick = () => {
  if (recapVideo.paused) recapVideo.play();
  else recapVideo.pause();
};

recapVideo.onplay = () => {
  rvPlay.textContent = '⏸';
};

recapVideo.onpause = () => {
  rvPlay.textContent = '▶';
};

recapVideo.ontimeupdate = () => {
  if (!rvSeeking && recapVideo.duration) {
    rvSeek.value = (recapVideo.currentTime / recapVideo.duration) * 1000;
  }
  rvTime.textContent = formatTime(recapVideo.currentTime) + ' / ' + formatTime(recapVideo.duration);
};

rvSeek.oninput = () => {
  rvSeeking = true;
  if (recapVideo.duration) {
    recapVideo.currentTime = (rvSeek.value / 1000) * recapVideo.duration;
  }
};

rvSeek.onchange = () => {
  rvSeeking = false;
};

rvMute.onclick = () => {
  recapVideo.muted = !recapVideo.muted;
  rvMute.textContent = recapVideo.muted ? '🔇' : '🔊';
};

// ==================== MAGIC REVEAL ====================
const magicCanvas = document.getElementById('magicCanvas');
const mctx = magicCanvas.getContext('2d');
const flashEl = document.getElementById('flash');
let magicParticles = [];
let magicRunning = false;

function resizeMagic() {
  magicCanvas.width = window.innerWidth;
  magicCanvas.height = window.innerHeight;
}

window.addEventListener('resize', resizeMagic);
resizeMagic();

function drawStar(ctx, x, y, r, color, rot) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rot);
  ctx.fillStyle = color;
  ctx.beginPath();
  for (let i = 0; i < 5; i++) {
    const a = (i * 2 * Math.PI) / 5 - Math.PI / 2;
    const a2 = a + Math.PI / 5;
    ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    ctx.lineTo(Math.cos(a2) * r * 0.45, Math.sin(a2) * r * 0.45);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function startMagicParticles() {
  magicParticles = [];
  for (let i = 0; i < 70; i++) {
    magicParticles.push({
      angle: Math.random() * Math.PI * 2,
      radius: 90 + Math.random() * 240,
      speed: (0.2 + Math.random() * 0.7) * (Math.random() < 0.5 ? 1 : -1),
      size: 4 + Math.random() * 11,
      color: MAGIC_COLORS[Math.floor(Math.random() * MAGIC_COLORS.length)],
      type: Math.random() < 0.4 ? 'star' : 'dust',
      twinkle: Math.random() * Math.PI * 2,
      twinkleSpeed: 0.04 + Math.random() * 0.1,
      yOff: Math.random() * 40,
      vy: -0.2 - Math.random() * 0.5,
    });
  }
  if (!magicRunning) {
    magicRunning = true;
    renderMagic();
  }
}

function stopMagicParticles() {
  magicRunning = false;
  magicParticles = [];
  mctx.clearRect(0, 0, magicCanvas.width, magicCanvas.height);
}

function renderMagic() {
  if (!magicRunning) return;
  mctx.clearRect(0, 0, magicCanvas.width, magicCanvas.height);
  const cx = window.innerWidth / 2;
  const cy = window.innerHeight / 2;

  for (const p of magicParticles) {
    p.angle += p.speed * 0.02;
    p.twinkle += p.twinkleSpeed;
    p.yOff += p.vy;
    const x = cx + Math.cos(p.angle) * p.radius;
    const y = cy + Math.sin(p.angle) * p.radius + p.yOff;
    const alpha = 0.45 + 0.55 * Math.abs(Math.sin(p.twinkle));
    mctx.globalAlpha = Math.max(0.12, alpha);

    if (p.type === 'star') {
      drawStar(mctx, x, y, p.size, p.color, p.twinkle);
    } else {
      mctx.fillStyle = p.color;
      mctx.beginPath();
      mctx.arc(x, y, p.size * 0.4, 0, Math.PI * 2);
      mctx.fill();
    }

    if (p.yOff < -340) p.yOff = 40;
  }
  mctx.globalAlpha = 1;
  requestAnimationFrame(renderMagic);
}

function doFlash(cb) {
  flashEl.classList.remove('on');
  void flashEl.offsetWidth;
  flashEl.classList.add('on');
  if (cb) setTimeout(cb, 190);
}

export function koonMagicIn() {
  koon.classList.add('magic');
  requestAnimationFrame(() => {
    if (window.koonFit) window.koonFit();
  });
  magicCanvas.classList.add('on');
  startMagicParticles();
  playMagic();
}

export function koonMagicOut() {
  koon.classList.remove('magic');
  requestAnimationFrame(() => {
    if (window.koonFit) window.koonFit();
  });
  magicCanvas.classList.remove('on');
  stopMagicParticles();
}

// ==================== ANSWER ====================
export function sendAnswer() {
  const t = document.getElementById('answerText').value.trim();
  if (!t) return;
  if (ws) ws.send(JSON.stringify({ type: 'answer', text: t }));
  document.getElementById('answerText').value = '';
  statusEl.textContent = '...';
}

// ==================== OPERATOR ====================
export function op(action) {
  if (ws) ws.send(JSON.stringify({ type: 'op', action }));
}

document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  const map = {
    'r': 'replay',
    's': 'skip',
    'f': 'force_correct',
    'Escape': 'restart'
  };
  if (map[e.key]) op(map[e.key]);
});

// ==================== MIC TOGGLE (export) ====================
export { toggleMic, stopSTT };

// ==================== TEST MIC ====================
export function toggleTestMic() {
  if (getSpeechRecognition() && activeSTT) {
    stopSTT();
    return;
  }

  const btn = document.getElementById('testBtn');
  const out = document.getElementById('testOut');

  if (btn) {
    btn.classList.add('rec');
    btn.textContent = '⏹ Dừng';
  }

  if (out) {
    out.textContent = '👂 đang nghe...';
  }

  recognizeOnce({
    onInterim: (t) => {
      if (out) out.textContent = t ? `… ${t}` : '👂 đang nghe...';
    },
    onFinal: (text, engine) => {
      if (out) {
        out.innerHTML = text
          ? `✅ "<b>${text}</b>" <span class="eng">${engineLabel(engine)}</span>`
          : '⚠️ không nghe rõ — thử lại';
      }
    },
    onError: (e) => {
      if (out) out.textContent = `❌ lỗi: ${e}`;
    },
    onEnd: () => {
      if (btn) {
        btn.classList.remove('rec');
        btn.textContent = '🎤 Test mic';
      }
    }
  });
}

// ==================== DIAGNOSTIC ====================
export async function loadDiag() {
  const el = document.getElementById('engines');
  let tts = '…';
  let llm = '…';

  try {
    const h = await (await fetch('/health')).json();
    tts = h.tts ? `✅ Kokoro (${h.tts_voice})` : '❌ Kokoro chưa cài';
    llm = h.llm ? `✅ ${h.llm_model || 'OpenRouter'}` : '⚠️ Tắt (fuzzy match)';
  } catch (e) {
    tts = llm = '❌ server không phản hồi';
  }

  const SpeechRecognition = getSpeechRecognition();
  const sttBr = SpeechRecognition
    ? `✅ Web Speech API • ${browserName()}`
    : '⚠️ không hỗ trợ — cần Chrome/Edge';

  if (el) {
    el.innerHTML =
      `<div class="row">TTS: <b>${tts}</b></div>` +
      `<div class="row">LLM judge: <b>${llm}</b></div>` +
      `<div class="row">STT: <b>${sttBr}</b></div>`;
  }
}

export function toggleDiag() {
  const d = document.getElementById('diag');
  d.classList.toggle('show');
  if (d.classList.contains('show')) loadDiag();
}

// ==================== LIVE2D + LIP-SYNC ====================
let l2d = null;
const LIPSYNC_PARAM = 'ParamA';
let lipCtx = null;
let lipPcm = null;
let lipSr = 0;
let lipTotal = 0;
let lipUserTime = 0;
let lipOffset = 0;

export function koonHappy() {
  if (!l2d) return;
  try {
    l2d.model.expression('exp_05');
  } catch (e) {}
  try {
    l2d.model.motion('');
  } catch (e) {}
  setTimeout(() => {
    if (!l2d) return;
    try {
      l2d.model.motion('Idle');
    } catch (e) {}
  }, 3000);
}

async function initLive2D() {
  if (!window.PIXI || !window.PIXI.live2d || !window.Live2DCubismCore) {
    return console.warn('[Live2D] thiếu lib → giữ emoji 🦊');
  }

  const canvas = document.getElementById('koonCanvas');
  if (!canvas) return;

  try {
    const koonDiv = document.getElementById('koon');
    const W = koonDiv.clientWidth || 420;
    const H = koonDiv.clientHeight || 420;
    canvas.width = W;
    canvas.height = H;

    const app = new PIXI.Application({
      view: canvas,
      backgroundAlpha: 0,
      antialias: true,
      width: W,
      height: H
    });

    const model = await PIXI.live2d.Live2DModel.from('/live2d/mao_pro/runtime/mao_pro.model3.json');
    app.stage.addChild(model);

    const fit = () => {
      const cw = koonDiv.clientWidth || W;
      const ch = koonDiv.clientHeight || H;
      canvas.width = cw;
      canvas.height = ch;
      app.renderer.resize(cw, ch);
      const s = Math.min(cw / model.internalModel.width, ch / model.internalModel.height);
      model.scale.set(s * 1.8); // zoom 1.8x
      model.x = (cw - model.width) / 2;
      model.y = ch * 0.12; // shift xuống
    };

    fit();
    window.addEventListener('resize', fit);
    window.koonFit = fit; // expose để gọi khi KOON đổi kích thước

    try {
      model.motion('Idle');
    } catch (e) {}
    koon.classList.add('live2d');
    l2d = { app, model };

    const coreModel = model.internalModel.coreModel;
    let lastT = performance.now();

    model.internalModel.on('beforeModelUpdate', () => {
      const now = performance.now();
      let dts = (now - lastT) / 1000;
      lastT = now;
      if (dts > 0.1) dts = 0.1;

      let value = 0;
      if (lipPcm && lipOffset < lipTotal) {
        lipUserTime += dts;
        let goalOffset = Math.floor(lipUserTime * lipSr);
        if (goalOffset > lipTotal) goalOffset = lipTotal;

        let sum = 0;
        let cnt = 0;
        for (let i = lipOffset; i < goalOffset; i++) {
          sum += lipPcm[i] * lipPcm[i];
          cnt++;
        }
        const rms = cnt ? Math.sqrt(sum / cnt) : 0;
        lipOffset = goalOffset;
        value = Math.min(1.0, rms * 1.5);
      }

      try {
        coreModel.setParameterValueById(LIPSYNC_PARAM, value);
      } catch (e) {}
    });

    console.log('[Live2D] KOON = mao_pro, lip-sync OK');
  } catch (err) {
    console.warn('[Live2D] load lỗi → giữ emoji 🦊:', err && err.message || err);
  }
}

function ensureLipCtx() {
  if (lipCtx) return;
  try {
    lipCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (lipCtx.state === 'suspended') lipCtx.resume();
  } catch (e) {
    console.warn('[Live2D] tạo AudioContext lỗi:', e);
  }
}

async function decodeForLipSync(url) {
  if (!lipCtx) ensureLipCtx();
  try {
    const resp = await fetch(url);
    if (!resp.ok) return;
    const ab = await lipCtx.decodeAudioData(await resp.arrayBuffer());
    lipPcm = ab.getChannelData(0);
    lipSr = ab.sampleRate;
    lipTotal = lipPcm.length;
    lipUserTime = 0;
    lipOffset = 0;
  } catch (err) {
    // skip
  }
}

// ==================== GLOBAL EXPOSURE ====================
// Expose functions to global scope for HTML onclick handlers
window.startGame = startShow;
window.toggleMic = toggleMic;
window.toggleTestMic = toggleTestMic;
window.toggleDiag = toggleDiag;
window.sendAnswer = sendAnswer;
window.op = op;

// Initialize
initLive2D();
connectWebSocket();

// Export formatTime helper
function formatTime(t) {
  if (!isFinite(t) || t < 0) t = 0;
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
