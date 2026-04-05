import csv
import os
import re

from langdetect import detect, LangDetectException

from core import config
from core import log


def safe_int(val):
    if val is None:
        return 0
    val = str(val).strip().replace(",", "")
    if not val or val.lower() in ("nan", "none", "null", ""):
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def normalize_date(raw):
    if raw is None:
        return ""
    raw = str(raw).strip()
    if not raw:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T\s]", raw)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", raw)
    if m:
        mm, dd, yyyy = m.groups()
        return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", raw)
    if m:
        dd, mm, yyyy = m.groups()
        return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
    return raw


def clean_text(text):
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_english(text):
    if len(text) < config.MIN_TEXT_LENGTH_FOR_DETECTION:
        return True
    try:
        return detect(text) == config.LANGUAGE
    except LangDetectException:
        return False


def normalize_content_type(platform_name, raw_value):
    value = (raw_value or "").strip().lower()
    if value:
        return value
    defaults = {
        "youtube": "video", "tiktok": "post",
        "linkedin": "post", "reddit": "post",
        "twitter": "post", "instagram": "post",
        "threads": "thread",
    }
    return defaults.get(platform_name, "post")


def load_platform(platform_name, filepath):
    if not os.path.exists(filepath):
        log.warn(f"File missing: {filepath}")
        return [], 0

    rows, skipped = [], 0
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            text = clean_text(raw.get("text", ""))
            if not text:
                continue
            if not is_english(text):
                skipped += 1
                continue

            likes = safe_int(raw.get("likes"))
            comments = safe_int(raw.get("comments"))
            views = safe_int(raw.get("views"))
            date = normalize_date(raw.get("date", ""))
            eng_raw = safe_int(raw.get("engagement"))
            engagement = eng_raw if eng_raw > 0 else likes + comments

            rows.append({
                "platform": platform_name,
                "text": text,
                "likes": likes,
                "comments": comments,
                "views": views,
                "date": date,
                "engagement": engagement,
                "content_type": normalize_content_type(platform_name, raw.get("content_type")),
                "url": (raw.get("url") or "").strip(),
                "text_length": len(text),
            })
    return rows, skipped


def deduplicate(rows):
    seen, out = set(), []
    for r in rows:
        key = r["text"].strip().lower()[:200]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def merge_datasets(append=False):
    log.section("MERGE & CLEAN")

    platforms = ["reddit", "youtube", "tiktok", "twitter", "instagram", "linkedin", "threads"]
    all_rows = []
    stats = {}

    if append and os.path.exists(config.MERGED_DATASET):
        log.info("Append mode: loading existing dataset for dedup")
        with open(config.MERGED_DATASET, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                all_rows.append(raw)
        log.info(f"  Existing rows: {len(all_rows)}")

    for name in platforms:
        path = os.path.join(config.DATA_RAW, f"{name}.csv")
        rows, skipped = load_platform(name, path)
        before = len(rows)
        rows = deduplicate(rows)
        after = len(rows)
        stats[name] = {"loaded": before, "deduped": after, "skipped_lang": skipped}
        log.info(f"{name:12s}  eng={before:>5}  dedup={after:>5}  skipped={skipped:>4}")
        all_rows.extend(rows)

    all_rows = deduplicate(all_rows)
    total = len(all_rows)
    log.ok(f"Total merged rows: {total}")

    if total == 0:
        log.warn("No rows after merge — check raw data")
        return [], stats

    os.makedirs(config.DATA_FINAL, exist_ok=True)
    with open(config.MERGED_DATASET, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=config.FINAL_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    log.ok(f"Saved -> {config.MERGED_DATASET}")
    return all_rows, stats
