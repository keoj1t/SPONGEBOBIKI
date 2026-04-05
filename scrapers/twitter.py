import os
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN_TWITTER", "")

SEARCH_QUERY = (
    '"Claude AI" OR "Anthropic Claude" OR "Claude 3" OR "Claude Opus" '
    'OR "Claude Sonnet" OR "Claude vs ChatGPT" OR "Claude vs GPT-4" '
    'OR "Claude coding" OR "Claude API" OR "switched to Claude" '
    'OR "Claude is better" OR "Claude underrated" OR "Anthropic update" '
    'lang:en'
)

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "twitter.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
TARGET_ROWS = 300


def _first_positive_int(obj, *keys):
    """Return first positive int from given keys."""
    for k in keys:
        val = obj.get(k)
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
        print("[!] APIFY_TOKEN_TWITTER not set in .env — skipping Twitter.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"[*] Twitter/X scraper (altimis/scweet) — target {TARGET_ROWS} rows")

    run_input = {
        "source_mode": "search",
        "search_query": SEARCH_QUERY,
        "search_sort": "Top",
        "max_items": TARGET_ROWS + 100,  # buffer for filtered-out tweets
    }

    all_entries = []
    _dumped_first = False

    try:
        print("[*] Sending request to Apify cloud… this may take a few minutes.")
        run = client.actor("altimis/scweet").call(run_input=run_input)

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

            # text can be at top level or nested under tweet
            tweet_obj = item.get("tweet", {}) or {}
            text = (item.get("text", "") or tweet_obj.get("text", "")
                    or item.get("full_text", "") or tweet_obj.get("full_text", "") or "").replace("\n", " ").strip()

            if not text or len(text) < 10:
                continue

            # language filter
            if len(text) > 20:
                try:
                    if detect(text) != "en":
                        continue
                except LangDetectException:
                    pass

            likes = (_first_positive_int(item, "favorite_count", "favourites_count", "likes", "likesCount", "likeCount")
                     or _first_positive_int(tweet_obj, "favorite_count", "favourites_count", "likes"))
            comments = (_first_positive_int(item, "reply_count", "replies", "repliesCount", "commentCount")
                        or _first_positive_int(tweet_obj, "reply_count", "replies"))
            retweets = (_first_positive_int(item, "retweet_count", "retweets", "retweetsCount", "shareCount")
                        or _first_positive_int(tweet_obj, "retweet_count", "retweets"))
            views = (_first_positive_int(item, "view_count", "views", "viewCount", "impressions")
                     or _first_positive_int(tweet_obj, "view_count", "views"))
            bookmarks = (_first_positive_int(item, "bookmark_count", "bookmarks")
                         or _first_positive_int(tweet_obj, "bookmark_count", "bookmarks"))

            raw_date = tweet_obj.get("created_at", "") or item.get("created_at", "") or item.get("date", "")
            if raw_date:
                try:
                    dt = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %z %Y")
                    date_str = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    date_str = str(raw_date)[:10]
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")

            tweet_url = (
                item.get("url", "") or item.get("tweet_url", "")
                or tweet_obj.get("url", "") or item.get("link", "") or ""
            )
            # construct URL from tweet id if missing
            if not tweet_url:
                tweet_id = item.get("id_str", "") or item.get("id", "") or tweet_obj.get("id_str", "")
                user = (item.get("user", {}) or {}).get("screen_name", "") or item.get("username", "")
                if tweet_id and user:
                    tweet_url = f"https://x.com/{user}/status/{tweet_id}"

            all_entries.append({
                "platform": "twitter",
                "text": text,
                "likes": likes,
                "comments": comments,
                "views": views,
                "date": date_str,
                "engagement": likes + comments + retweets + bookmarks,
                "content_type": "tweet",
                "url": tweet_url,
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
        print("[!] No data returned. Check APIFY_TOKEN_TWITTER / free-tier balance.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)


if __name__ == "__main__":
    main()
