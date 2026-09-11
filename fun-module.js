const CFG = window.APP_CONFIG || {};
const CORE_MODULES = new Set(['task','english','physics','psych','science','poetry','weekend_read']);
const esc = (s = '') => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let client = null;
let syncing = false;
let pending = false;

function dateFromUI() {
  const text = document.getElementById('dateText')?.textContent || '';
  const m = text.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (!m) return null;
  return `${m[1]}-${String(m[2]).padStart(2,'0')}-${String(m[3]).padStart(2,'0')}`;
}

function humanMeta(raw, fallback = '约 10–30 秒') {
  if (!raw) return fallback;
  if (typeof raw === 'object') return raw.duration || raw.reading_time || fallback;
  const text = String(raw).trim();
  if (!text.startsWith('{')) return text || fallback;
  try {
    const obj = JSON.parse(text);
    return [obj.duration, obj.language].filter(Boolean).join(' · ') || fallback;
  } catch { return fallback; }
}

function lockedCard(done) {
  const remaining = Math.max(0, 3 - done);
  return `<section class="card fun-c reward-locked" data-fun-card="1">
    <div class="card-head"><div><div class="kicker">😄 每日开心一刻</div><h2>今日彩蛋待解锁</h2><div class="meta">奖励模块 · 不计入今日进度</div></div><div class="reward-badge">🔒</div></div>
    <div class="locked-reward"><div class="lock-icon">🎁</div><strong>再完成 ${remaining} 个模块就能打开</strong><p>完成任意 3 个学习模块后，今天的开心一刻会自动出现。</p><div class="reward-progress">${[0,1,2].map(i=>`<span class="${i<Math.min(done,3)?'filled':''}"></span>`).join('')}</div></div>
  </section>`;
}

function unlockedCard(card) {
  const title = card.source_url
    ? `<a class="original-link" href="${esc(card.source_url)}" target="_blank" rel="noopener">${esc(card.title)}<span class="external"> ↗ 来源</span></a>`
    : esc(card.title);
  return `<section class="card fun-c" data-fun-card="1">
    <div class="card-head"><div><div class="kicker">😄 每日开心一刻</div><h2>${title}</h2><div class="meta">${esc(humanMeta(card.meta))} · 已解锁 🎉</div></div></div>
    ${card.body_html || ''}
    <div class="source-row"><div class="source-info">${esc(card.source_name || '')}</div><span class="reward-note">今天的奖励，不增加任务数</span></div>
  </section>`;
}

async function syncFun() {
  if (syncing || !client) { pending = true; return; }
  const date = dateFromUI();
  const cardsEl = document.getElementById('cards');
  if (!date || !cardsEl) return;
  syncing = true;
  pending = false;
  try {
    const { data: sessionData } = await client.auth.getSession();
    const session = sessionData.session;
    if (!session) return;
    const [{ data: fun, error: funError }, { data: rows, error: rowsError }] = await Promise.all([
      client.from('daily_cards').select('title,body_html,meta,source_name,source_url').eq('study_date', date).eq('module', 'fun').maybeSingle(),
      client.from('completion').select('module,completed').eq('study_date', date).eq('user_id', session.user.id).eq('completed', true)
    ]);
    if (funError || rowsError || !fun) return;
    const done = (rows || []).filter(r => CORE_MODULES.has(r.module)).length;
    cardsEl.querySelector('[data-fun-card="1"]')?.remove();
    cardsEl.insertAdjacentHTML('beforeend', done >= 3 ? unlockedCard(fun) : lockedCard(done));
  } finally {
    syncing = false;
    if (pending) setTimeout(syncFun, 80);
  }
}

function scheduleSync() {
  pending = true;
  clearTimeout(scheduleSync.timer);
  scheduleSync.timer = setTimeout(syncFun, 120);
}

window.addEventListener('DOMContentLoaded', async () => {
  if (!(CFG.SUPABASE_URL && CFG.SUPABASE_ANON_KEY)) return;
  try {
    const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
    client = createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } });
    const cards = document.getElementById('cards');
    const dateText = document.getElementById('dateText');
    if (cards) new MutationObserver(scheduleSync).observe(cards, { childList: true, subtree: false });
    if (dateText) new MutationObserver(scheduleSync).observe(dateText, { childList: true, characterData: true, subtree: true });
    client.auth.onAuthStateChange(scheduleSync);
    scheduleSync();
  } catch (err) {
    console.error('fun module failed', err);
  }
});
