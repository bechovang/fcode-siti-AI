/**
 * STT Module - Speech-to-Text (Web Speech API)
 * Xử lý nhận diện giọng nói
 */

import { getSpeechRecognition, engineLabel } from './utils.js';

let activeSTT = null;

/**
 * Dừng STT nếu đang chạy
 */
export function stopSTT() {
  if (activeSTT) {
    activeSTT.stop();
  }
}

/**
 * Nhận diện giọng nói một lần
 * @param {Object} handlers - Callback handlers
 * @param {Function} handlers.onInterim - Callback khi có kết quả tạm thời
 * @param {Function} handlers.onFinal - Callback khi có kết quả cuối cùng
 * @param {Function} handlers.onError - Callback khi có lỗi
 * @param {Function} handlers.onEnd - Callback khi kết thúc
 * @returns {Object|null} Control object với method stop()
 */
export function recognizeOnce(handlers) {
  const SpeechRecognition = getSpeechRecognition();

  if (!SpeechRecognition) {
    const errorMsg = 'Trình duyệt không hỗ trợ Web Speech API — dùng Chrome hoặc Edge';
    handlers.onError?.(errorMsg);
    handlers.onEnd?.();
    return null;
  }

  const ctrl = {
    engine: 'web-speech',
    _rec: null,
    stop() {
      if (this._rec) {
        try {
          this._rec.stop();
        } catch (e) {
          // Ignore stop errors
        }
      }
    }
  };

  activeSTT = ctrl;

  try {
    const r = new SpeechRecognition();
    r.lang = 'vi-VN';
    r.continuous = false;
    r.interimResults = true;

    ctrl._rec = r;

    r.onstart = () => {
      handlers.onInterim?.('');
    };

    r.onresult = (e) => {
      let interim = '';
      let final = '';

      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) {
          final = res[0].transcript;
        } else {
          interim += res[0].transcript;
        }
      }

      if (final) {
        handlers.onFinal?.(final.trim(), 'web-speech');
      } else if (interim) {
        handlers.onInterim?.(interim);
      }
    };

    r.onerror = (ev) => {
      handlers.onError?.(ev.error);
    };

    r.onend = () => {
      activeSTT = null;
      handlers.onEnd?.();
    };

    r.start();
  } catch (err) {
    activeSTT = null;
    handlers.onError?.(`start: ${err.message}`);
    handlers.onEnd?.();
  }

  return ctrl;
}

/**
 * Toggle mic (bật/tắt microphone)
 * @param {Object} options - Options
 * @param {HTMLElement} options.btn - Button element
 * @param {HTMLElement} options.statusEl - Status display element
 * @param {HTMLElement} options.sttHeardEl - STT heard display element
 * @param {Function} options.onResult - Callback khi có kết quả
 * @returns {Function} Stop function
 */
export function toggleMic({ btn, statusEl, sttHeardEl, onResult }) {
  if (activeSTT) {
    stopSTT();
    return () => {}; // Already stopped
  }

  if (btn) {
    btn.classList.add('rec');
    btn.textContent = '⏹ Dừng';
  }

  if (statusEl) {
    statusEl.textContent = '👂 đang nghe...';
  }

  if (sttHeardEl) {
    sttHeardEl.classList.remove('show');
  }

  recognizeOnce({
    onInterim: (t) => {
      if (statusEl) {
        statusEl.textContent = t ? `… ${t}` : '👂 đang nghe...';
      }
      if (sttHeardEl && t) {
        sttHeardEl.textContent = `KOON nghe được: "${t}"`;
        sttHeardEl.classList.add('show');
      }
    },
    onFinal: (text, engine) => {
      if (statusEl) {
        statusEl.textContent = text ? `bé nói: "${text}"` : '(không nghe rõ — thử lại)';
      }
      if (sttHeardEl && text) {
        sttHeardEl.textContent = `KOON nghe được: "${text}"`;
        sttHeardEl.classList.add('show');
      }
      if (text && onResult) {
        onResult(text, engine);
      }
      if (sttHeardEl) {
        setTimeout(() => sttHeardEl.classList.remove('show'), 4000);
      }
    },
    onError: (e) => {
      if (statusEl) {
        statusEl.textContent = `lỗi STT: ${e}${e === 'not-allowed' ? ' (cấp quyền mic cho site)' : ''}`;
      }
    },
    onEnd: () => {
      if (btn) {
        btn.classList.remove('rec');
        btn.textContent = '🎤 Mic';
      }
    }
  });

  // Return stop function
  return () => stopSTT();
}
