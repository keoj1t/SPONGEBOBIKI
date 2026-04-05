import os
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN_INSTAGRAM", "")
HASHTAGS = [
    "claudeai",
    "anthropicclaude",
    "claude3",
    "claude35",
    "claudesonnet",
    "claudeopus",
    "claudehaiku",
    "claudevschatgpt",
    "claudevsgpt4",
    "chatgptvsclaude",
    "claudecoding",
    "claudedev",
    "claudeprogramming",
    "claudeproductivity",
    "claudeworkflow",
    "usingclaude",
    "claudeprompts",
    "claudetips",
]
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "instagram.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
TARGET_ROWS = 300
RESULTS_PER_HASHTAG = 50


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


def main():
    if not APIFY_TOKEN:
        print("[!] APIFY_TOKEN_INSTAGRAM not set in .env — skipping Instagram.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"[*] Instagram Apify scraper — target {TARGET_ROWS} rows, {len(HASHTAGS)} hashtags")

    all_entries = []
    _dumped_first = False

    # Use keyword search via the official Instagram Hashtag Scraper
    run_input = {
        "hashtags": HASHTAGS,
        "resultsType": "posts",
        "resultsLimit": RESULTS_PER_HASHTAG,
        "keywordSearch": True,
    }

    try:
        print(f"[*] Sending request to Apify cloud… this may take a few minutes.")
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if len(all_entries) >= TARGET_ROWS:
                break

            # --- DEBUG: dump first item so we can see actual field names ---
            if not _dumped_first:
                _dumped_first = True
                print("[DEBUG] First item keys:", list(item.keys()))
                for k, v in item.items():
                    preview = str(v)[:120] if v is not None else "None"
                    print(f"  {k}: {preview}")

            text = (
                item.get("caption", "")
                or item.get("text", "")
                or item.get("alt", "")
                or ""
            )
            text = text.replace("\n", " ").strip()

            if not text or len(text) < 10:
                continue

            # skip non-English
            if len(text) > 20:
                try:
                    if detect(text) != "en":
                        continue
                except LangDetectException:
                    pass

            # --- ENGAGEMENT: try multiple field names, pick first > 0 ---
            likes = _first_positive_int(item, "likesCount", "likes", "likeCount", "edge_media_preview_like.count")
            comments_count = _first_positive_int(item, "commentsCount", "comments", "commentCount", "edge_media_to_comment.count")
            views = _first_positive_int(item, "videoViewCount", "videoPlayCount", "views", "viewCount", "playCount")
            shares = _first_positive_int(item, "sharesCount", "shares", "shareCount", "savesCount", "saves")

            raw_date = item.get("timestamp", "") or item.get("takenAt", "") or item.get("date", "")
            if isinstance(raw_date, (int, float)):
                if raw_date > 1e12:
                    raw_date = raw_date / 1000
                date_str = datetime.utcfromtimestamp(raw_date).strftime("%Y-%m-%d")
            else:
                date_str = str(raw_date)[:10] if raw_date else datetime.now().strftime("%Y-%m-%d")

            post_type = item.get("type", "post")
            if post_type == "Sidecar":
                content_type = "carousel_album"
            elif post_type == "Video" or item.get("isVideo"):
                content_type = "reel"
            else:
                content_type = "post"

            shortcode = item.get("shortCode", "") or item.get("shortcode", "") or item.get("code", "")
            post_url = item.get("url", "") or item.get("webInfoUrl", "") or item.get("permalink", "")
            if not post_url and shortcode:
                post_url = f"https://www.instagram.com/p/{shortcode}/"

            all_entries.append({
                "platform": "instagram",
                "text": text,
                "likes": likes,
                "comments": comments_count,
                "views": views,
                "date": date_str,
                "engagement": likes + comments_count + shares,
                "content_type": content_type,
                "url": post_url,
            })

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
        print("[!] No data returned. Check APIFY_TOKEN_INSTAGRAM / free-tier balance.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)


if __name__ == "__main__":
    main()
