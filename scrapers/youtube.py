import csv
import io
import json
import os
import re
import sys
import time
import random
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from search_engine import search as web_search

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SEARCH_QUERIES = [
    "Claude vs ChatGPT",
    "Claude vs GPT-4",
    "Claude vs Gemini",
    "Claude AI coding",
    "Claude for developers",
    "Claude coding demo",
    "Claude AI review",
    "Anthropic Claude review",
    "is Claude better than ChatGPT",
    "Claude AI demo",
    "what Claude can do",
    "Claude 3.5 Sonnet",
    "Claude Opus",
    "Anthropic Claude update",
    "Claude shocked me",
    "I switched to Claude",
    "Claude is insane",
]

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "youtube.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

_session = requests.Session()


def _extract_video_id(url):
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _parse_count(text):
    text = text.strip().replace(",", "")
    m = re.search(r"([\d.]+)", text)
    if not m:
        return 0
    num = float(m.group(1))
    if "k" in text.lower():
        num *= 1000
    elif "m" in text.lower():
        num *= 1000000
    return int(num)


def _scrape_video_page(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    }

    try:
        resp = _session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        html = resp.text

        title = ""
        description = ""
        views = 0
        likes = 0
        comments = 0
        published = ""

        # Extract from ytInitialPlayerResponse
        m = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.*?\})\s*;", html, re.DOTALL)
        if m:
            try:
                player = json.loads(m.group(1))
                vd = player.get("videoDetails", {})
                title = title or vd.get("title", "")
                description = description or vd.get("shortDescription", "")
                views = int(vd.get("viewCount", 0))
            except (json.JSONDecodeError, ValueError):
                pass

        # Extract from ytInitialData (likes, comments)
        m = re.search(r"var ytInitialData\s*=\s*(\{.*?\})\s*;", html, re.DOTALL)
        if m:
            try:
                raw_json = m.group(1)
                m_likes = re.search(r'"label"\s*:\s*"([\d,]+)\s+likes?"', raw_json, re.IGNORECASE)
                if m_likes:
                    likes = int(m_likes.group(1).replace(",", ""))
                m_comm = re.search(r'"commentCount"\s*:\s*\{"simpleText"\s*:\s*"([\d,]+)"', raw_json)
                if m_comm:
                    comments = int(m_comm.group(1).replace(",", ""))
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: likes from likeCount field
        if not likes:
            m_likes = re.search(r'"likeCount"\s*:\s*"?(\d+)"?', html)
            if m_likes:
                likes = int(m_likes.group(1))

        # Extract date
        if not published:
            m_date = re.search(r'"publishDate"\s*:\s*"([^"]+)"', html)
            if m_date:
                published = m_date.group(1)
        if not published:
            m_date = re.search(r'"uploadDate"\s*:\s*"([^"]+)"', html)
            if m_date:
                published = m_date.group(1)
        if not published:
            m_date = re.search(r'<meta\s+itemprop="datePublished"\s+content="([^"]+)"', html)
            if m_date:
                published = m_date.group(1)

        # Fallback: comment count
        if not comments:
            m_comm = re.search(r'"commentCount"\s*:\s*"?(\d+)"?', html)
            if m_comm:
                comments = int(m_comm.group(1))

        # Fallback: title
        if not title:
            m_title = re.search(r'<meta\s+name="title"\s+content="([^"]+)"', html)
            if m_title:
                title = m_title.group(1)
        if not title:
            m_title = re.search(r"<title>(.+?)(?:\s*-\s*YouTube)?\s*</title>", html)
            if m_title:
                title = m_title.group(1)

        if not title:
            return None

        return {
            "video_id": video_id,
            "title": title,
            "description": description or "",
            "views": views,
            "likes": likes,
            "comments": comments,
            "published": published,
        }

    except Exception as e:
        print(f"    Error scraping {video_id}: {e}")
        return None


def _search_youtube_directly(query, max_results=30):
    url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
    headers = {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    ids = []
    try:
        resp = _session.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return ids
        # Extract video IDs from ytInitialData JSON embedded in the page
        m = re.search(r"var ytInitialData\s*=\s*(\{.*?\})\s*;", resp.text, re.DOTALL)
        if m:
            raw = m.group(1)
            # Find all videoId values
            for vid_match in re.finditer(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', raw):
                vid = vid_match.group(1)
                if vid not in ids:
                    ids.append(vid)
                if len(ids) >= max_results:
                    break
    except Exception as e:
        print(f"    [YT search] Error: {e}")
    return ids


def discover_video_urls():
    ids = set()

    # YouTube search
    for query in SEARCH_QUERIES:
        print(f"    YT search: '{query[:50]}' ...", end=" ", flush=True)
        found = _search_youtube_directly(query, max_results=20)
        for vid in found:
            ids.add(vid)
        print(f"got {len(found)}")
        time.sleep(random.uniform(1, 2.5))

    # Web search fallback if YouTube gave too few results
    if len(ids) < 20:
        print("    Trying web search fallback...")
        for query in SEARCH_QUERIES[:5]:
            full_q = f"site:youtube.com/watch {query}"
            results = web_search(full_q, max_results=15)
            for r in results:
                link = r.get("link", "")
                vid = _extract_video_id(link)
                if vid:
                    ids.add(vid)

    return list(ids)


def clean_text(raw):
    text = raw
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000026FF\U0000200D\U00002B50\U00002B55"
        r"\U000023E9-\U000023F3\U0000231A-\U0000231B\U00002934-\U00002935"
        r"\U000025AA-\U000025FE\U00002190-\U000021FF\U0000274C\U0000274E"
        r"\U00002705\U00002714\U00002716]+",
        " ", text,
    )
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", "", text)
    text = re.sub(r"[-=*_]{3,}", " ", text)
    text = re.sub(r"(?i)(subscribe|like and share|hit the bell|don't forget to|follow me|join.*discord|merch:)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 500:
        text = text[:500].rsplit(" ", 1)[0] + "..."
    return text


def is_relevant(title, description):
    text = (title + " " + description).lower()
    return "claude" in text


def format_date(raw_date):
    if not raw_date:
        return ""
    try:
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        pass
    if re.match(r"\d{4}-\d{2}-\d{2}$", str(raw_date)):
        return raw_date
    m = re.search(r"(\w{3})\s+(\d{1,2}),?\s+(\d{4})", str(raw_date))
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)}, {m.group(3)}", "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return str(raw_date)[:10] if len(str(raw_date)) >= 10 else ""


def save_csv(rows, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("\n" + "=" * 60)
    print("  YouTube Collector — Claude AI (no API key)")
    print("=" * 60)

    print(f"\n[1/3] Discovering videos ({len(SEARCH_QUERIES)} queries)...")
    video_ids = discover_video_urls()
    print(f"  Found {len(video_ids)} unique video IDs")

    if not video_ids:
        print("  No videos found.")
        return

    print(f"\n[2/3] Scraping video pages...")
    rows = []
    seen = set()

    for i, vid in enumerate(video_ids):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(video_ids)}]...", flush=True)

        info = _scrape_video_page(vid)
        if not info:
            continue

        title = info["title"]
        desc = info["description"]

        if not is_relevant(title, desc):
            continue

        if title.lower() in seen:
            continue
        seen.add(title.lower())

        views = info["views"]
        likes = info["likes"]
        comments_count = info["comments"]
        date = format_date(info["published"])
        engagement = likes + comments_count
        raw_text = f"{title}. {desc}" if desc else title
        text = clean_text(raw_text)

        if len(text) < 10:
            continue

        rows.append({
            "platform": "youtube", "text": text, "likes": likes,
            "comments": comments_count, "views": views, "date": date,
            "engagement": engagement, "content_type": "video",
            "url": f"https://www.youtube.com/watch?v={vid}",
        })

        time.sleep(random.uniform(0.5, 1.5))

    print(f"\n[3/3] Saving...")
    save_csv(rows, OUTPUT)
    print(f"\n  {OUTPUT}: {len(rows)} rows")

    if rows:
        top = sorted(rows, key=lambda r: r["engagement"], reverse=True)[:5]
        print("\n  Top 5 by engagement:")
        for i, row in enumerate(top, 1):
            print(f"    {i}. {row['text'][:70]}... (eng={row['engagement']:,})")

    print("=" * 60)


if __name__ == "__main__":
    main()
