#!/usr/bin/env python3
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
TZ = timezone(timedelta(hours=8))

CATEGORIES = [
    {
        "id": "finance",
        "name": "\u8d22\u7ecf",
        "accent": "#0f766e",
        "query": '(\u8d22\u7ecf OR finance OR markets OR stocks OR economy OR "central bank") when:1d',
        "image": "https://source.unsplash.com/900x520/?finance,market",
    },
    {
        "id": "tech",
        "name": "\u79d1\u6280",
        "accent": "#2563eb",
        "query": '(\u79d1\u6280 OR technology OR AI OR semiconductor OR chip OR cloud) when:1d',
        "image": "https://source.unsplash.com/900x520/?technology,ai",
    },
    {
        "id": "bio",
        "name": "\u751f\u7269",
        "accent": "#5b7f2a",
        "query": '(\u751f\u7269 OR biotech OR biology OR pharma OR FDA OR medicine) when:1d',
        "image": "https://source.unsplash.com/900x520/?biotech,laboratory",
    },
    {
        "id": "games",
        "name": "\u6e38\u620f",
        "accent": "#9a4b14",
        "query": '(\u6e38\u620f OR gaming OR videogames OR esports OR PlayStation OR Nintendo OR Xbox) when:1d',
        "image": "https://source.unsplash.com/900x520/?gaming,esports",
    },
    {
        "id": "china",
        "name": "\u4e2d\u56fd",
        "accent": "#b42318",
        "query": '(\u4e2d\u56fd OR China) (\u65b0\u95fb OR economy OR technology OR policy OR society) when:1d',
        "image": "https://source.unsplash.com/900x520/?china,city",
    },
]


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("\ufffd\ufffd", "'").replace("\ufffd", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summarize(text, limit=118):
    text = strip_html(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" \uff0c,\u3002") + "\u2026"


def rss_url(query):
    params = {
        "q": query,
        "hl": "zh-CN",
        "gl": "CN",
        "ceid": "CN:zh-Hans",
    }
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 news-dashboard/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        return res.read()


def parse_source(title):
    if " - " not in title:
        return title, "Google News"
    headline, source = title.rsplit(" - ", 1)
    return headline.strip(), source.strip()


def parse_items(category):
    xml = fetch(rss_url(category["query"]))
    root = ET.fromstring(xml)
    items = []
    seen = set()
    for node in root.findall("./channel/item"):
        raw_title = node.findtext("title", "").strip()
        title, source = parse_source(strip_html(raw_title))
        link = node.findtext("link", "").strip()
        description = node.findtext("description", "").strip()
        published = node.findtext("pubDate", "").strip()
        key = re.sub(r"\W+", "", title.lower())[:60]
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            published_iso = parsedate_to_datetime(published).astimezone(TZ).isoformat()
        except Exception:
            published_iso = ""
        items.append(
            {
                "title": title,
                "summary": summarize(description or title),
                "why": "\u70ed\u5ea6\u4f9d\u636e\uff1a\u8fc7\u53bb 24 \u5c0f\u65f6\u65b0\u95fb\u805a\u5408\u7ed3\u679c\u9760\u524d\uff0c\u5e76\u5728\u8be5\u677f\u5757\u5173\u952e\u8bcd\u4e0b\u51fa\u73b0\u3002",
                "source": strip_html(source),
                "url": link,
                "published": published_iso,
                "image": category["image"] + f"&sig={category['id']}-{len(items) + 1}",
            }
        )
        if len(items) == 10:
            break
    return items


def fallback_item(category, index):
    return {
        "title": f"{category['name']}热点待更新 #{index}",
        "summary": "\u81ea\u52a8\u4efb\u52a1\u672c\u6b21\u672a\u80fd\u6293\u53d6\u8db3\u591f\u65b0\u95fb\u3002\u4e0b\u6b21\u8fd0\u884c\u4f1a\u7ee7\u7eed\u5c1d\u8bd5\u4f7f\u7528\u516c\u5f00 RSS \u6e90\u5237\u65b0\u3002",
        "why": "\u70ed\u5ea6\u4f9d\u636e\uff1a\u6570\u636e\u6e90\u6682\u4e0d\u53ef\u7528\uff0c\u5360\u4f4d\u4fdd\u7559\u9875\u9762\u7ed3\u6784\u3002",
        "source": "\u81ea\u52a8\u66f4\u65b0\u811a\u672c",
        "url": "https://news.google.com/",
        "published": "",
        "image": category["image"] + f"&sig=fallback-{category['id']}-{index}",
    }


def main():
    now = datetime.now(TZ)
    sections = []
    for category in CATEGORIES:
        try:
            items = parse_items(category)
            time.sleep(1)
        except Exception as exc:
            items = []
            print(f"Failed to fetch {category['id']}: {exc}")
        while len(items) < 10:
            items.append(fallback_item(category, len(items) + 1))
        sections.append(
            {
                "id": category["id"],
                "name": category["name"],
                "accent": category["accent"],
                "items": items[:10],
            }
        )

    payload = {
        "generatedAt": now.isoformat(),
        "dateLabel": now.strftime("%Y-%m-%d"),
        "window": "\u8fc7\u53bb 24 \u5c0f\u65f6",
        "sourceNote": "Google News RSS \u4e0e\u516c\u5f00\u65b0\u95fb\u805a\u5408\u7ed3\u679c\uff1b\u6309\u677f\u5757\u5173\u952e\u8bcd\u6293\u53d6\u5e76\u53bb\u91cd\u3002",
        "sections": sections,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
