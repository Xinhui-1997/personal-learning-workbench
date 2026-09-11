const CFG=window.APP_CONFIG||{};
const BASE=[
{id:'task',label:'今日小事',icon:'🌱',cls:'task-c'},
{id:'english',label:'Daily English',icon:'🇬🇧',cls:'english-c'},
{id:'physics',label:'每日物理',icon:'⚛️',cls:'physics-c'},
{id:'psych',label:'每日心理',icon:'🧠',cls:'psych-c'},
{id:'science',label:'每日科普',icon:'🔭',cls:'science-c'},
{id:'poetry',label:'每日诗词',icon:'📜',cls:'poetry-c'},
{id:'weekend_read',label:'周六短读',icon:'📖',cls:'weekend-c'}];
const BONUS={id:'fun',label:'每日开心一刻',icon:'😄',cls:'fun-c'};
const ALL_MODULES=BASE.filter(m=>CFG.SHOW_DAILY_TASK!==false||m.id!=='task');
const $=id=>document.getElementById(id);
let supabase=null,session=null,currentDate=fmt(new Date()),calendarCursor=parse(currentDate),cards=[],completion={},installPrompt=null;
const configured=!!(CFG.SUPABASE_URL&&CFG.SUPABASE_ANON_KEY);
function parse(s){const[y,m,d]=s.split('-').map(Number);return new Date(y,m-1,d)}
function fmt(d){return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function add(s,n){const d=parse(s);d.setDate(d.getDate()+n);return fmt(d)}
function wday(d){return ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'][d.getDay()]}
function showDate(s){const d=parse(s);return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 ${wday(d)}`}
function weekStart(s){const d=parse(s),x=(d.getDay()+6)%7;d.setDate(d.getDate()-x);return fmt(d)}
function modulesForDate(d){return parse(d).getDay()===6?ALL_MODULES:ALL_MODULES.filter(m=>m.id!=='weekend_read')}
function lk(d){return `plw-completion-${d}`}
function localRead(d){try{return JSON.parse(localStorage.getItem(lk(d)))||{}}catch{return{}}}
function localWrite(d,v){localStorage.setItem(lk(d),JSON.stringify(v))}
function qread(){try{return JSON.parse(localStorage.getItem('plw-sync-queue'))||[]}catch{return[]}}
function qwrite(v){localStorage.setItem('plw-sync-queue',JSON.stringify(v))}
function esc(s=''){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function displayMeta(raw,fallback='约 1–2 分钟'){
 if(raw==null||raw==='')return fallback;
 const fromObject=obj=>{
  if(!obj||typeof obj!=='object'||Array.isArray(obj))return fallback;
  const parts=[];
  const addPart=v=>{if(v!=null&&String(v).trim()&&!parts.includes(String(v).trim()))parts.push(String(v).trim())};
  addPart(obj.duration);addPart(obj.reading_time);addPart(obj.language);addPart(obj.published_date);addPart(obj.published_at);
  if(obj.free_read===true)addPart('免费可读');
  return parts.length?parts.join(' · '):fallback;
 };
 if(typeof raw==='object')return fromObject(raw);
 const text=String(raw).trim();
 if(!text)return fallback;
 if(!text.startsWith('{')&&!text.startsWith('['))return text;
 try{return fromObject(JSON.parse(text))}catch{return fallback}
}
function coreDoneCount(){return modulesForDate(currentDate).filter(m=>completion[m.id]).length}

async function init(){setupUI();setupPWA();if(configured)await setupSupabase();await load(currentDate)}
function setupUI(){
 document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
 $('prevDay').onclick=()=>load(add(currentDate,-1));$('nextDay').onclick=()=>load(add(currentDate,1));$('todayBtn').onclick=()=>load(fmt(new Date()));
 $('calendarBtn').onclick=e=>toggleCalendar(e);$('calPrev').onclick=()=>moveMonth(-1);$('calNext').onclick=()=>moveMonth(1);
 document.addEventListener('click',()=>$('calendarPop').classList.remove('open'));window.addEventListener('online',flushQueue);renderSources();
 const notice=$('languageNotice');if(notice&&$('todayView'))$('todayView').appendChild(notice);
}
function setupPWA(){if('serviceWorker'in navigator)navigator.serviceWorker.register('./sw.js').catch(()=>{});window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installPrompt=e;$('installBtn').classList.remove('hidden')});$('installBtn').onclick=async()=>{if(!installPrompt)return;installPrompt.prompt();await installPrompt.userChoice;installPrompt=null;$('installBtn').classList.add('hidden')}}
async function setupSupabase(){
 const {createClient}=await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
 supabase=createClient(CFG.SUPABASE_URL,CFG.SUPABASE_ANON_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
 const r=await supabase.auth.getSession();session=r.data.session;
 supabase.auth.onAuthStateChange((_e,s)=>{session=s;if(session){$('loginOverlay').classList.add('hidden');subscribe();flushQueue();load(currentDate)}});
 if(!session&&CFG.REQUIRE_LOGIN!==false)$('loginOverlay').classList.remove('hidden');badge();if(session)subscribe();
}
async function load(d){currentDate=d;$('dateText').textContent=showDate(d);const t=fmt(new Date());$('dateNote').textContent=d===t?'今天':d<t?'过去':'未来';calendarCursor=parse(d);cards=await fetchCards(d);completion=await fetchCompletion(d);renderProgress();renderCards()}
async function fetchCards(d){if(supabase&&session){const {data,error}=await supabase.from('daily_cards').select('*').eq('study_date',d).order('module');if(!error)return data||[]}return []}
async function fetchCompletion(d){if(supabase&&session){const {data,error}=await supabase.from('completion').select('module,completed').eq('study_date',d).eq('user_id',session.user.id);if(!error){const o={};(data||[]).forEach(r=>o[r.module]=r.completed);localWrite(d,o);return o}}return localRead(d)}
function renderProgress(){const active=modulesForDate(currentDate),cols=`repeat(${active.length},1fr)`;$('segments').style.gridTemplateColumns=cols;$('segmentLabels').style.gridTemplateColumns=cols;$('segments').innerHTML=active.map(m=>`<div class="segment ${m.id} ${completion[m.id]?'done':''}"></div>`).join('');$('segmentLabels').innerHTML=active.map(m=>`<span>${m.label}</span>`).join('');$('progressText').textContent=`今日完成 ${active.filter(m=>completion[m.id]).length} / ${active.length}`}
function renderCards(){if(!cards.length){$('cards').innerHTML=`<div class="empty"><div class="emoji">🗓️</div><strong>${showDate(currentDate)}</strong><br>这一天还没有内容。</div>`;return}const active=modulesForDate(currentDate),by=Object.fromEntries(cards.map(c=>[c.module,c]));const regular=active.filter(m=>by[m.id]).map(m=>card(m,by[m.id])).join('');const bonus=by[BONUS.id]?funCard(by[BONUS.id]):'';$('cards').innerHTML=regular+bonus;document.querySelectorAll('[data-complete]').forEach(b=>b.onclick=()=>toggleComplete(b.dataset.complete))}
function card(m,d){const title=d.source_url?`<a class="original-link" href="${esc(d.source_url)}" target="_blank" rel="noopener">${esc(d.title)}<span class="external"> ↗ 原文</span></a>`:esc(d.title);const score=d.score==null?'':`<div class="score">Score ${Math.round(d.score)}</div>`;const fallback=m.id==='task'?'30–60 秒':m.id==='poetry'?'约 3–5 分钟':'约 1–2 分钟';return `<section class="card ${m.cls}"><div class="card-head"><div><div class="kicker">${m.icon} ${m.label}</div><h2>${title}</h2><div class="meta">${esc(displayMeta(d.meta,fallback))}</div></div>${score}</div>${d.body_html||''}<div class="source-row"><div class="source-info">${esc(d.source_name||'')}</div><button class="complete-btn ${completion[m.id]?'done':''}" data-complete="${m.id}">${completion[m.id]?'✓ 已完成':'标记完成'}</button></div></section>`}
function funCard(d){
 const done=coreDoneCount(),unlocked=done>=3,remaining=Math.max(0,3-done);
 if(!unlocked)return `<section class="card ${BONUS.cls} reward-locked"><div class="card-head"><div><div class="kicker">${BONUS.icon} ${BONUS.label}</div><h2>今日彩蛋待解锁</h2><div class="meta">奖励模块 · 不计入今日进度</div></div><div class="reward-badge">🔒</div></div><div class="locked-reward"><div class="lock-icon">🎁</div><strong>再完成 ${remaining} 个模块就能打开</strong><p>完成任意 3 个学习模块后，今天的开心一刻会自动出现。</p><div class="reward-progress">${Array.from({length:3},(_,i)=>`<span class="${i<Math.min(done,3)?'filled':''}"></span>`).join('')}</div></div></section>`;
 const title=d.source_url?`<a class="original-link" href="${esc(d.source_url)}" target="_blank" rel="noopener">${esc(d.title)}<span class="external"> ↗ 来源</span></a>`:esc(d.title);
 return `<section class="card ${BONUS.cls}"><div class="card-head"><div><div class="kicker">${BONUS.icon} ${BONUS.label}</div><h2>${title}</h2><div class="meta">${esc(displayMeta(d.meta,'约 10–30 秒'))} · 已解锁 🎉</div></div></div>${d.body_html||''}<div class="source-row"><div class="source-info">${esc(d.source_name||'')}</div><span class="reward-note">今天的奖励，不增加任务数</span></div></section>`;
}
async function toggleComplete(module){const next=!completion[module];completion[module]=next;localWrite(currentDate,completion);renderProgress();renderCards();if(!(supabase&&session))return;setBadge('syncing');const payload={user_id:session.user.id,study_date:currentDate,module,completed:next,updated_at:new Date().toISOString()};const {error}=await supabase.from('completion').upsert(payload,{onConflict:'user_id,study_date,module'});if(error){const q=qread();q.push(payload);qwrite(q);setBadge('offline')}else setBadge('synced')}
async function flushQueue(){if(!(supabase&&session))return;const q=qread();if(!q.length){setBadge('synced');return}setBadge('syncing');const remain=[];for(const x of q){const {error}=await supabase.from('completion').upsert({...x,user_id:session.user.id},{onConflict:'user_id,study_date,module'});if(error)remain.push(x)}qwrite(remain);setBadge(remain.length?'offline':'synced')}
function setBadge(mode){const e=$('syncBadge');e.className=`sync-badge ${mode}`;e.textContent=mode==='synced'?'已同步':mode==='syncing'?'同步中':'离线待同步';$('modeText').textContent=session?'云端同步已启用':'等待登录'}
function badge(){setBadge(navigator.onLine?'synced':'offline')}
function subscribe(){if(!(supabase&&session)||window._plwSubscribed)return;window._plwSubscribed=true;supabase.channel('completion-live').on('postgres_changes',{event:'*',schema:'public',table:'completion',filter:`user_id=eq.${session.user.id}`},p=>{if(p.new?.study_date===currentDate){completion[p.new.module]=p.new.completed;localWrite(currentDate,completion);renderProgress();renderCards()}}).subscribe()}
function toggleCalendar(e){e.stopPropagation();const p=$('calendarPop'),open=!p.classList.contains('open');if(open){renderCalendar();p.classList.add('open')}else p.classList.remove('open')}
function moveMonth(n){calendarCursor=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()+n,1);renderCalendar()}
function renderCalendar(){const y=calendarCursor.getFullYear(),m=calendarCursor.getMonth();$('calMonthTitle').textContent=`${y}年${m+1}月`;const first=new Date(y,m,1),idx=(first.getDay()+6)%7,start=new Date(y,m,1-idx),today=fmt(new Date());let h='';for(let i=0;i<42;i++){const d=new Date(start);d.setDate(start.getDate()+i);const ds=fmt(d),cls=['cal-day',d.getMonth()===m?'':'muted',ds===today?'today':'',ds===currentDate?'selected':''].filter(Boolean).join(' ');h+=`<button class="${cls}" data-date="${ds}">${d.getDate()}</button>`}$('calGrid').innerHTML=h;$('calGrid').querySelectorAll('[data-date]').forEach(b=>b.onclick=()=>{$('calendarPop').classList.remove('open');load(b.dataset.date)})}
function switchView(v){['today','stats','sources'].forEach(x=>$(x+'View').classList.toggle('hidden',x!==v));document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.view===v));if(v==='stats')renderStats()}
async function getRange(start,end){if(supabase&&session){const {data,error}=await supabase.from('completion').select('study_date,module,completed').eq('user_id',session.user.id).gte('study_date',start).lte('study_date',end);if(!error)return data||[]}return[]}
async function renderStats(){
 const today=fmt(new Date()),ws=weekStart(today),we=add(ws,6),start=add(today,-60),rows=await getRange(start,today);
 const truth=rows.filter(r=>r.completed&&modulesForDate(r.study_date).some(m=>m.id===r.module)),by={};truth.forEach(r=>(by[r.study_date]??=[]).push(r.module));
 let streak=0,c=today;while((by[c]||[]).length){streak++;c=add(c,-1)}
 const dates=Array.from({length:7},(_,i)=>add(ws,i)),week=truth.filter(r=>r.study_date>=ws&&r.study_date<=we),slots=dates.reduce((n,d)=>n+modulesForDate(d).length,0),rate=slots?Math.round(week.length/slots*100):0;
 $('streakNum').textContent=streak;$('totalNum').textContent=truth.length;$('weekRate').textContent=rate+'%';$('statsDateRange').textContent=`${ws} — ${we}`;$('donut').style.setProperty('--pct',rate);$('donutText').textContent=rate+'%';
 const regular=modulesForDate(ws).length;$('weekDescription').textContent=`平日 ${regular} 个学习栏目，周六加一篇「周六短读」；「每日开心一刻」是完成 3 个模块后的奖励，不计入进度。`;
 const cols=`100px repeat(7,1fr) 54px`;$('dayHead').style.gridTemplateColumns=cols;$('dayHead').innerHTML='<span></span>'+['一','二','三','四','五','六','日'].map(x=>`<span>${x}</span>`).join('')+'<span></span>';
 $('moduleRows').innerHTML=ALL_MODULES.map(m=>{const activeDates=dates.filter(d=>modulesForDate(d).some(x=>x.id===m.id)),dots=dates.map(d=>{const active=modulesForDate(d).some(x=>x.id===m.id);return `<span class="day-dot ${active?'':'inactive'} ${active&&(by[d]||[]).includes(m.id)?'done':''}"></span>`}).join(''),n=activeDates.filter(d=>(by[d]||[]).includes(m.id)).length,den=activeDates.length;return `<div class="module-row ${m.id}" style="grid-template-columns:${cols}"><span class="module-name">${m.label}</span>${dots}<span class="module-rate">${den?Math.round(n/den*100):0}%</span></div>`}).join('');
 const hdates=Array.from({length:14},(_,i)=>add(today,-13+i));$('heatmap').innerHTML=hdates.map(d=>{const expected=modulesForDate(d).length,n=(by[d]||[]).length,r=expected?n/expected:0,l=n===0?0:r<=.34?1:r<=.67?2:r<1?3:4;return `<div class="heat" data-level="${l}" title="${d}: ${n}/${expected}">${parse(d).getDate()}</div>`).join('')
}
function renderSources(){const pools=[
['🇬🇧 Daily English',[['China Daily 英语点津','中英双语','https://language.chinadaily.com.cn/news_bilingual'],['News in Levels','分级简单英文','https://www.newsinlevels.com/'],['VOA Learning English','学习者英语','https://learningenglish.voanews.com/']]],
['⚛️ 每日物理',[['中科院物理所·物理学咬文嚼字','中文高质量长期题库','https://www.iop.cas.cn/kxcb/kpwz/ywjzzl/'],['Physics World','高质量英文，入选后转中文','https://physicsworld.com/']]],
['🧠 每日心理',[['中国科学院心理研究所','中文研究进展与科普','https://www.psych.cas.cn/'],['Greater Good','英文心理学，入选后转中文','https://greatergood.berkeley.edu/']]],
['🔭 每日科普',[['中国科普博览','中文科学内容','https://www.kepu.net.cn/'],['Science News Explores','青少年英文科普','https://www.snexplores.org/']]],
['📜 每日诗词',[['经典文学选库','古诗、古词、古文名篇与适合展示的现代诗；优先经典，不走小学启蒙路线','']]],
['📖 周六短读',[['近两周人物 / 思想 / 文化文章','只在周六出现；免费可读，优先 5–10 分钟，先核实发布日期与原文链接','']]],
['😄 每日开心一刻',[['轻松奖励内容','冷笑话、热笑话、谐音梗或有趣小事；干净、不低俗，完成 3 个学习模块后解锁','']]]
];$('sourceCards').innerHTML=pools.map(([t,items])=>`<section class="source-card"><h3>${t}</h3>${items.map(([n,d,u])=>`<div class="source-item">${u?`<a href="${u}" target="_blank" rel="noopener">${n} ↗</a>`:`<strong>${n}</strong>`}<p>${d}</p></div>`).join('')}</section>`).join('')}
init().catch(err=>{console.error(err);$('cards').innerHTML=`<div class="empty">加载失败：${esc(err.message||String(err))}</div>`});
