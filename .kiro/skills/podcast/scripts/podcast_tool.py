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


SCAN_DIR = Path(__file__).parent.parent / "references" / "scan_cache"
SEEN_LINKS_FILE = Path(__file__).parent.parent / "references" / "seen_links.json"


def load_seen_links():
    """Load the set of previously seen links."""
    if SEEN_LINKS_FILE.exists():
        return set(json.loads(SEEN_LINKS_FILE.read_text()))
    return set()


def save_seen_links(seen):
    """Persist the seen links set."""
    SEEN_LINKS_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=0))


def scan_single_feed(feed_index):
    """Scan a single feed by index, save only NEW results to scan_cache/<index>.json."""
    if not FEEDS_FILE.exists():
        print("feeds.json not found", file=sys.stderr)
        sys.exit(1)
    feeds = json.loads(FEEDS_FILE.read_text())
    if feed_index < 0 or feed_index >= len(feeds):
        print(f"Invalid index {feed_index}, total feeds: {len(feeds)}", file=sys.stderr)
        sys.exit(1)

    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    seen = load_seen_links()
    feed_info = feeds[feed_index]
    print(f"抓取: {feed_info['name']}...", file=sys.stderr)
    try:
        if feed_info.get("source") == "web":
            episodes = scrape_blog_links(feed_info)
        else:
            episodes = scan_rss(feed_info)
    except Exception as e:
        print(f"失败: {e}", file=sys.stderr)
        episodes = []

    new_episodes = [ep for ep in episodes if ep.get("link") and ep["link"] not in seen]
    for ep in new_episodes:
        seen.add(ep["link"])

    out_path = SCAN_DIR / f"{feed_index}.json"
    out_path.write_text(json.dumps(new_episodes, ensure_ascii=False, indent=2))
    save_seen_links(seen)
    print(f"已保存 {len(new_episodes)} 条新内容（跳过 {len(episodes) - len(new_episodes)} 条已见）")


def scan_feeds():
    """Scan all feeds sequentially, saving only NEW items to scan_cache/<index>.json."""
    if not FEEDS_FILE.exists():
        print("feeds.json not found", file=sys.stderr)
        sys.exit(1)
    feeds = json.loads(FEEDS_FILE.read_text())
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    seen = load_seen_links()
    total_new = 0

    for i, feed_info in enumerate(feeds):
        print(f"[{i}/{len(feeds)}] 抓取: {feed_info['name']}...", file=sys.stderr)
        try:
            if feed_info.get("source") == "web":
                episodes = scrape_blog_links(feed_info)
            else:
                episodes = scan_rss(feed_info)
        except Exception as e:
            print(f"  失败: {e}", file=sys.stderr)
            episodes = []

        new_episodes = [ep for ep in episodes if ep.get("link") and ep["link"] not in seen]
        for ep in new_episodes:
            seen.add(ep["link"])

        out_path = SCAN_DIR / f"{i}.json"
        out_path.write_text(json.dumps(new_episodes, ensure_ascii=False, indent=2))
        print(f"  {len(new_episodes)} 条新 / {len(episodes)} 条总", file=sys.stderr)
        total_new += len(new_episodes)

    save_seen_links(seen)
    print(json.dumps({"total_feeds": len(feeds), "new_items": total_new, "cache_dir": str(SCAN_DIR)}))


# ─── FETCH ARTICLE ──────────────────────────────────────────────────────────

def fetch_article(url):
    """Fetch article HTML and print to stdout."""
    print(fetch_html(url))


# ─── FETCH IMAGES ───────────────────────────────────────────────────────────

def fetch_images(source, output_dir):
    """Extract and download all images from HTML (file path or URL). Output JSON mapping.

    Images with a description (alt text or nearby figcaption) are considered
    content images and named fig_XX_<slug>.ext. Images without description are
    treated as decorative (hero/banner/icon) and named fig_XX_untitled.ext.
    The output JSON includes a "use" field: true for content images, false for decorative.
    """
    from html import unescape
    from urllib.parse import urljoin, urlparse, parse_qs
    import unicodedata

    if os.path.isfile(source):
        html = Path(source).read_text(encoding="utf-8", errors="ignore")
        base_url = ""
    else:
        html = fetch_html(source)
        base_url = source

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    def resolve_url(src):
        """Resolve a src to a downloadable URL, handling Next.js _next/image wrappers."""
        src = unescape(src)
        if src.startswith("data:"):
            return None
        if not src.startswith("http"):
            if base_url:
                src = urljoin(base_url, src)
            else:
                return None
        parsed = urlparse(src)
        if "/_next/image" in parsed.path:
            qs = parse_qs(parsed.query)
            if "url" in qs:
                src = qs["url"][0]
        return src

    def slugify(text, max_len=40):
        """Convert text to a filename-safe slug."""
        text = text.strip().lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        text = text.strip('-')[:max_len].rstrip('-')
        return text or ""

    def get_description(match, html_text):
        """Extract description from alt attr or nearby figcaption."""
        tag = match.group(0)
        # Try alt attribute
        alt_m = re.search(r'alt="([^"]*)"', tag, re.IGNORECASE)
        alt = alt_m.group(1).strip() if alt_m else ""
        if alt and alt.lower() not in ("", "image", "img", "photo", "picture", "figure"):
            return alt
        # Try figcaption after the img (within 300 chars)
        after = html_text[match.end():match.end()+500]
        cap_m = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', after, re.IGNORECASE|re.DOTALL)
        if cap_m:
            cap = re.sub(r'<[^>]+>', '', cap_m.group(1)).strip()
            if cap:
                return cap[:80]
        return ""

    # Extract img entries with context
    img_entries = []  # list of (url, description)
    seen_urls = set()
    for m in re.finditer(r'<img[^>]+>', html, re.IGNORECASE):
        tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', tag, re.IGNORECASE)
        if not src_m:
            continue
        url = resolve_url(src_m.group(1))
        if not url or url in seen_urls:
            # Also try srcset
            srcset_m = re.search(r'srcset="([^"]+)"', tag, re.IGNORECASE)
            if srcset_m:
                parts = [p.strip().split()[0] for p in srcset_m.group(1).split(",") if p.strip()]
                if parts:
                    url = resolve_url(parts[-1])
            if not url or url in seen_urls:
                continue
        seen_urls.add(url)
        desc = get_description(m, html)
        img_entries.append((url, desc))

    results = []
    for i, (url, desc) in enumerate(img_entries, 1):
        ext = Path(urlparse(url).path).suffix or ".png"
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
            ext = ".png"
        slug = slugify(desc)
        use = bool(slug)  # has description = content image
        if slug:
            filename = f"fig_{i:02d}_{slug}{ext}"
        else:
            filename = f"fig_{i:02d}_untitled{ext}"
        filepath = output_path / filename
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                filepath.write_bytes(resp.read())
            results.append({"index": i, "file": filename, "description": desc, "use": use, "original_url": url})
            mark = "✓" if use else "○"
            print(f"  {mark} {filename} ← {url[:70]}", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ {filename} 失败: {e}", file=sys.stderr)
            results.append({"index": i, "file": filename, "description": desc, "use": use, "original_url": url, "error": str(e)})

    print(json.dumps(results, ensure_ascii=False, indent=2))


# ─── CHUNK ARTICLE ──────────────────────────────────────────────────────────

def chunk_article(source_html, output_prefix):
    """Split article HTML into chunks by h2/h3 sections, save to temp files."""
    from html import unescape

    html = Path(source_html).read_text(encoding="utf-8", errors="ignore")

    # Extract article body
    m = re.search(r'<article>(.*?)</article>', html, re.DOTALL)
    if not m:
        # Fallback: use full HTML
        body = html
    else:
        body = m.group(1)

    # Split by h2/h3 headings (keep heading with its content)
    parts = re.split(r'(<h[23][^>]*>.*?</h[23]>)', body, flags=re.DOTALL)

    chunks = []
    current_heading = ""
    current_content = ""

    def text_of(html_str):
        t = re.sub(r'<[^>]+>', ' ', html_str)
        return unescape(re.sub(r'\s+', ' ', t).strip())

    def save_chunk():
        nonlocal current_heading, current_content
        text = text_of(current_content)
        if len(text.split()) < 20:
            return  # skip trivially small chunks
        chunks.append({"heading": current_heading, "text": text})

    for part in parts:
        if re.match(r'<h[23]', part):
            # Save previous chunk
            if current_content.strip():
                save_chunk()
            current_heading = text_of(part)
            current_content = ""
        else:
            current_content += part

    # Save last chunk
    if current_content.strip():
        save_chunk()

    # Merge small chunks or split large ones
    final_chunks = []
    for chunk in chunks:
        words = len(chunk["text"].split())
        if words > 1500:
            # Split by paragraphs into ~800-1200 word sub-chunks
            sentences = chunk["text"].split('. ')
            sub = ""
            sub_idx = 0
            for s in sentences:
                if len((sub + s).split()) > 1000 and sub:
                    final_chunks.append({"heading": f"{chunk['heading']} (part {sub_idx+1})", "text": sub.strip()})
                    sub_idx += 1
                    sub = s + ". "
                else:
                    sub += s + ". "
            if sub.strip():
                final_chunks.append({"heading": f"{chunk['heading']} (part {sub_idx+1})", "text": sub.strip()})
        else:
            final_chunks.append(chunk)

    # Save each chunk to a file
    output_dir = Path(output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = Path(output_prefix).name

    manifest = []
    for i, chunk in enumerate(final_chunks, 1):
        filepath = output_dir / f"{prefix}_chunk_{i:02d}.txt"
        filepath.write_text(chunk["text"], encoding="utf-8")
        manifest.append({
            "index": i,
            "heading": chunk["heading"],
            "words": len(chunk["text"].split()),
            "file": str(filepath)
        })

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


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

    sub.add_parser("scan", help="扫描所有feeds，结果存入scan_cache/")

    sf = sub.add_parser("scan-feed", help="扫描单个feed（按索引）")
    sf.add_argument("index", type=int)

    fa = sub.add_parser("fetch-article", help="抓取文章HTML")
    fa.add_argument("url")

    fi = sub.add_parser("fetch-images", help="从HTML中提取并下载所有图片")
    fi.add_argument("source", help="HTML文件路径或URL")
    fi.add_argument("output_dir", help="图片保存目录")

    ca = sub.add_parser("chunk-article", help="将文章HTML按章节分块存入临时文件")
    ca.add_argument("source_html", help="source.html文件路径")
    ca.add_argument("output_prefix", help="输出前缀，如 /tmp/slug")

    tr = sub.add_parser("transcribe", help="下载并转录音频")
    tr.add_argument("url")
    tr.add_argument("-t", "--title", default="episode")
    tr.add_argument("-m", "--model", default="base")

    args = parser.parse_args()

    if args.command == "scan":
        scan_feeds()
    elif args.command == "scan-feed":
        scan_single_feed(args.index)
    elif args.command == "fetch-article":
        fetch_article(args.url)
    elif args.command == "fetch-images":
        fetch_images(args.source, args.output_dir)
    elif args.command == "chunk-article":
        chunk_article(args.source_html, args.output_prefix)
    elif args.command == "transcribe":
        transcribe(args.url, title=args.title, model=args.model)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
