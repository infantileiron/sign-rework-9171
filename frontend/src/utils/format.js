export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
}
export const fixed = (number, digits = 2) => Number(number).toFixed(digits);
export const signed = number => `${number > 0 ? '+' : ''}${fixed(number, 4)}`;
export function timecode(minutes) {
  const seconds = Math.round(minutes * 60);
  return `${String(Math.floor(seconds / 3600)).padStart(2, '0')}:${String(Math.floor(seconds / 60) % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}
