/**
 * Utils Module - Utility functions shared cho cả 2 games
 */

/**
 * Lấy tên browser đang sử dụng
 * @returns {string} Tên browser
 */
export function browserName() {
  const ua = navigator.userAgent;
  if (/Edg\//.test(ua)) return 'Edge • Azure';
  if (/OPR\//.test(ua) || /Opera/.test(ua)) return 'Opera';
  if (/Chrome\//.test(ua)) return 'Chrome • Google';
  if (/Firefox\//.test(ua)) return 'Firefox';
  if (/Safari\//.test(ua)) return 'Safari';
  return 'browser';
}

/**
 * Kiểm tra Web Speech API support
 * @returns {boolean} Có hỗ trợ hay không
 */
export function supportsSpeechRecognition() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

/**
 * Lấy label cho engine STT
 * @param {string} engine - Engine type
 * @returns {string} Label hiển thị
 */
export function engineLabel(engine) {
  const STT_BROWSER = supportsSpeechRecognition()
    ? `Web Speech API • ${browserName()}`
    : null;

  return engine === 'web-speech' ? STT_BROWSER : (engine || '?');
}

/**
 * Format thời gian hiển thị
 * @param {number} t - Thời gian (giây)
 * @returns {string} Format "m:ss"
 */
export function formatTime(t) {
  if (!isFinite(t) || t < 0) t = 0;
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

/**
 * Lấy Speech Recognition constructor
 * @returns {SpeechRecognition|webkitSpeechRecognition|null} Constructor hoặc null
 */
export function getSpeechRecognition() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}
