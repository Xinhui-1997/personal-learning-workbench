#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from pathlib import Path

MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")

SOURCES = [
    {
        "module": "english",
        "meta": "1–2 分钟 · 中英双语",
        "source_name": "NASA Science",
        "source_url": "https://science.nasa.gov/exoplanets/",
        "source_text": (
            "Exoplanets are planets that orbit stars beyond our solar system. "
            "Scientists detect them with methods including transits, where a planet "
            "passes in front of its star and causes a small, measurable dip in brightness. "
            "Studying an exoplanet's size, orbit and atmosphere can help researchers compare "
            "other planetary systems with our own."
        ),
        "instructions": (
            "Create a bilingual English-learning card that takes about 1–2 minutes. "
            "Use easy English suitable for a Chinese learner. The body must contain: "
            "a short Chinese preview; 3–5 short English sentences; a Chinese explanation; "
            "three useful English expressions with Chinese meanings; and exactly one short "
            "English sentence to read aloud."
        ),
    },
    {
        "module": "physics",
        "meta": "1–2 分钟 · 中文",
        "source_name": "Encyclopaedia Britannica",
        "source_url": "https://www.britannica.com/science/Leidenfrost-effect",
        "source_text": (
            "The Leidenfrost effect occurs when a liquid contacts a surface much hotter than "
            "its boiling point. A vapor layer forms beneath the droplet and partially insulates "
            "it from the hot surface, so the droplet can skate or hover instead of boiling away "
            "immediately. Heat transfer, evaporation and fluid motion all contribute."
        ),
        "instructions": (
            "Write the title and body in Simplified Chinese, except necessary scientific terms. "
            "Create a 1–2 minute physics card for a curious adult. Explain the mechanism accurately "
            "and intuitively. Keep it compact and avoid unsupported details."
        ),
    },
    {
        "module": "psych",
        "meta": "1–2 分钟 · 中文",
        "source_name": "The Learning Scientists",
        "source_url": "https://www.learningscientists.org/spaced-practice",
        "source_text": (
            "Spaced practice means spreading study sessions across time instead of doing the "
            "same amount of study in one long session. Research on memory generally finds that "
            "spacing improves long-term retention. The best spacing interval depends on the "
            "material, learner and how long the information needs to be remembered."
        ),
        "instructions": (
            "Write the title and body in Simplified Chinese, except the English term spaced practice "
            "when useful. Create a 1–2 minute psychology/learning-science card. Clearly distinguish "
            "a general research tendency from an individual guarantee. Include one important "
            "limitation and one gentle reflection question. Do not invent specific effect sizes."
        ),
    },
    {
        "module": "science",
        "meta": "1–2 分钟 · 中文",
        "source_name": "Smithsonian Ocean",
        "source_url": "https://ocean.si.edu/ocean-life/invertebrates/octopuses",
        "source_text": (
            "Octopuses are cephalopods with complex nervous systems. They have three hearts and "
            "use hemocyanin, a copper-containing oxygen-carrying protein that gives their blood "
            "a bluish color. Their skin contains specialized cells that help produce rapid "
            "changes in color and pattern for camouflage and signaling."
        ),
        "instructions": (
            "Write the title and body in Simplified Chinese, except necessary scientific terms. "
            "Create a light but accurate 1–2 minute science card. Include one clearly labeled "
            "section called ‘今天的原来如此’ with a memorable takeaway."
        ),
    },
]

SYSTEM = """You transform a supplied source packet into one learning card.
Use ONLY the supplied source packet. Never add facts that are not present in the packet.
Do not invent quotations, numbers, dates, studies, mechanisms, organizations, or URLs.
Return strict JSON only with exactly these keys: title, body_html, quality_note.
body_html may use p, div class=callout, div class=vocab, strong, em, ul, li.
Do not use markdown. Do not include source fields, metadata fields, scores, or hidden fields.
quality_note must be one short sentence and should mention any simplification or uncertainty.
"""

def call_ollama(item):
    prompt = (
        f"MODULE: {item['module']}\n"
        f"SOURCE_PACKET:\n{item['source_text']}\n\n"
        f"TASK:\n{item['instructions']}\n"
    )
    payload = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.15,
            "num_predict": 850,
        },
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = json.load(resp)
    elapsed = round(time.time() - started, 2)
    generated = json.loads(raw["message"]["content"])

    card = {
        "module": item["module"],
        "title": generated.get("title", "").strip(),
        "body_html": generated.get("body_html", "").strip(),
        "meta": item["meta"],
        "source_name": item["source_name"],
        "source_url": item["source_url"],
        "quality_note": generated.get("quality_note", "").strip(),
    }
    return card, elapsed

def validate(item, card):
    required = [
        "module", "title", "body_html", "meta",
        "source_name", "source_url", "quality_note"
    ]
    missing = [k for k in required if not card.get(k)]
    if missing:
        raise ValueError(f"{item['module']}: missing keys/values: {missing}")
    if card["module"] != item["module"]:
        raise ValueError(f"{item['module']}: wrong module")
    if card["source_name"] != item["source_name"]:
        raise ValueError(f"{item['module']}: source_name mismatch")
    if card["source_url"] != item["source_url"]:
        raise ValueError(f"{item['module']}: source_url mismatch")
    if card["meta"] != item["meta"]:
        raise ValueError(f"{item['module']}: meta mismatch")

def main():
    out_dir = Path("test-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    timings = {}
    failures = []

    for item in SOURCES:
        print(f"Generating {item['module']} with {MODEL} ...", flush=True)
        try:
            card, elapsed = call_ollama(item)
            validate(item, card)
            results.append(card)
            timings[item["module"]] = elapsed
            print(f"  OK in {elapsed}s", flush=True)
        except Exception as exc:
            failures.append({"module": item["module"], "error": str(exc)})
            print(f"  FAILED: {exc}", flush=True)

    bundle = {
        "experiment": "local-qwen-learning-cards",
        "model": MODEL,
        "cards": results,
        "failures": failures,
        "timings_seconds": timings,
    }
    (out_dir / "learning_cards.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = [
        f"model={MODEL}",
        f"success={len(results)}/{len(SOURCES)}",
        f"failures={len(failures)}",
        "timings=" + json.dumps(timings, ensure_ascii=False),
    ]
    if failures:
        report.append("failure_details=" + json.dumps(failures, ensure_ascii=False))
    (out_dir / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
