#!/usr/bin/env python3
import html
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup

MODEL_NAME = "Helsinki-NLP/opus-mt-en-zh"

SOURCE_POOLS = {
    "english": [
        {
            "feed": "https://learningenglish.voanews.com/api/zoroqql-vomx-tpeptpqq",
            "source_name": "VOA Learning English · Everyday Grammar",
            "source_priority": 40,
        },
        {
            "feed": "https://learningenglish.voanews.com/api/zkm-ql-vomx-tpej-rqi",
            "source_name": "VOA Learning English · As It Is",
            "source_priority": 30,
        },
        {
            "feed": "https://learningenglish.voanews.com/api/z_goqvl-vomx-tpevmmqt",
            "source_name": "VOA Learning English · What's Trending Today",
            "source_priority": 20,
        },
        {
            "feed": "https://learningenglish.voanews.com/api/zmg_pl-vomx-tpeymtm",
            "source_name": "VOA Learning English · Science & Technology",
            "source_priority": 10,
        },
    ],
    "physics": [
        {
            "feed": "https://physicsworld.com/feed/",
            "source_name": "Physics World",
            "source_priority": 20,
        }
    ],
    "psych": [
        {
            "feed": "https://greatergood.berkeley.edu/site/rss/articles",
            "source_name": "Greater Good Science Center · UC Berkeley",
            "source_priority": 20,
        }
    ],
    "science": [
        {
            "feed": "https://www.snexplores.org/feed/",
            "source_name": "Science News Explores",
            "source_priority": 20,
        }
    ],
}

META = {
    "english": "约 1–2 分钟 · 中英双语",
    "physics": "约 1–2 分钟 · 中文",
    "psych": "约 1–2 分钟 · 中文",
    "science": "约 1–2 分钟 · 中文",
}

BLOCK = {
    "english": [
        "war", "election", "president", "minister", "military", "killed", "murder",
        "sexual", "rape", "assault",
    ],
    "physics": [
        "nobel", "prize", "award", "wins ", "winner", "obituary", "dies at",
        "quiz", "podcast", "interview", "jobs", "career", "salary",
    ],
    "psych": [
        "sexual", "rape", "assault", "violence", "suicide", "self-harm", "abuse",
        "grief", "authoritarian", "election", "politic", "war", "trauma",
    ],
    "science": [
        "quiz", "subscription", "sponsored",
    ],
}

PREFER = {
    "english": [
        "grammar", "word", "phrase", "language", "learn", "science", "technology",
        "culture", "education", "study", "everyday",
    ],
    "physics": [
        "quantum", "material", "particle", "laser", "light", "magnet", "energy",
        "fluid", "wave", "atom", "space", "temperature", "superconduct",
        "experiment", "physics", "electron", "neutrino", "gravity",
    ],
    "psych": [
        "attention", "memory", "stress", "emotion", "empathy", "compassion",
        "relationship", "sleep", "awe", "gratitude", "mindful", "happiness",
        "learning", "motivation", "creativity", "habit", "connection",
        "kindness", "well-being", "consciousness",
    ],
    "science": [
        "science", "animal", "space", "earth", "climate", "ocean", "chemistry",
        "brain", "technology", "plant", "physics", "material", "energy",
    ],
}

STOPWORDS = {
    "the","a","an","and","or","but","for","to","of","in","on","at","by","with","from",
    "as","is","are","was","were","be","been","being","that","this","these","those","it",
    "its","their","our","your","you","we","they","he","she","his","her","about","into",
    "over","under","after","before","more","most","new","how","why","what","when","where",
    "can","could","may","might","will","would","should","than","ago","has","have","had",
}

def fetch(url, timeout=30):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "personal-learning-workbench/1.0 (+https://github.com/Xinhui-1997/personal-learning-workbench)",
            "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def clean_text(raw):
    if not raw:
        return ""
    soup = BeautifulSoup(html.unescape(str(raw)), "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common WordPress-style RSS boilerplate without touching article facts.
    text = re.sub(
        r"\s*The post .*? appeared first on .*?\.?\s*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\s*Continue reading.*$", "", text, flags=re.I)
    text = re.sub(r"\s*Read more\.?\s*$", "", text, flags=re.I)
    return text.strip()

def first_sentences(text, max_sentences=2, max_chars=520):
    text = clean_text(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out, total = [], 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if total + len(part) > max_chars and out:
            break
        out.append(part)
        total += len(part)
        if len(out) >= max_sentences:
            break
    return " ".join(out).strip()[:max_chars].rstrip()

def entry_summary(entry):
    candidates = [
        entry.get("summary"),
        entry.get("description"),
        entry.get("subtitle"),
    ]
    for candidate in candidates:
        text = first_sentences(candidate, 2, 520)
        if len(text) >= 35:
            return text
    content = entry.get("content") or []
    if isinstance(content, list):
        for block in content:
            text = first_sentences(block.get("value", ""), 2, 520)
            if len(text) >= 35:
                return text
    return ""

def valid_http_url(url):
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False

def published_datetime(entry):
    stamp = entry.get("published_parsed") or entry.get("updated_parsed")
    if stamp:
        try:
            return datetime(
                stamp.tm_year, stamp.tm_mon, stamp.tm_mday,
                stamp.tm_hour, stamp.tm_min, stamp.tm_sec,
                tzinfo=timezone.utc,
            )
        except Exception:
            pass
    return None

def age_days(dt):
    if not dt:
        return 999
    now = datetime.now(timezone.utc)
    return max(0, (now - dt).days)

def score_entry(module, entry, source_priority):
    title = clean_text(entry.get("title", ""))
    summary = entry_summary(entry)
    link = entry.get("link", "")
    if not title or not valid_http_url(link) or len(summary) < 35:
        return None

    hay = (title + " " + summary).lower()
    if any(term in hay for term in BLOCK[module]):
        return None
    if any(term in hay for term in ["podcast", "video:", "watch:", "quiz of the week"]):
        return None

    dt = published_datetime(entry)
    days = age_days(dt)

    # English must not silently fall back to a years-old dormant feed.
    if module == "english" and days > 90:
        return None

    score = source_priority
    score += max(0, 35 - min(days, 35))
    score += sum(5 for term in PREFER[module] if term in hay)

    # Prefer snippets with enough substance but avoid huge feed bodies.
    if 70 <= len(summary) <= 420:
        score += 15
    elif len(summary) > 420:
        score += 5

    return {
        "score": score,
        "title_en": title,
        "summary_en": summary,
        "source_url": link,
        "published": dt.isoformat() if dt else "",
        "age_days": days,
    }

def pick_best(module):
    candidates = []
    errors = []
    for source in SOURCE_POOLS[module]:
        try:
            feed_bytes = fetch(source["feed"])
            parsed = feedparser.parse(feed_bytes)
            if parsed.bozo and not parsed.entries:
                raise RuntimeError(str(parsed.bozo_exception))
            for entry in parsed.entries[:30]:
                scored = score_entry(module, entry, source["source_priority"])
                if scored:
                    scored["source_name"] = source["source_name"]
                    scored["feed"] = source["feed"]
                    candidates.append(scored)
        except Exception as exc:
            errors.append(f"{source['feed']}: {exc}")

    if not candidates:
        raise RuntimeError(f"{module}: no usable candidates; errors={errors}")

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0], candidates[:5]

class MarianTranslator:
    def __init__(self):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        self.model.eval()

    def translate(self, text):
        text = clean_text(text)
        if not text:
            return ""
        # This multilingual-target Marian model expects the target-language token.
        source = ">>cmn_Hans<< " + text
        inputs = self.tokenizer(
            source,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        with self.torch.no_grad():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=300,
                num_beams=4,
                do_sample=False,
                early_stopping=True,
            )
        out = self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        return polish_zh(out)

def polish_zh(text):
    text = clean_text(text)
    text = text.replace(",", "，").replace(".", "。")
    text = text.replace(" ?", "？").replace(" !", "！")
    text = re.sub(r"\s+([，。！？；：])", r"\1", text)
    text = re.sub(r"([，。！？；：])\s+", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def esc(text):
    return html.escape(text or "", quote=True)

def candidate_phrases(text, limit=3):
    tokens = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)*", text)
    runs = []
    current = []
    for tok in tokens:
        low = tok.lower()
        if low in STOPWORDS:
            if current:
                runs.append(current)
                current = []
            continue
        current.append(tok)
    if current:
        runs.append(current)

    scored = []
    seen = set()
    for run in runs:
        # Drop leading proper names from content runs.
        while run and run[0][0].isupper():
            run = run[1:]
        if not run:
            continue
        for width in (3, 2, 1):
            if len(run) < width:
                continue
            for i in range(len(run) - width + 1):
                chunk = run[i:i+width]
                phrase = " ".join(chunk)
                key = phrase.lower()
                if key in seen or len(phrase) < 6:
                    continue
                seen.add(key)
                content_score = width * 10 + sum(len(x) for x in chunk)
                if "-" in phrase:
                    content_score += 4
                scored.append((content_score, phrase))
    scored.sort(reverse=True)
    return [p for _, p in scored[:limit]]

def build_card(module, item, tr):
    title_zh = tr.translate(item["title_en"])
    summary_zh = tr.translate(item["summary_en"])

    if module == "english":
        phrases = candidate_phrases(item["summary_en"], 3)
        vocab = [(p, tr.translate(p)) for p in phrases]
        follow = first_sentences(item["summary_en"], 1, 180)
        body = (
            f'<div class="callout"><strong>先看中文：</strong>{esc(summary_zh)}</div>'
            f'<p><strong>Today’s English</strong></p>'
            f'<p>{esc(item["summary_en"])}</p>'
        )
        if vocab:
            body += '<div class="vocab"><strong>3 个词 / 表达</strong><ul>'
            body += "".join(
                f"<li><strong>{esc(p)}</strong> — {esc(m)}</li>" for p, m in vocab
            )
            body += "</ul></div>"
        body += f'<div class="callout"><strong>跟读一句：</strong>{esc(follow)}</div>'
        title = item["title_en"]
    elif module == "physics":
        body = (
            f'<div class="callout"><strong>今天讲什么：</strong>{esc(title_zh)}</div>'
            f'<p>{esc(summary_zh)}</p>'
            '<p><em>只依据来源 RSS 摘要整理；需要更完整的机制和背景时，点标题进入原文。</em></p>'
        )
        title = title_zh
    elif module == "psych":
        body = (
            f'<div class="callout"><strong>今天的心理学材料：</strong>{esc(title_zh)}</div>'
            f'<p>{esc(summary_zh)}</p>'
            '<p><em>这里只呈现文章来源摘要，不用于个人诊断，也不把群体研究结论当作个人保证。</em></p>'
        )
        title = title_zh
    else:
        body = (
            f'<div class="callout"><strong>今天的原来如此：</strong>{esc(summary_zh)}</div>'
            '<p><em>内容只来自来源 RSS 摘要，没有增加摘要之外的新事实。</em></p>'
        )
        title = title_zh

    return {
        "module": module,
        "title": title,
        "body_html": body,
        "meta": META[module],
        "source_name": item["source_name"],
        "source_url": item["source_url"],
    }

def main():
    start = time.time()
    out_dir = Path("test-output-marian")
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = {}
    top_candidates = {}
    failures = []
    fetch_timings = {}

    for module in ["english", "physics", "psych", "science"]:
        t0 = time.time()
        try:
            item, top = pick_best(module)
            selected[module] = item
            top_candidates[module] = top
            fetch_timings[module] = round(time.time() - t0, 2)
            print(
                f"[select] {module}: {item['title_en']} | "
                f"{item['source_name']} | age={item['age_days']}d | score={item['score']}",
                flush=True,
            )
        except Exception as exc:
            failures.append({"module": module, "stage": "select", "error": str(exc)})
            print(f"[select] {module} FAILED: {exc}", flush=True)

    model_t0 = time.time()
    translator = MarianTranslator()
    model_load_seconds = round(time.time() - model_t0, 2)

    cards = []
    translate_timings = {}
    for module, item in selected.items():
        t0 = time.time()
        try:
            cards.append(build_card(module, item, translator))
            translate_timings[module] = round(time.time() - t0, 2)
        except Exception as exc:
            failures.append({"module": module, "stage": "translate", "error": str(exc)})
            print(f"[translate] {module} FAILED: {exc}", flush=True)

    (out_dir / "cards.json").write_text(
        json.dumps(cards, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "debug.json").write_text(
        json.dumps(
            {
                "model": MODEL_NAME,
                "selected": selected,
                "top_candidates": top_candidates,
                "failures": failures,
                "fetch_timings_seconds": fetch_timings,
                "model_load_seconds": model_load_seconds,
                "translate_timings_seconds": translate_timings,
                "total_seconds": round(time.time() - start, 2),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "report.txt").write_text(
        "\n".join([
            f"model={MODEL_NAME}",
            f"cards={len(cards)}/4",
            f"failures={len(failures)}",
            f"fetch_timings={json.dumps(fetch_timings, ensure_ascii=False)}",
            f"model_load_seconds={model_load_seconds}",
            f"translate_timings={json.dumps(translate_timings, ensure_ascii=False)}",
            f"total_seconds={round(time.time() - start, 2)}",
            f"failure_details={json.dumps(failures, ensure_ascii=False)}",
        ]) + "\n",
        encoding="utf-8",
    )

    if len(cards) != 4:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
