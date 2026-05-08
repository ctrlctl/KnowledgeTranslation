#!/usr/bin/env python3
"""Podcast Tool - RSS fetch, web scrape, audio transcribe, article fetch utilities."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import feedparser

NOTES_DIR = Path(__file__).parent.parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)
FEEDS_FILE = Path(__file__).parent.parent / "references" / "feeds.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


# ─── HTML LINK EXTRACTOR ────────────────────────────────────────────────────

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def scrape_blog_links(feed_info):
    """Scrape article links from a blog listing page using regex."""
    url = feed_info["url"]
    name = feed_info["name"]
    pattern = feed_info.get("link_pattern", "")

    html = fetch_html(url)

    articles = []
    seen = set()

    # Method 1: <a> tags with text content
    for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href, text = m.group(1), m.group(2)
        title = re.sub(r'<[^>]+>', ' ', text).strip()
        title = re.sub(r'\s+', ' ', title)
        if href.startswith("/"):
            base = url.split("/")[0] + "//" + url.split("/")[2]
            href = base + href
        if pattern and not re.search(pattern, href):
            continue
        if "/team/" in href:
            continue
        if len(title) >= 15 and href not in seen:
            seen.add(href)
            articles.append({"feed": name, "title": title, "summary": "", "link": href, "audio": "", "type": "article"})

    # Method 2: empty <a> tags (e.g. LangChain) — extract href and derive title from slug
    if not articles:
        for m in re.finditer(r'href="([^"]*' + re.escape(pattern) + r'[^"]*)"', html):
            href = m.group(1)
            if href.startswith("/"):
                base = url.split("/")[0] + "//" + url.split("/")[2]
                href = base + href
            if "/team/" in href or href in seen:
                continue
            seen.add(href)
            # Derive title from URL slug
            slug = href.rstrip("/").split("/")[-1]
            title = slug.replace("-", " ").replace("_", " ").title()
            if len(title) >= 10:
                articles.append({"feed": name, "title": title, "summary": "", "link": href, "audio": "", "type": "article"})

    return articles


# ─── RSS SCAN ───────────────────────────────────────────────────────────────

def detect_content_type(entry):
    for enc in entry.get("enclosures", []):
        t = enc.get("type", "")
        if "audio" in t or "video" in t:
            return "media"
    for link in entry.get("links", []):
        t = link.get("type", "")
        if "audio" in t or "video" in t:
            return "media"
    return "article"


def extract_audio_url(entry):
    for enc in entry.get("enclosures", []):
        if "audio" in enc.get("type", "") or "video" in enc.get("type", ""):
            return enc.get("href", "")
    for link in entry.get("links", []):
        if "audio" in link.get("type", "") or "video" in link.get("type", ""):
            return link.get("href", "")
    return entry.get("link", "")


def scan_rss(feed_info):
    """Scan a single RSS feed, take latest 10 entries."""
    feed = feedparser.parse(feed_info["url"])
    episodes = []
    for entry in feed.entries[:10]:
        title = entry.get("title", "")
        summary = entry.get("summary", entry.get("description", ""))
        content_type = detect_content_type(entry)
        episodes.append({
            "feed": feed_info["name"],
            "title": title,
            "summary": summary[:500],
            "link": entry.get("link", ""),
            "audio": extract_audio_url(entry) if content_type == "media" else "",
            "type": content_type,
        })
    return episodes


def scan_feeds():
    if not FEEDS_FILE.exists():
        print("feeds.json not found", file=sys.stderr)
        sys.exit(1)
    feeds = json.loads(FEEDS_FILE.read_text())
    all_episodes = []

    for feed_info in feeds:
        print(f"抓取: {feed_info['name']}...", file=sys.stderr)
        try:
            if feed_info.get("source") == "web":
                episodes = scrape_blog_links(feed_info)
            else:
                episodes = scan_rss(feed_info)
            all_episodes.extend(episodes)
        except Exception as e:
            print(f"  失败: {e}", file=sys.stderr)

    print(json.dumps(all_episodes, ensure_ascii=False, indent=2))


# ─── FETCH ARTICLE ──────────────────────────────────────────────────────────

def fetch_article(url):
    """Fetch article HTML and print to stdout."""
    print(fetch_html(url))


# ─── TRANSCRIBE ─────────────────────────────────────────────────────────────

def transcribe(url, title="episode", model="base"):
    """Download audio and transcribe with Whisper, output timestamped text."""
    import whisper

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "audio.%(ext)s")
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_path, url]
        print(f"下载: {url}", file=sys.stderr)
        subprocess.run(cmd, check=True, capture_output=True)

        audio_path = None
        for f in os.listdir(tmpdir):
            if f.startswith("audio"):
                audio_path = os.path.join(tmpdir, f)
                break
        if not audio_path:
            print("下载失败", file=sys.stderr)
            sys.exit(1)

        print(f"转录中 (模型: {model})...", file=sys.stderr)
        m = whisper.load_model(model)
        result = m.transcribe(audio_path, verbose=False)

    for seg in result["segments"]:
        seconds = seg["start"]
        h = int(seconds // 3600)
        mi = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ts = f"{h:02d}:{mi:02d}:{s:02d}" if h > 0 else f"{mi:02d}:{s:02d}"
        print(f"[{ts}] {seg['text'].strip()}")


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="播客工具")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="扫描feeds，输出JSON")

    fa = sub.add_parser("fetch-article", help="抓取文章HTML")
    fa.add_argument("url")

    tr = sub.add_parser("transcribe", help="下载并转录音频")
    tr.add_argument("url")
    tr.add_argument("-t", "--title", default="episode")
    tr.add_argument("-m", "--model", default="base")

    args = parser.parse_args()

    if args.command == "scan":
        scan_feeds()
    elif args.command == "fetch-article":
        fetch_article(args.url)
    elif args.command == "transcribe":
        transcribe(args.url, title=args.title, model=args.model)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
