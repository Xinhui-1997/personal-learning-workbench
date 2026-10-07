#!/usr/bin/env python3
import html
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:1.7b"

RSS = {
    "physics": ("https://physicsworld.com/feed/", "Physics World"),
    "psych": ("https://greatergood.berkeley.edu/site/rss/articles", "Greater Good Science Center · UC Berkeley"),
    "science": ("https://www.snexplores.org/feed/", "Science News Explores"),
}

BLOCK = {
    "english": ["war","election","president","minister","military","killed","murder","execution","prison",
                "sexual","rape","assault","drug","money","salary","rent","house prices","inflation","protest"],
    "physics": ["nobel","prize","award","wins ","winner","obituary","dies at","quiz","puzzle","podcast",
                "interview","jobs","career","salary","festival season","high spirits"],
    "psych": ["sexual","rape","assault","violence","suicide","self-harm","abuse","grief","authoritarian",
              "election","politic","war","trauma","calendar"],
    "science": ["quiz","subscription","sponsored"],
}

PREFER = {
    "english": ["animal","nature","science","technology","culture","education","language","city","travel",
                "food","environment","space","history","japan"],
    "physics": ["quantum","material","particle","laser","light","magnet","energy","fluid","atom","space",
                "temperature","superconduct","experiment","physics","electron","neutrino","gravity","photon"],
    "psych": ["attention","memory","stress","emotion","empathy","compassion","relationship","sleep","awe",
              "gratitude","mindful","happiness","learning","motivation","creativity","habit","connection",
              "kindness","well-being","consciousness"],
    "science": ["science","animal","space","earth","climate","ocean","chemistry","brain","technology","plant",
                "physics","material","energy"],
}

META = {
    "english": "约 1–2 分钟 · 中英双语",
    "physics": "约 1–2 分钟 · 中文",
    "psych": "约 1–2 分钟 · 中文",
    "science": "约 1–2 分钟 · 中文",
}

def fetch(url, timeout=30):
    req = urllib.request.Request(
        url,
        headers={"User-Agent":"personal-learning-workbench/1.0","Accept":"text/html,application/rss+xml,application/xml,*/*"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def clean(raw):
    if not raw:
        return ""
    soup = BeautifulSoup(html.unescape(str(raw)), "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    text = re.sub(r"\s*The post .*? appeared first on .*?\.?\s*$", "", text, flags=re.I)
    text = re.sub(r"\s*Continue reading.*$", "", text, flags=re.I)
    text = re.sub(r"\s*Read more\.?\s*$", "", text, flags=re.I)
    return text.strip()

def sentences(text, n=2, chars=520):
    text=clean(text)
    parts=re.split(r"(?<=[.!?])\s+", text)
    out=[]; total=0
    for p in parts:
        p=p.strip()
        if not p: continue
        if out and total+len(p)>chars: break
        out.append(p); total+=len(p)
        if len(out)>=n: break
    return " ".join(out)[:chars].strip()

def summary(entry):
    for k in ("summary","description","subtitle"):
        t=sentences(entry.get(k),2,520)
        if len(t)>=35: return t
    for block in entry.get("content") or []:
        t=sentences(block.get("value"),2,520)
        if len(t)>=35: return t
    return ""

def dt_from(entry):
    st=entry.get("published_parsed") or entry.get("updated_parsed")
    if not st: return None
    try:
        return datetime(st.tm_year,st.tm_mon,st.tm_mday,st.tm_hour,st.tm_min,st.tm_sec,tzinfo=timezone.utc)
    except Exception: return None

def age(dt):
    return 999 if not dt else max(0,(datetime.now(timezone.utc)-dt).days)

def blocked(module,text):
    low=text.lower()
    return any(x in low for x in BLOCK[module])

def pick_rss(module):
    feed_url, source_name=RSS[module]
    parsed=feedparser.parse(fetch(feed_url))
    candidates=[]
    for e in parsed.entries[:35]:
        title=clean(e.get("title"))
        sm=summary(e)
        link=e.get("link","")
        if not title or not link.startswith(("http://","https://")): continue
        hay=title+" "+sm
        if blocked(module,hay): continue
        if len(sm)<70: continue
        d=dt_from(e); days=age(d)
        score=max(0,35-min(days,35)) + sum(6 for x in PREFER[module] if x in hay.lower())
        if 100<=len(sm)<=430: score+=20
        if module=="physics" and len(sm)<110: score-=25
        candidates.append({
            "title_en":title,"summary_en":sm,"source_url":link,"source_name":source_name,
            "published":d.isoformat() if d else "","age_days":days,"score":score
        })
    if not candidates:
        raise RuntimeError(f"{module}: no suitable RSS candidate")
    candidates.sort(key=lambda x:x["score"],reverse=True)
    return candidates[0],candidates[:5]

def parse_nil(url):
    soup=BeautifulSoup(fetch(url),"html.parser")
    title=""
    for tag in soup.find_all(["h1","h2"]):
        t=clean(tag.get_text(" ",strip=True))
        if "level 2" in t.lower():
            title=re.sub(r"\s*[–-]\s*level\s*2\s*$","",t,flags=re.I).strip(); break
    if not title: return None

    raw=soup.get_text("\n")
    dm=re.search(r"\b(\d{2})-(\d{2})-(\d{4})\s+\d{2}:\d{2}\b",raw)
    d=None
    if dm:
        day,mon,year=map(int,dm.groups()); d=datetime(year,mon,day,tzinfo=timezone.utc)

    # Prefer actual paragraph tags after title. This preserves sentence punctuation better.
    paras=[]
    seen_title=False
    for tag in soup.find_all(["h1","h2","p"]):
        t=clean(tag.get_text(" ",strip=True))
        if not t: continue
        if tag.name in ("h1","h2") and "level 2" in t.lower():
            seen_title=True; continue
        if not seen_title: continue
        low=t.lower()
        if low.startswith("difficult words:") or low.startswith("learn 3000 words"): break
        if re.fullmatch(r"\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}",t): continue
        if len(t)>=45: paras.append(t)
        if len(paras)>=3: break

    body=sentences(" ".join(paras),2,450)
    if len(body)<70: return None

    difficult=[]
    for tag in soup.find_all(["p","div"]):
        t=clean(tag.get_text(" ",strip=True))
        if not t.lower().startswith("difficult words:"): continue
        payload=t.split(":",1)[1]
        for term,definition in re.findall(r"([^,()]{2,40})\s*\(([^()]{3,180})\)",payload):
            term=term.strip(" ,:;"); definition=definition.strip()
            if term and definition: difficult.append((term,definition))
            if len(difficult)>=3: break
        if difficult: break

    return {"title_en":title,"summary_en":body,"source_url":url,"source_name":"News in Levels · Level 2",
            "published":d.isoformat() if d else "","age_days":age(d),"difficult_words":difficult}

def pick_english():
    home="https://www.newsinlevels.com/"
    soup=BeautifulSoup(fetch(home),"html.parser")
    urls=[]; seen=set()
    for a in soup.find_all("a",href=True):
        if clean(a.get_text(" ",strip=True)).lower()!="level 2": continue
        u=urljoin(home,a["href"])
        if "/products/" not in u or u in seen: continue
        seen.add(u); urls.append(u)
    candidates=[]
    for order,u in enumerate(urls[:18]):
        try: item=parse_nil(u)
        except Exception: continue
        if not item: continue
        hay=item["title_en"]+" "+item["summary_en"]
        if blocked("english",hay) or item["age_days"]>30: continue
        s=120-order*3 + max(0,20-min(item["age_days"],20))
        s+=sum(7 for x in PREFER["english"] if x in hay.lower())
        item["score"]=s
        candidates.append(item)
    if not candidates: raise RuntimeError("english: no suitable News in Levels candidate")
    candidates.sort(key=lambda x:x["score"],reverse=True)
    return candidates[0],candidates[:5]

def translate_exact(text):
    payload={
        "model":MODEL,"stream":False,"think":False,
        "messages":[
            {"role":"system","content":
             "Translate English to natural Simplified Chinese. Return ONLY the Chinese translation, with no label, no quotation marks, no explanation, and no extra text. "
             "Do not summarize, expand, omit facts, add examples, or add background knowledge. "
             "Preserve all numbers, proper nouns, scientific terms, qualifiers, uncertainty words, and sentence meaning."},
            {"role":"user","content":text}
        ],
        "options":{"temperature":0.0,"num_predict":600}
    }
    req=urllib.request.Request(
        OLLAMA_URL,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST"
    )
    with urllib.request.urlopen(req,timeout=240) as r:
        raw=json.load(r)
    out=clean(raw.get("message",{}).get("content",""))
    out=re.sub(r"^(?:翻译|译文|中文翻译)\s*[:：]\s*","",out).strip()
    if not out:
        raise RuntimeError("empty translation")
    if len(out) > max(80, len(text)*3):
        raise RuntimeError("translation unexpectedly long")
    compact_out = out.replace(",", "")
    compact_src = text.replace(",", "")
    for num in re.findall(r"\d+(?:\.\d+)?", compact_src):
        if num in compact_out:
            continue
        try:
            value=float(num)
        except ValueError:
            raise RuntimeError(f"translation dropped number {num}")
        alternatives=[]
        if value.is_integer() and int(value)>=10000 and int(value)%10000==0:
            alternatives.append(f"{int(value)//10000}万")
        if value.is_integer() and int(value)>=100000000 and int(value)%100000000==0:
            alternatives.append(f"{int(value)//100000000}亿")
        if not any(a in compact_out for a in alternatives):
            raise RuntimeError(f"translation dropped number {num}")
    return out

def esc(s): return html.escape(s or "",quote=True)

def build(module,item):
    title_zh=translate_exact(item["title_en"])
    sm_zh=translate_exact(item["summary_en"])
    if module=="english":
        vocab=[]
        for term,definition in item.get("difficult_words",[])[:3]:
            vocab.append((term,translate_exact(definition)))
        body=(f'<div class="callout"><strong>先看中文：</strong>{esc(sm_zh)}</div>'
              f'<p><strong>Today’s English</strong></p><p>{esc(item["summary_en"])}</p>')
        if vocab:
            body+='<div class="vocab"><strong>3 个词 / 表达</strong><ul>'
            body+="".join(f'<li><strong>{esc(t)}</strong> — {esc(m)}</li>' for t,m in vocab)
            body+='</ul></div>'
        body+=f'<div class="callout"><strong>跟读一句：</strong>{esc(sentences(item["summary_en"],1,190))}</div>'
        title=item["title_en"]
    elif module=="physics":
        body=(f'<div class="callout"><strong>今天讲什么：</strong>{esc(title_zh)}</div><p>{esc(sm_zh)}</p>'
              '<p><em>只依据来源摘要整理，没有补充摘要之外的新事实；点击标题可阅读原文。</em></p>')
        title=title_zh
    elif module=="psych":
        body=(f'<div class="callout"><strong>今天的心理学材料：</strong>{esc(title_zh)}</div><p>{esc(sm_zh)}</p>'
              '<p><em>这里只翻译文章来源摘要，不用于个人诊断，也不把群体研究结论当作个人保证。</em></p>')
        title=title_zh
    else:
        body=(f'<div class="callout"><strong>今天的原来如此：</strong>{esc(sm_zh)}</div>'
              '<p><em>内容只来自来源摘要，没有增加摘要之外的新事实。</em></p>')
        title=title_zh
    return {"module":module,"title":title,"body_html":body,"meta":META[module],
            "source_name":item["source_name"],"source_url":item["source_url"]}

def main():
    out=Path("test-output-qwen-translate"); out.mkdir(exist_ok=True)
    selected={}; tops={}; failures=[]; timings={}
    for module in ["english","physics","psych","science"]:
        t=time.time()
        try:
            item,top=(pick_english() if module=="english" else pick_rss(module))
            selected[module]=item; tops[module]=top; timings[module+"_select"]=round(time.time()-t,2)
            print(f"[select] {module}: {item['title_en']} | score={item['score']} | age={item['age_days']}d",flush=True)
        except Exception as e:
            failures.append({"module":module,"stage":"select","error":str(e)})
    cards=[]
    for module,item in selected.items():
        t=time.time()
        try:
            cards.append(build(module,item)); timings[module+"_translate"]=round(time.time()-t,2)
        except Exception as e:
            failures.append({"module":module,"stage":"translate","error":str(e)})
            print(f"[translate] {module} FAILED: {e}",flush=True)
    (out/"cards.json").write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"debug.json").write_text(json.dumps({"selected":selected,"top_candidates":tops,"failures":failures,"timings":timings},
                                            ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"report.txt").write_text("\n".join([
        f"model={MODEL}",f"cards={len(cards)}/4",f"failures={len(failures)}",
        f"timings={json.dumps(timings,ensure_ascii=False)}",
        f"failure_details={json.dumps(failures,ensure_ascii=False)}"
    ])+"\n",encoding="utf-8")
    if len(cards)!=4: raise SystemExit(1)

if __name__=="__main__":
    main()
