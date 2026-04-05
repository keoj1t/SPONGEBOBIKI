import os
import json
import pandas as pd
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN_LINKEDIN", "")
SEARCH_KEYWORDS = ["Claude AI", "Anthropic Claude", "Claude vs ChatGPT", "Claude AI enterprise"]
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "linkedin.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
TARGET_ROWS = 300
POSTS_PER_QUERY = 100


def _deep_get(obj, dotted_key, default=None):
    """Traverse nested dicts via dotted key path, e.g. 'socialActivity.numLikes'."""
    parts = dotted_key.split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return default
    return cur if cur is not None else default


def _find_int(item, *key_paths):
    """Return FIRST positive int found across many dotted-key paths, else 0."""
    for kp in key_paths:
        val = _deep_get(item, kp)
        if val is None:
            continue
        try:
            n = int(val)
            if n > 0:
                return n
        except (ValueError, TypeError):
            pass
    return 0


def _find_str(item, *key_paths):
    """Return first non-empty string found across key paths."""
    for kp in key_paths:
        val = _deep_get(item, kp)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def main():
    if not APIFY_TOKEN:
        print("[!] APIFY_TOKEN_LINKEDIN not set in .env — skipping LinkedIn.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"[*] LinkedIn Apify scraper — target {TARGET_ROWS} rows, {len(SEARCH_KEYWORDS)} keywords")

    all_entries = []
    _dumped_first = False

    for kw in SEARCH_KEYWORDS:
        if len(all_entries) >= TARGET_ROWS:
            break

        run_input = {
            "keyword": kw,
            "sort_type": "relevance",
            "total_posts": POSTS_PER_QUERY,
        }

        try:
            print(f"[*] Searching: '{kw}' ...")
            run = client.actor("apimaestro/linkedin-posts-search-scraper-no-cookies").call(run_input=run_input)

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

                # --- TEXT ---
                text = _find_str(
                    item,
                    "text", "content", "commentary", "post_text",
                    "commentary.text", "commentary.text.text",
                    "postText", "description", "message",
                )
                if not text:
                    text = ""
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

                # --- ENGAGEMENT (try every known LinkedIn Apify field path) ---
                reactions = _find_int(
                    item,
                    "totalReactionCount", "numLikes", "reactions", "likes",
                    "likeCount", "reactionCount", "likesCount",
                    "socialActivity.totalReactionCount",
                    "socialActivity.numLikes",
                    "socialActivity.reactionCount",
                    "socialDetail.totalSocialActivityCounts.numLikes",
                    "socialDetail.likes",
                    "socialContent.totalReactionCount",
                    "socialContent.numLikes",
                    "stats.total_reactions", "stats.likes", "stats.reactions",
                    "activity.likes", "activity.reactions",
                )
                comments_count = _find_int(
                    item,
                    "numComments", "comments", "commentsCount", "commentCount",
                    "socialActivity.totalComments",
                    "socialActivity.numComments",
                    "socialActivity.commentCount",
                    "socialDetail.totalSocialActivityCounts.numComments",
                    "socialDetail.comments",
                    "socialContent.totalComments",
                    "socialContent.numComments",
                    "stats.comments", "stats.totalComments",
                    "activity.comments",
                )
                impressions = _find_int(
                    item,
                    "impressionCount", "impressions", "views", "numViews",
                    "viewCount", "numImpressions",
                    "socialActivity.impressionCount",
                    "socialDetail.impressions",
                    "stats.views", "stats.impressions", "stats.viewCount",
                    "activity.views",
                )
                reposts = _find_int(
                    item,
                    "repostCount", "numShares", "shares", "shareCount",
                    "repostsCount", "sharesCount",
                    "socialActivity.totalShares",
                    "socialActivity.numShares",
                    "socialDetail.totalSocialActivityCounts.numShares",
                    "socialContent.totalShares",
                    "stats.shares", "stats.reposts",
                    "activity.shares",
                )

                # --- DATE ---
                raw_date = _find_str(
                    item,
                    "postedAt", "date", "postedDate", "publishedAt",
                    "posted_at.date", "posted_at.display_text",
                    "postedDateTimestamp", "createdAt", "created_at",
                    "timestamp", "time", "publishDate",
                )
                if not raw_date:
                    # try numeric timestamp
                    ts = _find_int(
                        item,
                        "postedTimestamp", "postedDateTimestamp",
                        "posted_at.timestamp",
                        "createdAt", "timestamp", "created_at",
                    )
                    if ts > 0:
                        raw_date = ts

                if isinstance(raw_date, (int, float)) and raw_date > 1e9:
                    if raw_date > 1e12:
                        raw_date = raw_date / 1000
                    date_str = datetime.utcfromtimestamp(raw_date).strftime("%Y-%m-%d")
                elif isinstance(raw_date, str) and raw_date:
                    date_str = raw_date[:10]
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")

                content_type = "article" if _find_str(item, "articleLink", "article", "articleUrl") else "post"

                # --- URL ---
                post_url = _find_str(
                    item,
                    "post_url", "postUrl", "url", "shareUrl", "postLink",
                    "link", "permalink", "canonicalUrl",
                )

                all_entries.append({
                    "platform": "linkedin",
                    "text": text,
                    "likes": reactions,
                    "comments": comments_count,
                    "views": impressions,
                    "date": date_str,
                    "engagement": reactions + comments_count + reposts,
                    "content_type": content_type,
                    "url": post_url,
                })

        except Exception as e:
            print(f"[!] Apify error for '{kw}': {e}")

    # --- STATS ---
    if all_entries:
        total_eng = sum(e["engagement"] for e in all_entries)
        non_zero = sum(1 for e in all_entries if e["engagement"] > 0)
        print(f"[STATS] {len(all_entries)} rows, {non_zero} with engagement>0, total engagement={total_eng}")
        if non_zero == 0:
            print("[WARNING] All engagement = 0! The Apify actor may have changed its output schema.")
            print("[WARNING] Check the [DEBUG] output above for actual field names.")

    if all_entries:
        df = pd.DataFrame(all_entries).head(TARGET_ROWS)
        df.to_csv(OUTPUT, index=False, columns=FIELDNAMES)
        print(f"[OK] {OUTPUT} saved — {len(df)} rows")
    else:
        print("[!] No data returned. Check APIFY_TOKEN_LINKEDIN / free-tier balance.")
        pd.DataFrame(columns=FIELDNAMES).to_csv(OUTPUT, index=False)


if __name__ == "__main__":
    main()
