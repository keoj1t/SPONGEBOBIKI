import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import csv
import datetime
import html
import time
import random
import json

SUBREDDITS = ["ClaudeAI", "Anthropic", "ChatGPT", "artificial", "LocalLLaMA", "MachineLearning"]
QUERIES = ["Claude AI", "Anthropic Claude"]
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "reddit.csv")
FIELDNAMES = ["platform", "text", "likes", "comments", "views", "date", "engagement", "content_type", "url"]
MAX_COMMENTS_PER_POST = 20
TARGET_ROWS = 300


def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": f"ClaudeGrowthBot/1.0 (research project; contact: student@uni.edu) python-requests/{requests.__version__}",
        "Accept": "application/json",
    })
    retries = Retry(total=5, backoff_factor=5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def clean_text(title, selftext):
    title = html.unescape((title or "")).strip()
    selftext = html.unescape((selftext or "")).strip()
    if selftext in ("[removed]", "[deleted]"):
        selftext = ""
    if title in ("[removed]", "[deleted]", ""):
        return None
    return f"{title}. {selftext}" if selftext else title


def format_date(created_utc):
    if not created_utc:
        return ""
    return datetime.datetime.fromtimestamp(
        created_utc, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")


def make_post_row(text, score, num_comments, created_utc, url=""):
    likes = int(score or 0)
    comments = int(num_comments or 0)
    return {
        "platform": "reddit",
        "text": text,
        "likes": likes,
        "comments": comments,
        "views": 0,
        "date": format_date(created_utc),
        "engagement": likes + comments,
        "content_type": "post",
        "url": url,
    }


def make_comment_row(text, score, created_utc, comment_id="", parent_permalink=""):
    likes = int(score or 0)
    url = ""
    if parent_permalink:
        url = f"https://reddit.com{parent_permalink}"
        if comment_id:
            url += f"?comment={comment_id}"
    return {
        "platform": "reddit",
        "text": text,
        "likes": likes,
        "comments": 0,
        "views": 0,
        "date": format_date(created_utc),
        "engagement": likes,
        "content_type": "comment",
        "url": url,
    }


def _fetch_json(session, url, params=None):
    time.sleep(random.uniform(2, 5))
    resp = session.get(url, params=params or {}, timeout=30)
    if resp.status_code == 429:
        wait = int(resp.headers.get("Retry-After", 60))
        print(f"    [429] Rate limited, waiting {wait}s...")
        time.sleep(wait + 5)
        resp = session.get(url, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def scrape_posts(session):
    seen_ids = set()
    posts = []
    permalinks = []

    # Subreddit hot/top posts
    for sub in SUBREDDITS:
        if len(posts) >= TARGET_ROWS:
            break
        for sort in ["hot", "top"]:
            print(f"[SUB] r/{sub}/{sort}...", end=" ", flush=True)
            try:
                data = _fetch_json(session,
                    f"https://www.reddit.com/r/{sub}/{sort}.json",
                    {"limit": 100, "t": "year"})
            except Exception as e:
                print(f"Error: {e}")
                continue

            fetched = 0
            for item in data.get("data", {}).get("children", []):
                raw = item.get("data", {})
                post_id = raw.get("id", "")
                if post_id in seen_ids:
                    continue

                title = (raw.get("title") or "").lower()
                selftext = (raw.get("selftext") or "").lower()
                combined = title + " " + selftext
                # only keep Claude/Anthropic posts
                if not any(kw in combined for kw in ["claude", "anthropic", "sonnet", "opus", "haiku"]):
                    continue

                text = clean_text(raw.get("title"), raw.get("selftext"))
                if text is None:
                    continue

                seen_ids.add(post_id)
                permalink = raw.get("permalink", "")
                posts.append(make_post_row(text, raw.get("score", 0), raw.get("num_comments", 0), raw.get("created_utc", 0), f"https://reddit.com{permalink}" if permalink else ""))
                permalinks.append(permalink)
                fetched += 1

            print(f"{fetched} posts")
            time.sleep(random.uniform(2, 4))

    # Fallback: search API
    if len(posts) < TARGET_ROWS:
        for query in QUERIES:
            if len(posts) >= TARGET_ROWS:
                break
            print(f"[SEARCH] '{query}'...", end=" ", flush=True)
            try:
                data = _fetch_json(session,
                    "https://www.reddit.com/search.json",
                    {"q": query, "sort": "relevance", "t": "all", "limit": 100, "type": "link"})
            except Exception as e:
                print(f"Error: {e}")
                continue

            fetched = 0
            for item in data.get("data", {}).get("children", []):
                raw = item.get("data", {})
                post_id = raw.get("id", "")
                if post_id in seen_ids:
                    continue
                text = clean_text(raw.get("title"), raw.get("selftext"))
                if text is None:
                    continue
                seen_ids.add(post_id)
                permalink = raw.get("permalink", "")
                posts.append(make_post_row(text, raw.get("score", 0), raw.get("num_comments", 0), raw.get("created_utc", 0), f"https://reddit.com{permalink}" if permalink else ""))
                permalinks.append(permalink)
                fetched += 1
            print(f"{fetched} posts")
            time.sleep(random.uniform(3, 6))

    print(f"\n  Total posts collected: {len(posts)}")
    return posts, permalinks


def extract_comments(comment_data, results, depth=0, parent_permalink=""):
    if not isinstance(comment_data, dict):
        return
    kind = comment_data.get("kind", "")
    data = comment_data.get("data", {})

    if kind == "t1":
        body = html.unescape((data.get("body") or "")).strip()
        if body and body not in ("[removed]", "[deleted]"):
            comment_id = data.get("id", "")
            permalink = data.get("permalink", "") or parent_permalink
            results.append(make_comment_row(body, data.get("score", 0), data.get("created_utc", 0),
                                            comment_id=comment_id, parent_permalink=permalink))
        replies = data.get("replies")
        if isinstance(replies, dict):
            for child in replies.get("data", {}).get("children", []):
                extract_comments(child, results, depth + 1, parent_permalink=parent_permalink)
    elif kind == "Listing":
        for child in data.get("children", []):
            extract_comments(child, results, depth, parent_permalink=parent_permalink)


def scrape_comments(session, permalinks, max_posts=100):
    comments = []
    count = min(len(permalinks), max_posts)
    print(f"\n[COMMENTS] Fetching from {count} posts...")

    for i, permalink in enumerate(permalinks[:count]):
        if not permalink:
            continue
        try:
            time.sleep(random.uniform(2, 5))
            url = f"https://old.reddit.com{permalink}.json"
            resp = session.get(url, params={"limit": MAX_COMMENTS_PER_POST, "sort": "top"}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [{i+1}/{count}] Error: {e}")
            time.sleep(5)
            continue

        if isinstance(data, list) and len(data) > 1:
            before = len(comments)
            extract_comments(data[1], comments, parent_permalink=permalink)
            got = len(comments) - before
            if (i + 1) % 20 == 0 or i == 0:
                print(f"  [{i+1}/{count}] +{got} comments (total: {len(comments)})")
        time.sleep(random.uniform(2, 4))

    print(f"  Total comments: {len(comments)}")
    return comments


def deduplicate(rows):
    seen = set()
    result = []
    for r in rows:
        text = r.get("text", "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(r)
    return result


def save_csv(rows, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("=" * 55)
    print("Reddit Scraper — Claude AI (posts + comments)")
    print("=" * 55)

    session = create_session()

    posts, permalinks = scrape_posts(session)

    # limit comments fetching to keep total ~300
    remaining = max(0, TARGET_ROWS - len(posts))
    if remaining > 0:
        max_comment_posts = min(len(permalinks), 15)
        comments = scrape_comments(session, permalinks, max_posts=max_comment_posts)
    else:
        comments = []

    all_rows = posts + comments
    print(f"\nCollected: {len(all_rows)} (posts: {len(posts)}, comments: {len(comments)})")

    clean = deduplicate(all_rows)
    clean.sort(key=lambda x: x["engagement"], reverse=True)
    clean = clean[:TARGET_ROWS]
    print(f"After dedup + cap: {len(clean)}")

    n_posts = sum(1 for r in clean if r["content_type"] == "post")
    n_comments = sum(1 for r in clean if r["content_type"] == "comment")
    print(f"  Posts: {n_posts} | Comments: {n_comments}")

    save_csv(clean, OUTPUT_FILE)
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
