/**
 * Confetti Module - Hiệu ứng confetti shared cho cả 2 games
 */

/**
 * Tạo confetti effect
 * @param {number} count - Số lượng confetti pieces
 * @param {Array<string>} colorSet - Mảng colors (optional)
 */
export function burstConfetti(count, colorSet) {
  const canvas = document.getElementById('confettiCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let pieces = [];
  let running = false;

  // Mặc định colors với pastel palette
  const colors = colorSet || [
    '#FF6B6B', '#FFA500', '#FFD93D', '#6BCF7F',
    '#4ECDC4', '#A78BFA', '#F06595', '#FFF', '#FFD700'
  ];

  // Resize canvas
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  // Tạo confetti pieces
  for (let i = 0; i < count; i++) {
    pieces.push({
      x: window.innerWidth / 2 + (Math.random() - 0.5) * 300,
      y: window.innerHeight * 0.2,
      vx: (Math.random() - 0.5) * 14,
      vy: -Math.random() * 16 - 4,
      w: 4 + Math.random() * 8,
      h: 4 + Math.random() * 8,
      color: colors[Math.floor(Math.random() * colors.length)],
      rot: Math.random() * 360,
      rotV: (Math.random() - 0.5) * 8,
      life: 1,
      decay: 0.004 + Math.random() * 0.008,
    });
  }

  if (!running) {
    running = true;
    renderConfetti();
  }

  function renderConfetti() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces = pieces.filter(p => p.life > 0);

    for (const p of pieces) {
      p.x += p.vx;
      p.vy += 0.22; // gravity
      p.y += p.vy;
      p.rot += p.rotV;
      p.life -= p.decay;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot * Math.PI / 180);
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
      ctx.restore();
    }

    if (pieces.length > 0) {
      requestAnimationFrame(renderConfetti);
    } else {
      running = false;
    }
  }
}

/**
 * Xóa tất cả confetti
 */
export function clearConfetti() {
  const canvas = document.getElementById('confettiCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// Auto-resize khi window resize
window.addEventListener('resize', () => {
  const canvas = document.getElementById('confettiCanvas');
  if (canvas) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
});
