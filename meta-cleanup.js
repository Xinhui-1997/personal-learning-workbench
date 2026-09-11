function humanizeMeta(text) {
  const raw = String(text || '').trim();
  if (!raw || (!raw.startsWith('{') && !raw.startsWith('['))) return null;
  try {
    const obj = JSON.parse(raw);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null;
    const parts = [];
    const add = value => {
      const s = value == null ? '' : String(value).trim();
      if (s && !parts.includes(s)) parts.push(s);
    };
    add(obj.duration);
    add(obj.reading_time);
    add(obj.language);
    add(obj.published_date);
    add(obj.published_at);
    if (obj.free_read === true) add('免费可读');
    return parts.length ? parts.join(' · ') : null;
  } catch {
    const parts = [];
    const pick = key => {
      const m = raw.match(new RegExp(`"${key}"\\s*:\\s*"([^"]+)"`));
      if (m && !parts.includes(m[1])) parts.push(m[1]);
    };
    pick('duration');
    pick('reading_time');
    pick('language');
    pick('published_date');
    return parts.length ? parts.join(' · ') : null;
  }
}

function cleanVisibleMeta(root = document) {
  root.querySelectorAll?.('.card .meta').forEach(el => {
    const cleaned = humanizeMeta(el.textContent);
    if (cleaned) el.textContent = cleaned;
  });
}

window.addEventListener('DOMContentLoaded', () => {
  const cards = document.getElementById('cards');
  cleanVisibleMeta();
  if (!cards) return;
  new MutationObserver(() => cleanVisibleMeta(cards)).observe(cards, { childList: true, subtree: true });
});
