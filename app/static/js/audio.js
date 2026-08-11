/**
 * Audio Module - Web Audio API sound effects
 * Chime sounds và audio effects shared cho cả 2 games
 */

let chimeCtx = null;

/**
 * Lấy hoặc tạo AudioContext
 */
function getChimeCtx() {
  if (!chimeCtx) {
    chimeCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (chimeCtx.state === 'suspended') {
    chimeCtx.resume();
  }
  return chimeCtx;
}

/**
 * Phát chime sound effect
 * @param {string} kind - Loại chime ('correct' | 'finale')
 */
export function playChime(kind) {
  try {
    const ctx = getChimeCtx();
    const now = ctx.currentTime;

    if (kind === 'correct') {
      // 3 nốt đi lên: C5→E5→G5 (ding ding ding vui)
      [523.25, 659.25, 783.99].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.value = freq;

        gain.gain.setValueAtTime(0.3, now + i * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.12 + 0.3);

        osc.connect(gain).connect(ctx.destination);
        osc.start(now + i * 0.12);
        osc.stop(now + i * 0.12 + 0.3);
      });
    } else if (kind === 'finale') {
      // 7 nốt — thang 7 màu, dài hơn
      [523.25, 587.33, 659.25, 698.46, 783.99, 880, 987.77].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.value = freq;

        gain.gain.setValueAtTime(0.22, now + i * 0.15);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.15 + 0.45);

        osc.connect(gain).connect(ctx.destination);
        osc.start(now + i * 0.15);
        osc.stop(now + i * 0.15 + 0.45);
      });
    }
  } catch (e) {
    // Audio fail = silent
    console.warn('Audio error:', e);
  }
}

/**
 * Phát magic sound effect (sparkle + swoosh)
 */
export function playMagic() {
  try {
    const ctx = getChimeCtx();
    const now = ctx.currentTime;

    // Sparkle: 4 nốt cao bay lên
    [784, 988, 1175, 1568].forEach((f, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.value = f;

      gain.gain.setValueAtTime(0.0001, now + i * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.2, now + i * 0.08 + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.5);

      osc.connect(gain).connect(ctx.destination);
      osc.start(now + i * 0.08);
      osc.stop(now + i * 0.08 + 0.5);
    });

    // Swoosh: noise bandpass quét tần số lên
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.5, ctx.sampleRate);
    const d = buf.getChannelData(0);

    for (let i = 0; i < d.length; i++) {
      d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    }

    const src = ctx.createBufferSource();
    src.buffer = buf;

    const flt = ctx.createBiquadFilter();
    flt.type = 'bandpass';
    flt.frequency.setValueAtTime(400, now);
    flt.frequency.exponentialRampToValueAtTime(3200, now + 0.4);
    flt.Q.value = 0.7;

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.16, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

    src.connect(flt).connect(gain).connect(ctx.destination);
    src.start(now);
    src.stop(now + 0.5);
  } catch (e) {
    console.warn('Magic sound error:', e);
  }
}

/**
 * Phát fanfare sound (7 nốt thang âm) cho winner
 */
export function playFanfare() {
  try {
    const ctx = getChimeCtx();
    const now = ctx.currentTime;

    // 7 nốt thang âm
    [523, 587, 659, 698, 784, 880, 988].forEach((f, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.value = f;

      gain.gain.setValueAtTime(0.22, now + i * 0.14);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.14 + 0.4);

      osc.connect(gain).connect(ctx.destination);
      osc.start(now + i * 0.14);
      osc.stop(now + i * 0.14 + 0.4);
    });
  } catch (e) {
    console.warn('Fanfare error:', e);
  }
}
