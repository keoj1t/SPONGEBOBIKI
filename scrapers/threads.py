import os
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN_THREADS", "")

SEARCH_KEYWORDS = [
    "Claude AI",
    "Anthropic Claude",
    "Claude Sonnet",
    "Claude Opus",
    "Claude vs ChatGPT",
    "Claude coding",
    "Claude API",
    "#ClaudeAI",
    "#Anthropic",
    "Claude AI review",
    "Claude AI productivity",
    "switched to Claude",
    "Claude is better",
    "Claude developer",
    "Claude prompts",
]
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "threads.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
TARGET_ROWS = 300
MAX_PER_KEYWORD = 40


def _first_positive_int(item, *keys):
    """Return first positive int from given top-level keys."""
    for k in keys:
        val = item.get(k)
        if val is None:
            continue
        try:
            n = int(val)
            if n > 0:
                return n
        except (ValueError, TypeError):
            pass
    return 0


def _parse_item(item):
    text = (item.get("text", "")
            or item.get("caption", "")
            or item.get("text_content", "")
            or item.get("content", "")
            or "").replace("\n", " ").strip()

    if not text or len(text) < 10:
        return None

    # skip non-English
    if len(text) > 20:
        try:
            if detect(text) != "en":
                return None
        except LangDetectException:
            pass

    likes = _first_positive_int(item, "like_count", "likes", "likesCount", "likeCount",
                                "heart_count", "reactions")
    comments = _first_positive_int(item, "reply_count", "comment_count", "comments",
                                   "commentsCount", "replies", "repliesCount")
    reposts = _first_positive_int(item, "repost_count", "reposts", "repostsCount",
                                  "share_count", "shares", "sharesCount", "quote_count")
    views = _first_positive_int(item, "view_count", "views", "viewCount",
                                "impressions", "reach")

    raw_date = item.get("created_at", "") or item.get("timestamp", "")
    if raw_date:
        try:
            if isinstance(raw_date, (int, float)):
                date_str = datetime.utcfromtimestamp(raw_date).strftime("%Y-%m-%d")
            else:
                date_str = str(raw_date)[:10]
        except (ValueError, TypeError):
            date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    return {
        "platform": "threads",
        "text": text,
        "likes": likes,
        "comments": comments,
        "views": views,
        "date": date_str,
        "engagement": likes + comments + reposts,
        "content_type": "thread",
        "url": (item.get("url", "") or item.get("post_url", "")
                or item.get("link", "") or item.get("permalink", "") or ""),
    }


def main():
    if not APIFY_TOKEN:
        print("[!] APIFY_TOKEN_THREADS not set in .env — skipping Threads.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"[*] Threads scraper (watcher.data) — target {TARGET_ROWS} rows, {len(SEARCH_KEYWORDS)} keywords")

    run_input = {
        "keywords": SEARCH_KEYWORDS,
        "maxItemsPerKeyword": MAX_PER_KEYWORD,
        "sortByRecent": False,
        "outputFormat": "json",
    }

    all_entries = []
    seen_texts = set()
    _dumped_first = False

    try:
        print("[*] Sending request to Apify cloud… this may take a few minutes.")
        run = client.actor("watcher.data/search-threads-by-keywords").call(run_input=run_input)

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if len(all_entries) >= TARGET_ROWS:
                break

            # --- DEBUG: dump first item ---
            if not _dumped_first:
                _dumped_first = True
                print("[DEBUG] First item keys:", list(item.keys()))
                for k, v in item.items():
                    preview = str(v)[:120] if v is not None else "None"
                    print(f"  {k}: {preview}")

            row = _parse_item(item)
            if row is None:
                continue

            key = row["text"][:80]
            if key in seen_texts:
                continue
            seen_texts.add(key)

            all_entries.append(row)

    except Exception as e:
        print(f"[!] Apify error: {e}")

    if all_entries:
        total_eng = sum(e["engagement"] for e in all_entries)
        non_zero = sum(1 for e in all_entries if e["engagement"] > 0)
        with_url = sum(1 for e in all_entries if e["url"])
        print(f"[STATS] {len(all_entries)} rows | {non_zero} with engagement>0 | {with_url} with URL | total engagement={total_eng}")
        df = pd.DataFrame(all_entries).head(TARGET_ROWS)
        df.to_csv(OUTPUT, index=False, columns=FIELDNAMES)
        print(f"[OK] {OUTPUT} saved — {len(df)} rows")
    else:
        print("[!] No data returned. Check APIFY_TOKEN_THREADS / free-tier balance.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)


if __name__ == "__main__":
    main()
