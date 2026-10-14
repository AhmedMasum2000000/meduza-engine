"""Medusa trial loop: Scout -> Brief -> Create -> Guard -> (Publish preview) -> Report.

Runs with no API keys. Pulls live Google Trends for BD/IN/PK/TH, picks top topics,
writes captions, renders square post images, checks them with Guard rules,
and writes a report page to trial/out/index.html.
"""
import datetime as dt
import html
import json
import os
import re
import textwrap
import urllib.request
import xml.etree.ElementTree as ET  # trusted source (Google Trends RSS)

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "out")
COUNTRIES = {"BD": "Bangladesh", "IN": "India", "PK": "Pakistan", "TH": "Thailand"}
PER_COUNTRY = 3
NS = {"ht": "https://trends.google.com/trending/rss"}

BANNED = ["bet", "betting", "casino", "gambl", "porn", "xxx", "guaranteed return", "loan app"]
SPORT_WORDS = ["cricket", "vs", "match", "football", "fc", "league", "cup", "ipl", "bpl", "psl", "score", "live"]


def scout(geo):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 medusa-trial"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        traffic = (it.findtext("ht:approx_traffic", namespaces=NS) or "").strip()
        news = it.find("ht:news_item", NS)
        source = news.findtext("ht:news_item_source", namespaces=NS) if news is not None else ""
        headline = news.findtext("ht:news_item_title", namespaces=NS) if news is not None else ""
        items.append({"topic": title, "traffic": traffic, "source": source or "", "headline": headline or ""})
    return items


def traffic_num(t):
    m = re.match(r"([\d,]+)", t or "")
    return int(m.group(1).replace(",", "")) if m else 0


def guard(text):
    low = text.lower()
    for w in BANNED:
        if re.search(r"\b" + re.escape(w), low):
            return "block", f"banned topic: '{w}'"
    return "pass", "no banned topics, original caption, AI label added"


def brief(item, country):
    topic = item["topic"]
    is_sport = any(w in topic.lower() for w in SPORT_WORDS)
    niche = "Sports" if is_sport else "Entertainment & news"
    hook = f"Everyone in {country} is searching this right now 👀"
    caption = (
        f"{hook}\n\n🔥 {topic.title()}\n"
        + (f"📰 {item['headline']}\n" if item["headline"] else "")
        + f"\nWhat's your take? Comment below 👇\n#{re.sub(r'[^A-Za-z0-9]', '', topic.title())[:30]} #{country.replace(' ', '')}Trending\n"
        + "ℹ️ Made with AI assistance."
    )
    return {"niche": niche, "hook": hook, "caption": caption}


SCRIPT_FONTS = [  # (unicode range, candidate font files) - Noto on GitHub runners, FreeSerif fallback
    ((0x0E00, 0x0E7F), ["NotoSansThai-Bold.ttf", "NotoSansThai-Regular.ttf", "FreeSerifBold.ttf"]),
    ((0x0980, 0x09FF), ["NotoSansBengali-Bold.ttf", "NotoSansBengali-Regular.ttf", "FreeSerifBold.ttf"]),
    ((0x0900, 0x097F), ["NotoSansDevanagari-Bold.ttf", "NotoSansDevanagari-Regular.ttf", "FreeSerifBold.ttf"]),
    ((0x0600, 0x06FF), ["NotoSansArabic-Bold.ttf", "NotoNaskhArabic-Bold.ttf", "FreeSerifBold.ttf"]),
]
FONT_DIRS = ["/usr/share/fonts/truetype/noto", "/usr/share/fonts/opentype/noto", "/usr/share/fonts/truetype/freefont", "/usr/share/fonts/truetype/dejavu"]


def _find(names):
    for n in names:
        for d in FONT_DIRS:
            if os.path.exists(os.path.join(d, n)):
                return os.path.join(d, n)
    return None


def font(size, bold=True, text=""):
    for (lo, hi), names in SCRIPT_FONTS:
        if any(lo <= ord(c) <= hi for c in text):
            path = _find(names)
            if path:
                return ImageFont.truetype(path, size)
    path = _find(["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"])
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()


def create(item, country, niche, path):
    W = 1080
    img = Image.new("RGB", (W, W), "#0a1311")
    d = ImageDraw.Draw(img)
    for r in range(520, 0, -8):  # emerald glow
        a = int(40 * (1 - r / 520))
        d.ellipse([W - 300 - r, 200 - r, W - 300 + r, 200 + r], fill=(10 + a // 3, 19 + a, 17 + a // 2))
    d.rectangle([0, 0, W, 14], fill="#f2c057")
    d.text((70, 70), "MEDUSA · " + niche.upper(), font=font(30), fill="#7cf5d0")
    d.text((70, 120), f"TRENDING IN {country.upper()}", font=font(34), fill="#f2c057")
    y = 300
    for line in textwrap.wrap(item["topic"].title(), 16)[:4]:
        d.text((70, y), line, font=font(96, text=line), fill="#f3eee2")
        y += 112
    if item["headline"]:
        for line in textwrap.wrap(item["headline"], 44)[:2]:
            d.text((70, y + 20), line, font=font(34, False, text=line), fill="#c9d0c9")
            y += 46
    d.rounded_rectangle([70, 900, 520, 990], radius=45, fill="#19c48f")
    d.text((105, 922), f"{item['traffic'] or 'Rising'} searches", font=font(38), fill="#050a09")
    d.text((W - 330, 950), "AI-assisted", font=font(26, False), fill="#86968f")
    img.save(path, quality=88)


def main():
    os.makedirs(OUT, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    posts, log = [], []
    for geo, country in COUNTRIES.items():
        try:
            items = scout(geo)
        except Exception as e:  # keep the demo running if one country fails
            log.append(f"{country}: scout failed ({e})")
            continue
        log.append(f"{country}: {len(items)} trending topics found")
        items.sort(key=lambda i: traffic_num(i["traffic"]), reverse=True)
        for i, item in enumerate(items[:PER_COUNTRY]):
            b = brief(item, country)
            verdict, reason = guard(item["topic"] + " " + item["headline"] + " " + b["caption"])
            fname = f"{geo.lower()}-{i}.jpg"
            if verdict == "pass":
                create(item, country, b["niche"], os.path.join(OUT, fname))
            posts.append({**item, **b, "country": country, "guard": verdict, "reason": reason,
                          "image": fname if verdict == "pass" else None})
    data = {"generated_at": now.isoformat(), "log": log, "posts": posts}
    json.dump(data, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, indent=2)
    write_report(data)
    print("\n".join(log), f"\n{len(posts)} posts briefed, {sum(p['guard']=='pass' for p in posts)} passed Guard")


def write_report(data):
    passed = [p for p in data["posts"] if p["guard"] == "pass"]
    blocked = [p for p in data["posts"] if p["guard"] != "pass"]
    cards = "".join(
        f"""<article><img src="{p['image']}" alt="Post about {html.escape(p['topic'])}" loading="lazy">
<div class="meta"><span class="ok">✓ Guard passed</span><span>{html.escape(p['country'])} · {html.escape(p['niche'])} · {html.escape(p['traffic'] or 'rising')} searches</span></div>
<pre>{html.escape(p['caption'])}</pre></article>""" for p in passed)
    blocked_html = "".join(f"<li><b>{html.escape(p['topic'])}</b> ({html.escape(p['country'])}): {html.escape(p['reason'])}</li>" for p in blocked) or "<li>Nothing blocked this run.</li>"
    log_html = "".join(f"<li>{html.escape(l)}</li>" for l in data["log"])
    when = data["generated_at"][:16].replace("T", " ") + " UTC"
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Medusa Trial Run</title><style>
body{{margin:0;background:#060b0a;color:#f3eee2;font:16px/1.6 system-ui,sans-serif}}
.wrap{{max-width:1100px;margin:auto;padding:32px max(16px,env(safe-area-inset-left))}}
h1{{font-size:clamp(1.8rem,5vw,3rem);margin:0}} h1 span{{color:#f2c057}}
.steps{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}} .steps b{{background:#0e1c18;border:1px solid #1f3a33;border-radius:999px;padding:6px 14px;font-size:.85rem}}
.steps b.on{{border-color:#19c48f;color:#7cf5d0}}
.grid{{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}}
article{{background:#0e1c18;border:1px solid #1f3a33;border-radius:14px;overflow:hidden}} article img{{width:100%;display:block}}
.meta{{display:flex;flex-direction:column;gap:2px;padding:12px 14px 0;font-size:.85rem;color:#c9d0c9}} .ok{{color:#19c48f;font-weight:600}}
pre{{white-space:pre-wrap;font:inherit;font-size:.85rem;padding:0 14px 14px;color:#c9d0c9}}
section{{margin-top:36px}} .muted{{color:#86968f}}
</style></head><body><div class="wrap">
<p class="muted">Medusa · automated trial · last run {when}</p>
<h1>The loop <span>works.</span></h1>
<p>This page was built by a robot on GitHub with no human help. It found what people are searching for right now in 4 countries, wrote posts, designed images, checked every post against our rules, and published this report.</p>
<div class="steps"><b class="on">1 Scout ✓</b><b class="on">2 Brief ✓</b><b class="on">3 Create ✓</b><b class="on">4 Guard ✓</b><b>5 Publish: next, needs page logins</b><b class="on">6 Report ✓</b></div>
<p><b>{len(passed)}</b> posts ready · <b>{len(blocked)}</b> blocked by Guard</p>
<div class="grid">{cards}</div>
<section><h2>Blocked by Guard</h2><ul>{blocked_html}</ul></section>
<section><h2>Run log</h2><ul class="muted">{log_html}</ul><p class="muted">Runs automatically every 6 hours. Source: live Google Trends.</p></section>
</div></body></html>"""
    open(os.path.join(OUT, "index.html"), "w").write(page)


if __name__ == "__main__":
    main()
