const NAV_MODULES=[
  {id:'task',label:'今日小事',cls:'task-c'},
  {id:'english',label:'Daily English',cls:'english-c'},
  {id:'physics',label:'每日物理',cls:'physics-c'},
  {id:'psych',label:'每日心理',cls:'psych-c'},
  {id:'science',label:'每日科普',cls:'science-c'},
  {id:'poetry',label:'每日诗词',cls:'poetry-c'}
];

function jumpToModule(index){
  const mod=NAV_MODULES[index];
  if(!mod)return;
  const target=document.querySelector(`.card.${mod.cls}`);
  if(!target)return;
  target.scrollIntoView({behavior:'smooth',block:'start'});
  target.animate([
    {boxShadow:'0 0 0 0 rgba(91,130,230,0)'},
    {boxShadow:'0 0 0 5px rgba(91,130,230,.13)'},
    {boxShadow:'0 9px 28px rgba(30,43,70,.055)'}
  ],{duration:850,easing:'ease-out'});
}

function wireProgressNavigation(){
  document.querySelectorAll('#segments .segment').forEach((el,index)=>{
    const mod=NAV_MODULES[index];
    if(!mod)return;
    el.setAttribute('role','button');
    el.setAttribute('tabindex','0');
    el.setAttribute('aria-label',`跳转到${mod.label}`);
    el.title=`跳转到${mod.label}`;
    el.onclick=()=>jumpToModule(index);
    el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();jumpToModule(index)}};
  });

  document.querySelectorAll('#segmentLabels > *').forEach((el,index)=>{
    const mod=NAV_MODULES[index];
    if(!mod)return;
    el.classList.add('segment-label');
    el.setAttribute('role','button');
    el.setAttribute('tabindex','0');
    el.title=`跳转到${mod.label}`;
    el.onclick=()=>jumpToModule(index);
    el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();jumpToModule(index)}};
  });
}

function addBackToTop(){
  if(document.getElementById('backToTop'))return;
  const btn=document.createElement('button');
  btn.id='backToTop';
  btn.className='back-to-top';
  btn.type='button';
  btn.setAttribute('aria-label','回到顶部');
  btn.title='回到顶部';
  btn.textContent='↑';
  btn.onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
  document.body.appendChild(btn);

  const update=()=>btn.classList.toggle('show',window.scrollY>420);
  window.addEventListener('scroll',update,{passive:true});
  update();
}

function enhance(){
  wireProgressNavigation();
  addBackToTop();
}

const observer=new MutationObserver(mutations=>{
  if(mutations.some(m=>m.target.id==='segments'||m.target.id==='segmentLabels'||m.target.id==='cards')){
    requestAnimationFrame(wireProgressNavigation);
  }
});

window.addEventListener('DOMContentLoaded',()=>{
  enhance();
  const root=document.getElementById('todayView');
  if(root)observer.observe(root,{childList:true,subtree:true});
});
