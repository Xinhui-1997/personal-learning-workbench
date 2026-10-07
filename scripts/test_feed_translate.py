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

SOURCES = {
    "english": {
        "feed": "https://learningenglish.voanews.com/api/zmg_pl-vomx-tpeymtm",
        "source_name": "VOA Learning English · Science & Technology",
        "meta": "约 1–2 分钟 · 中英双语",
    },
    "physics": {
        "feed": "https://physicsworld.com/feed/",
        "source_name": "Physics World",
        "meta": "约 1–2 分钟 · 中文",
    },
    "psych": {
        "feed": "https://greatergood.berkeley.edu/site/rss/articles",
        "source_name": "Greater Good Science Center · UC Berkeley",
        "meta": "约 1–2 分钟 · 中文",
    },
    "science": {
        "feed": "https://www.snexplores.org/feed/",
        "source_name": "Science News Explores",
        "meta": "约 1–2 分钟 · 中文",
    },
}

STOPWORDS = {
    "the","a","an","and","or","but","for","to","of","in","on","at","by","with","from",
    "as","is","are","was","were","be","been","being","that","this","these","those","it",
    "its","their","our","your","you","we","they","he","she","his","her","about","into",
    "over","under","after","before","more","most","new","how","why","what","when","where",
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
    return text

def first_sentences(text, max_sentences=2, max_chars=520):
    text = clean_text(text)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    total = 0
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
    joined = " ".join(out).strip()
    return joined[:max_chars].rstrip()

def entry_summary(entry):
    candidates = [
        entry.get("summary"),
        entry.get("description"),
        entry.get("subtitle"),
    ]
    for candidate in candidates:
        text = first_sentences(candidate, max_sentences=2, max_chars=520)
        if len(text) >= 40:
            return text

    content = entry.get("content") or []
    if isinstance(content, list):
        for block in content:
            text = first_sentences(block.get("value", ""), max_sentences=2, max_chars=520)
            if len(text) >= 40:
                return text
    return ""

def valid_http_url(url):
    try:
        p = urlparse(url)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False

def pick_entry(feed_bytes, module):
    parsed = feedparser.parse(feed_bytes)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"{module}: feed parse failed: {parsed.bozo_exception}")
    if not parsed.entries:
        raise RuntimeError(f"{module}: no feed entries")

    rejected = []
    for entry in parsed.entries[:20]:
        title = clean_text(entry.get("title", ""))
        link = entry.get("link", "")
        summary = entry_summary(entry)
        if not title or not valid_http_url(link) or len(summary) < 40:
            rejected.append(title or "(untitled)")
            continue

        # Avoid video-only / podcast-like items in the reading cards.
        haystack = (title + " " + summary).lower()
        if any(word in haystack for word in ["podcast", "video:", "watch:", "quiz of the week"]):
            rejected.append(title)
            continue

        published = clean_text(
            entry.get("published")
            or entry.get("updated")
            or entry.get("dc_date")
            or ""
        )
        return {
            "title_en": title,
            "summary_en": summary,
            "source_url": link,
            "published": published,
        }

    raise RuntimeError(f"{module}: no usable feed item; rejected={rejected[:6]}")

def ensure_argos_en_zh():
    import argostranslate.package
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    has_en = any(lang.code == "en" for lang in installed)
    has_zh = any(lang.code == "zh" for lang in installed)
    if has_en and has_zh:
        try:
            src = next(lang for lang in installed if lang.code == "en")
            dst = next(lang for lang in installed if lang.code == "zh")
            if src.get_translation(dst):
                return
        except Exception:
            pass

    argostranslate.package.update_package_index()
    packages = argostranslate.package.get_available_packages()
    candidates = [
        p for p in packages
        if p.from_code == "en" and p.to_code == "zh"
    ]
    if not candidates:
        raise RuntimeError("No Argos en→zh package found in package index")

    package = candidates[0]
    path = package.download()
    argostranslate.package.install_from_path(path)

def zh(text):
    import argostranslate.translate
    text = clean_text(text)
    if not text:
        return ""
    return argostranslate.translate.translate(text, "en", "zh").strip()

def choose_phrases(text, limit=3):
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", text)
    phrases = []
    seen = set()

    # Prefer compact adjacent two-word phrases that contain content words.
    for i in range(len(words) - 1):
        pair = words[i:i+2]
        low = [w.lower() for w in pair]
        if all(w in STOPWORDS for w in low):
            continue
        phrase = " ".join(pair)
        key = phrase.lower()
        if key in seen or len(phrase) < 7:
            continue
        seen.add(key)
        phrases.append(phrase)
        if len(phrases) >= limit:
            return phrases

    for word in words:
        low = word.lower()
        if low in STOPWORDS or len(word) < 6 or low in seen:
            continue
        seen.add(low)
        phrases.append(word)
        if len(phrases) >= limit:
            break
    return phrases

def esc(text):
    return html.escape(text or "", quote=True)

def build_card(module, source_cfg, item):
    title_zh = zh(item["title_en"])
    summary_zh = zh(item["summary_en"])

    if module == "english":
        phrases = choose_phrases(item["summary_en"], 3)
        vocab = []
        for phrase in phrases:
            try:
                meaning = zh(phrase)
            except Exception:
                meaning = ""
            vocab.append((phrase, meaning))

        first_sentence = first_sentences(item["summary_en"], max_sentences=1, max_chars=180)
        body = (
            f'<div class="callout"><strong>先看中文：</strong>{esc(summary_zh)}</div>'
            f'<p><strong>Today’s English</strong></p>'
            f'<p>{esc(item["summary_en"])}</p>'
        )
        if vocab:
            body += '<div class="vocab"><strong>3 个表达</strong><ul>'
            body += "".join(
                f"<li><strong>{esc(p)}</strong> — {esc(m)}</li>"
                for p, m in vocab
            )
            body += "</ul></div>"
        body += (
            f'<div class="callout"><strong>跟读一句：</strong>{esc(first_sentence)}</div>'
        )
        title = item["title_en"]
    elif module == "physics":
        body = (
            f'<div class="callout"><strong>今天讲什么：</strong>{esc(title_zh)}</div>'
            f'<p>{esc(summary_zh)}</p>'
            '<p><em>这张卡只翻译并整理来源摘要，不额外补充摘要之外的科学事实。</em></p>'
        )
        title = title_zh
    elif module == "psych":
        body = (
            f'<div class="callout"><strong>今天的心理学材料：</strong>{esc(title_zh)}</div>'
            f'<p>{esc(summary_zh)}</p>'
            '<p><em>这是文章摘要的中文整理，不用于个人诊断，也不把群体研究结论当作个人保证。</em></p>'
        )
        title = title_zh
    else:
        body = (
            f'<div class="callout"><strong>今天的原来如此：</strong>{esc(title_zh)}</div>'
            f'<p>{esc(summary_zh)}</p>'
            '<p><em>只依据来源 Feed 提供的摘要整理，没有添加摘要之外的新事实。</em></p>'
        )
        title = title_zh

    return {
        "module": module,
        "title": title,
        "body_html": body,
        "meta": source_cfg["meta"],
        "source_name": source_cfg["source_name"],
        "source_url": item["source_url"],
        "published": item["published"],
        "source_title_en": item["title_en"],
        "source_summary_en": item["summary_en"],
    }

def main():
    started = time.time()
    out_dir = Path("test-output-feed")
    out_dir.mkdir(parents=True, exist_ok=True)

    fetched = {}
    failures = []
    fetch_timings = {}

    for module, cfg in SOURCES.items():
        print(f"[fetch] {module}: {cfg['feed']}", flush=True)
        t0 = time.time()
        try:
            data = fetch(cfg["feed"])
            item = pick_entry(data, module)
            fetched[module] = item
            fetch_timings[module] = round(time.time() - t0, 2)
            print(f"  -> {item['title_en']}", flush=True)
        except Exception as exc:
            failures.append({"module": module, "stage": "fetch", "error": str(exc)})
            print(f"  FAILED: {exc}", flush=True)

    if not fetched:
        raise SystemExit("All feed fetches failed")

    print("[translate] installing/checking Argos en→zh model", flush=True)
    translate_started = time.time()
    ensure_argos_en_zh()
    install_seconds = round(time.time() - translate_started, 2)

    cards = []
    translate_timings = {}
    for module, item in fetched.items():
        cfg = SOURCES[module]
        print(f"[translate] {module}", flush=True)
        t0 = time.time()
        try:
            card = build_card(module, cfg, item)
            cards.append(card)
            translate_timings[module] = round(time.time() - t0, 2)
        except Exception as exc:
            failures.append({"module": module, "stage": "translate", "error": str(exc)})
            print(f"  FAILED: {exc}", flush=True)

    # Public-facing candidate output: only fields the website would need.
    public_cards = []
    for c in cards:
        public_cards.append({
            k: c[k] for k in [
                "module", "title", "body_html", "meta",
                "source_name", "source_url"
            ]
        })

    (out_dir / "cards.json").write_text(
        json.dumps(public_cards, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "debug.json").write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "cards_debug": cards,
                "failures": failures,
                "fetch_timings_seconds": fetch_timings,
                "argos_setup_seconds": install_seconds,
                "translate_timings_seconds": translate_timings,
                "total_seconds": round(time.time() - started, 2),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "report.txt").write_text(
        "\n".join([
            f"cards={len(cards)}/4",
            f"failures={len(failures)}",
            f"fetch_timings={json.dumps(fetch_timings, ensure_ascii=False)}",
            f"argos_setup_seconds={install_seconds}",
            f"translate_timings={json.dumps(translate_timings, ensure_ascii=False)}",
            f"total_seconds={round(time.time() - started, 2)}",
            f"failure_details={json.dumps(failures, ensure_ascii=False)}",
        ]) + "\n",
        encoding="utf-8",
    )

    if len(cards) < 4:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
