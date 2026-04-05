import os
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
SEARCH_QUERIES = ["Claude AI", "Anthropic Claude", "Claude AI review", "Claude vs ChatGPT"]
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "tiktok.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
TARGET_ROWS = 300
RESULTS_PER_QUERY = 100  # videos per search query


def _first_positive_int(item, *keys):
    """Return first positive int from given top-level keys, then try 'stats' sub-dict."""
    for k in keys:
        val = item.get(k)
        if val is not None:
            try:
                n = int(val)
                if n > 0:
                    return n
            except (ValueError, TypeError):
                pass
    # fallback: try inside "stats" sub-dict
    stats = item.get("stats") or item.get("statistics") or {}
    if isinstance(stats, dict):
        for k in keys:
            val = stats.get(k)
            if val is not None:
                try:
                    n = int(val)
                    if n > 0:
                        return n
                except (ValueError, TypeError):
                    pass
    return 0


def main():
    if not APIFY_TOKEN:
        print("[!] APIFY_TOKEN not set in .env — skipping TikTok.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"[*] TikTok Apify scraper — target {TARGET_ROWS} rows, {len(SEARCH_QUERIES)} queries")

    run_input = {
        "searchQueries": SEARCH_QUERIES,
        "resultsPerPage": RESULTS_PER_QUERY,
        "searchSection": "/video",
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    }

    all_entries = []
    _dumped_first = False

    try:
        print("[*] Sending request to Apify cloud… this may take a few minutes.")
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)

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

            likes    = _first_positive_int(item, "diggCount", "likesCount", "likes", "likeCount", "heartCount")
            comments = _first_positive_int(item, "commentCount", "commentsCount", "comments", "replyCount")
            views    = _first_positive_int(item, "playCount", "viewCount", "views", "playCountStr")
            shares   = _first_positive_int(item, "shareCount", "sharesCount", "shares", "forwardCount")

            desc = (item.get("text", "") or item.get("desc", "") or item.get("description", "") or "").replace("\n", " ").strip()

            # skip non-English posts
            if len(desc) > 20:
                try:
                    if detect(desc) != "en":
                        continue
                except LangDetectException:
                    pass

            raw_date = item.get("createTimeISO", "") or item.get("createTime", "")

            if isinstance(raw_date, (int, float)):
                date_str = datetime.utcfromtimestamp(raw_date).strftime("%Y-%m-%d")
            else:
                date_str = str(raw_date)[:10] if raw_date else datetime.now().strftime("%Y-%m-%d")

            post_url = (item.get("webVideoUrl", "") or item.get("url", "")
                        or item.get("link", "") or item.get("videoUrl", "") or "")
            # construct URL from author + id if missing
            if not post_url:
                author = item.get("authorMeta", {}).get("name", "") or item.get("author", {}).get("uniqueId", "")
                video_id = item.get("id", "")
                if author and video_id:
                    post_url = f"https://www.tiktok.com/@{author}/video/{video_id}"

            all_entries.append({
                "platform": "tiktok",
                "text": desc,
                "likes": likes,
                "comments": comments,
                "views": views,
                "date": date_str,
                "engagement": likes + comments + shares,
                "content_type": "video",
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
        print("[!] No data returned. Check APIFY_TOKEN / free-tier balance.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)


if __name__ == "__main__":
    main()