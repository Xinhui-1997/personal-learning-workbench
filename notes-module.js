const CFG = window.APP_CONFIG || {};
const BUCKET = 'learning-notes';
const MAX_IMAGES = 4;
const MAX_FILE_BYTES = 12 * 1024 * 1024;
const $ = id => document.getElementById(id);
const esc = (s = '') => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

let client = null;
let session = null;
let selectedDate = null;
let pendingImages = [];
let pendingAudio = null;
let pendingAudioUrl = null;
let recorder = null;
let recordStream = null;
let recordChunks = [];
let recordTimer = null;
let recordSeconds = 0;
let loadToken = 0;

function dateFromUI() {
  const text = $('dateText')?.textContent || '';
  const m = text.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (!m) return null;
  return `${m[1]}-${String(m[2]).padStart(2,'0')}-${String(m[3]).padStart(2,'0')}`;
}

function todayLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function dateCaption(date) {
  if (!date) return '这一天的记录';
  if (date === todayLocal()) return '今天留下的碎片';
  const [,m,d] = date.split('-');
  return `${Number(m)}月${Number(d)}日留下的碎片`;
}

function createPanel() {
  if ($('inspirationNotes')) return;
  const cards = $('cards');
  if (!cards) return;
  const section = document.createElement('section');
  section.id = 'inspirationNotes';
  section.className = 'notes-panel';
  section.innerHTML = `
    <div class="notes-head">
      <div>
        <div class="notes-kicker">✨ 灵感 & 小确幸</div>
        <div class="notes-subtitle">想到什么就随手放在这里，不算任务。</div>
      </div>
      <div class="notes-types"><span>文字</span><span>图片</span><span>语音</span></div>
    </div>

    <div class="notes-composer">
      <textarea id="noteText" rows="3" maxlength="1200" placeholder="记一句突然冒出来的想法、一件让你开心的小事，或者今天想留住的一个瞬间……"></textarea>
      <input id="noteImageInput" type="file" accept="image/*" multiple hidden>
      <div id="noteDraftMedia" class="note-draft-media hidden"></div>
      <div class="notes-toolbar">
        <div class="notes-tools">
          <button id="noteImageBtn" class="note-tool" type="button">🖼️ 图片</button>
          <button id="noteRecordBtn" class="note-tool" type="button">🎙️ 语音</button>
          <span id="noteStatus" class="note-status"></span>
        </div>
        <button id="noteSaveBtn" class="note-save" type="button">保存这一刻</button>
      </div>
    </div>

    <div class="notes-divider"></div>
    <div class="notes-list-head">
      <span id="notesDateCaption">今天留下的碎片</span>
      <span id="notesCount" class="notes-count">0 条</span>
    </div>
    <div id="notesList" class="notes-list"><div class="notes-empty">还没有记录。想到什么，就从上面随手留一点。</div></div>
  `;
  cards.parentNode.insertBefore(section, cards);

  $('noteImageBtn').addEventListener('click', () => $('noteImageInput').click());
  $('noteImageInput').addEventListener('change', onImagesPicked);
  $('noteRecordBtn').addEventListener('click', toggleRecording);
  $('noteSaveBtn').addEventListener('click', saveNote);
}

function setStatus(text, kind = '') {
  const el = $('noteStatus');
  if (!el) return;
  el.textContent = text || '';
  el.className = `note-status ${kind}`.trim();
}

function revokeDraftUrls() {
  pendingImages.forEach(x => x.preview && URL.revokeObjectURL(x.preview));
  if (pendingAudioUrl) URL.revokeObjectURL(pendingAudioUrl);
}

function clearDraft({ keepText = false } = {}) {
  revokeDraftUrls();
  pendingImages = [];
  pendingAudio = null;
  pendingAudioUrl = null;
  if (!keepText && $('noteText')) $('noteText').value = '';
  if ($('noteImageInput')) $('noteImageInput').value = '';
  renderDraftMedia();
}

function onImagesPicked(event) {
  const files = [...(event.target.files || [])];
  if (!files.length) return;
  const room = Math.max(0, MAX_IMAGES - pendingImages.length);
  if (!room) {
    setStatus(`每条最多放 ${MAX_IMAGES} 张图片`, 'warn');
    event.target.value = '';
    return;
  }
  let added = 0;
  for (const file of files.slice(0, room)) {
    if (!file.type.startsWith('image/')) continue;
    if (file.size > MAX_FILE_BYTES) {
      setStatus('单张图片请控制在 12 MB 以内', 'warn');
      continue;
    }
    pendingImages.push({ file, preview: URL.createObjectURL(file) });
    added++;
  }
  if (files.length > room) setStatus(`一次最多保留 ${MAX_IMAGES} 张图片`, 'warn');
  else if (added) setStatus('图片已放进草稿');
  event.target.value = '';
  renderDraftMedia();
}

function renderDraftMedia() {
  const box = $('noteDraftMedia');
  if (!box) return;
  const imageHTML = pendingImages.map((item, i) => `
    <div class="note-draft-thumb">
      <img src="${item.preview}" alt="待上传图片 ${i+1}">
      <button type="button" data-remove-image="${i}" aria-label="移除图片">×</button>
    </div>`).join('');
  const audioHTML = pendingAudioUrl ? `
    <div class="note-draft-audio">
      <span>🎧 语音草稿</span>
      <audio controls src="${pendingAudioUrl}"></audio>
      <button type="button" id="removeDraftAudio" aria-label="移除语音">×</button>
    </div>` : '';
  box.innerHTML = imageHTML + audioHTML;
  box.classList.toggle('hidden', !imageHTML && !audioHTML);
  box.querySelectorAll('[data-remove-image]').forEach(btn => btn.addEventListener('click', () => {
    const i = Number(btn.dataset.removeImage);
    const [removed] = pendingImages.splice(i, 1);
    if (removed?.preview) URL.revokeObjectURL(removed.preview);
    renderDraftMedia();
  }));
  $('removeDraftAudio')?.addEventListener('click', () => {
    if (pendingAudioUrl) URL.revokeObjectURL(pendingAudioUrl);
    pendingAudio = null;
    pendingAudioUrl = null;
    renderDraftMedia();
  });
}

function recordingMime() {
  const candidates = ['audio/webm;codecs=opus','audio/mp4','audio/webm','audio/ogg'];
  return candidates.find(t => window.MediaRecorder?.isTypeSupported?.(t)) || '';
}

function updateRecordButton() {
  const btn = $('noteRecordBtn');
  if (!btn) return;
  if (recorder && recorder.state === 'recording') {
    const mm = String(Math.floor(recordSeconds / 60)).padStart(2,'0');
    const ss = String(recordSeconds % 60).padStart(2,'0');
    btn.classList.add('recording');
    btn.textContent = `■ 停止 ${mm}:${ss}`;
  } else {
    btn.classList.remove('recording');
    btn.textContent = '🎙️ 语音';
  }
}

async function toggleRecording() {
  if (recorder && recorder.state === 'recording') {
    recorder.stop();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setStatus('这个浏览器暂不支持直接录音', 'error');
    return;
  }
  try {
    recordStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = recordingMime();
    recorder = mimeType ? new MediaRecorder(recordStream, { mimeType }) : new MediaRecorder(recordStream);
    recordChunks = [];
    recorder.ondataavailable = e => { if (e.data?.size) recordChunks.push(e.data); };
    recorder.onstop = () => {
      clearInterval(recordTimer);
      recordTimer = null;
      recordStream?.getTracks().forEach(t => t.stop());
      recordStream = null;
      if (recordChunks.length) {
        if (pendingAudioUrl) URL.revokeObjectURL(pendingAudioUrl);
        pendingAudio = new Blob(recordChunks, { type: recorder.mimeType || mimeType || 'audio/webm' });
        pendingAudioUrl = URL.createObjectURL(pendingAudio);
        setStatus('语音已放进草稿');
        renderDraftMedia();
      }
      recordSeconds = 0;
      updateRecordButton();
    };
    recorder.start();
    recordSeconds = 0;
    updateRecordButton();
    recordTimer = setInterval(() => { recordSeconds++; updateRecordButton(); }, 1000);
    setStatus('正在录音…', 'recording');
  } catch (err) {
    console.error(err);
    setStatus('没有获得麦克风权限，可以在浏览器地址栏重新允许', 'error');
  }
}

function extFor(type, fallback = 'bin') {
  const map = {
    'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/gif':'gif','image/heic':'heic','image/heif':'heif',
    'audio/webm':'webm','audio/mp4':'m4a','audio/mpeg':'mp3','audio/ogg':'ogg','audio/wav':'wav','audio/x-wav':'wav'
  };
  return map[type] || fallback;
}

async function uploadMedia(uid, date) {
  const uploaded = [];
  try {
    for (const item of pendingImages) {
      const path = `${uid}/${date}/${crypto.randomUUID()}.${extFor(item.file.type, 'img')}`;
      const { error } = await client.storage.from(BUCKET).upload(path, item.file, { contentType: item.file.type, upsert: false });
      if (error) throw error;
      uploaded.push({ type: 'image', path, mime: item.file.type, name: item.file.name || 'image' });
    }
    if (pendingAudio) {
      const mime = pendingAudio.type || 'audio/webm';
      const path = `${uid}/${date}/${crypto.randomUUID()}.${extFor(mime, 'audio')}`;
      const { error } = await client.storage.from(BUCKET).upload(path, pendingAudio, { contentType: mime, upsert: false });
      if (error) throw error;
      uploaded.push({ type: 'audio', path, mime, name: 'voice-note' });
    }
    return uploaded;
  } catch (err) {
    if (uploaded.length) await client.storage.from(BUCKET).remove(uploaded.map(x => x.path)).catch(()=>{});
    throw err;
  }
}

async function saveNote() {
  if (!client || !session) {
    setStatus('登录后才能保存并同步', 'error');
    return;
  }
  if (recorder?.state === 'recording') {
    setStatus('先停止录音，再保存这一刻', 'warn');
    return;
  }
  const date = dateFromUI();
  if (!date) return;
  const content = ($('noteText')?.value || '').trim();
  if (!content && !pendingImages.length && !pendingAudio) {
    setStatus('先写一句话，或者放一张图片 / 一段语音', 'warn');
    $('noteText')?.focus();
    return;
  }
  const btn = $('noteSaveBtn');
  btn.disabled = true;
  btn.textContent = '保存中…';
  setStatus('正在把这一刻收好…');
  let media = [];
  try {
    media = await uploadMedia(session.user.id, date);
    const { error } = await client.from('learning_notes').insert({
      user_id: session.user.id,
      note_date: date,
      content,
      media
    });
    if (error) throw error;
    clearDraft();
    setStatus('已保存 ✓', 'ok');
    await loadNotes();
    setTimeout(() => { if ($('noteStatus')?.textContent === '已保存 ✓') setStatus(''); }, 1800);
  } catch (err) {
    console.error(err);
    if (media.length) await client.storage.from(BUCKET).remove(media.map(x => x.path)).catch(()=>{});
    setStatus('保存失败了，请稍后再试', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '保存这一刻';
  }
}

async function signedMap(notes) {
  const paths = notes.flatMap(n => Array.isArray(n.media) ? n.media.map(m => m.path).filter(Boolean) : []);
  if (!paths.length) return new Map();
  const { data, error } = await client.storage.from(BUCKET).createSignedUrls(paths, 60 * 60);
  if (error || !data) return new Map();
  return new Map(data.map(x => [x.path, x.signedUrl]));
}

function formatTime(iso) {
  try {
    return new Intl.DateTimeFormat('zh-CN', { hour:'2-digit', minute:'2-digit', hour12:false }).format(new Date(iso));
  } catch { return ''; }
}

function renderNotes(notes, urls) {
  const list = $('notesList');
  if (!list) return;
  $('notesDateCaption').textContent = dateCaption(selectedDate);
  $('notesCount').textContent = `${notes.length} 条`;
  if (!notes.length) {
    list.innerHTML = '<div class="notes-empty">还没有记录。想到什么，就从上面随手留一点。</div>';
    return;
  }
  list.innerHTML = notes.map(note => {
    const media = Array.isArray(note.media) ? note.media : [];
    const images = media.filter(m => m.type === 'image' && urls.get(m.path)).map((m,i) => `<a class="note-image-link" href="${urls.get(m.path)}" target="_blank" rel="noopener"><img src="${urls.get(m.path)}" alt="记录图片 ${i+1}" loading="lazy"></a>`).join('');
    const audios = media.filter(m => m.type === 'audio' && urls.get(m.path)).map(m => `<div class="saved-audio"><span>🎙️</span><audio controls preload="metadata" src="${urls.get(m.path)}"></audio></div>`).join('');
    const content = note.content ? `<div class="note-text">${esc(note.content).replace(/\n/g,'<br>')}</div>` : '';
    return `<article class="saved-note" data-note-id="${note.id}">
      <div class="saved-note-top"><span>${formatTime(note.created_at)}</span><button type="button" class="note-delete" data-delete-note="${note.id}" aria-label="删除这条记录">删除</button></div>
      ${content}
      ${images ? `<div class="saved-images">${images}</div>` : ''}
      ${audios}
    </article>`;
  }).join('');
  list.querySelectorAll('[data-delete-note]').forEach(btn => btn.addEventListener('click', () => deleteNote(btn.dataset.deleteNote, notes)));
}

async function deleteNote(id, currentNotes) {
  const note = currentNotes.find(n => n.id === id);
  if (!note || !window.confirm('删除这条记录吗？')) return;
  const { error } = await client.from('learning_notes').delete().eq('id', id);
  if (error) {
    setStatus('删除失败，请稍后再试', 'error');
    return;
  }
  const paths = Array.isArray(note.media) ? note.media.map(m => m.path).filter(Boolean) : [];
  if (paths.length) client.storage.from(BUCKET).remove(paths).catch(()=>{});
  await loadNotes();
}

async function loadNotes() {
  if (!client) return;
  const date = dateFromUI();
  if (!date) return;
  selectedDate = date;
  $('notesDateCaption').textContent = dateCaption(date);
  const token = ++loadToken;
  const { data: authData } = await client.auth.getSession();
  session = authData.session;
  if (!session) {
    if (token === loadToken) $('notesList').innerHTML = '<div class="notes-empty">登录后，这里的记录会自动在电脑和手机之间同步。</div>';
    return;
  }
  const { data, error } = await client.from('learning_notes')
    .select('id,content,media,note_date,created_at')
    .eq('user_id', session.user.id)
    .eq('note_date', date)
    .order('created_at', { ascending: false });
  if (token !== loadToken) return;
  if (error) {
    console.error(error);
    $('notesList').innerHTML = '<div class="notes-empty">记录暂时没有加载出来，请刷新后再试。</div>';
    return;
  }
  const notes = data || [];
  const urls = await signedMap(notes);
  if (token !== loadToken) return;
  renderNotes(notes, urls);
}

function scheduleLoad() {
  clearTimeout(scheduleLoad.timer);
  scheduleLoad.timer = setTimeout(loadNotes, 120);
}

window.addEventListener('DOMContentLoaded', async () => {
  createPanel();
  const dateText = $('dateText');
  if (dateText) new MutationObserver(scheduleLoad).observe(dateText, { childList:true, characterData:true, subtree:true });
  if (!(CFG.SUPABASE_URL && CFG.SUPABASE_ANON_KEY)) return;
  try {
    const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
    client = createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY, { auth:{ persistSession:true, autoRefreshToken:true, detectSessionInUrl:true } });
    const { data } = await client.auth.getSession();
    session = data.session;
    client.auth.onAuthStateChange((_event, s) => { session = s; scheduleLoad(); });
    scheduleLoad();
  } catch (err) {
    console.error('notes module failed', err);
    setStatus('记事框暂时没有连上云端', 'error');
  }
});

window.addEventListener('beforeunload', () => {
  clearInterval(recordTimer);
  recordStream?.getTracks().forEach(t => t.stop());
  revokeDraftUrls();
});
