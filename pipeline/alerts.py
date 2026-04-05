import json
import os
from datetime import datetime

import pandas as pd

from core import config
from core import log


def _load():
    if not os.path.exists(config.MERGED_DATASET):
        return pd.DataFrame()
    df = pd.read_csv(config.MERGED_DATASET)
    for col in ["likes", "comments", "views", "engagement"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["parsed_date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    return df


def check_engagement_spikes(df):
    alerts = []
    dated = df[df["parsed_date"].notna()].copy()
    if dated.empty:
        return alerts

    daily = dated.groupby(dated["parsed_date"].dt.date)["engagement"].sum().sort_index()
    if len(daily) < 7:
        return alerts

    rolling_mean = daily.rolling(window=7, min_periods=3).mean()
    rolling_std = daily.rolling(window=7, min_periods=3).std()

    for i in range(7, len(daily)):
        curr = daily.iloc[i]
        mean_val = rolling_mean.iloc[i - 1]
        std_val = rolling_std.iloc[i - 1]
        prev = daily.iloc[i - 1]

        if std_val > 0 and curr > mean_val + 3 * std_val and curr > 500 and prev > 0:
            ratio = curr / prev
            if ratio >= config.ALERT_ENGAGEMENT_SPIKE_MULTIPLIER:
                alerts.append({
                    "type": "engagement_spike",
                    "severity": "high",
                    "date": str(daily.index[i]),
                    "message": f"Engagement spiked {ratio:.1f}x on {daily.index[i]} "
                               f"({int(prev)} -> {int(curr)}, 7d avg: {int(mean_val)})",
                    "value": int(curr),
                    "previous": int(prev),
                })

    alerts.sort(key=lambda x: x.get("value", 0), reverse=True)
    return alerts[:15]


def check_mention_spikes(df):
    alerts = []
    dated = df[df["parsed_date"].notna()].copy()
    if dated.empty:
        return alerts

    daily = dated.groupby(dated["parsed_date"].dt.date).size().sort_index()
    if len(daily) < 7:
        return alerts

    rolling_mean = daily.rolling(window=7, min_periods=3).mean()
    rolling_std = daily.rolling(window=7, min_periods=3).std()

    for i in range(7, len(daily)):
        curr = daily.iloc[i]
        mean_val = rolling_mean.iloc[i - 1]
        std_val = rolling_std.iloc[i - 1]
        prev = daily.iloc[i - 1]

        if std_val > 0 and curr > mean_val + 2.5 * std_val and curr >= 5 and prev > 0:
            alerts.append({
                "type": "mention_spike",
                "severity": "medium",
                "date": str(daily.index[i]),
                "message": f"Mentions jumped {curr / prev:.1f}x on {daily.index[i]} "
                           f"({prev} -> {curr} posts, 7d avg: {mean_val:.0f})",
                "value": int(curr),
                "previous": int(prev),
            })

    alerts.sort(key=lambda x: x.get("value", 0), reverse=True)
    return alerts[:10]


def check_keyword_trends(df):
    alerts = []
    dated = df[df["parsed_date"].notna()].copy()
    if dated.empty or len(dated) < 20:
        return alerts

    dated = dated.sort_values("parsed_date")
    cutoff = len(dated) // 2
    older = dated.iloc[:cutoff]
    newer = dated.iloc[cutoff:]

    text_old = older["text"].fillna("").str.lower()
    text_new = newer["text"].fillna("").str.lower()

    for kw in config.KEYWORDS:
        old_count = text_old.str.contains(rf"\b{kw}\b", regex=True, na=False).sum()
        new_count = text_new.str.contains(rf"\b{kw}\b", regex=True, na=False).sum()

        old_rate = old_count / max(len(older), 1)
        new_rate = new_count / max(len(newer), 1)

        if old_rate > 0 and new_rate / old_rate >= 2.0:
            alerts.append({
                "type": "keyword_trending",
                "severity": "medium",
                "message": f'Keyword "{kw}" trending up — '
                           f'{new_rate / old_rate:.1f}x more frequent in recent data '
                           f'({old_count} -> {new_count})',
                "keyword": kw,
            })

        if old_count == 0 and new_count >= 5:
            alerts.append({
                "type": "keyword_new",
                "severity": "low",
                "message": f'New keyword detected: "{kw}" appeared {new_count} times in recent data',
                "keyword": kw,
            })

    return alerts


def check_viral_posts(df):
    alerts = []
    medians = df.groupby("platform")["engagement"].median()

    for _, row in df.iterrows():
        platform = row["platform"]
        med = medians.get(platform, 0)
        if med > 0 and row["engagement"] > med * 50:
            alerts.append({
                "type": "viral_post",
                "severity": "info",
                "message": f"Viral post on {platform}: {int(row['engagement'])} engagement "
                           f"(median {int(med)}) — {str(row['text'])[:60]}...",
                "platform": platform,
                "engagement": int(row["engagement"]),
            })

    alerts.sort(key=lambda x: x.get("engagement", 0), reverse=True)
    return alerts[:5]


def run_alerts():
    log.section("ALERT DETECTION")
    df = _load()
    if df.empty:
        log.warn("No data for alerts")
        return []

    all_alerts = []
    all_alerts.extend(check_engagement_spikes(df))
    all_alerts.extend(check_mention_spikes(df))
    all_alerts.extend(check_keyword_trends(df))
    all_alerts.extend(check_viral_posts(df))

    seen = set()
    unique = []
    for a in all_alerts:
        if a["message"] not in seen:
            seen.add(a["message"])
            unique.append(a)
    all_alerts = unique

    os.makedirs(config.ALERTS_DIR, exist_ok=True)
    with open(config.ALERTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_alerts, f, indent=2, ensure_ascii=False, default=str)

    summary_path = os.path.join(config.ALERTS_DIR, "alerts_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        if all_alerts:
            for a in all_alerts:
                f.write(f"[{a['severity'].upper()}] {a['message']}\n")
        else:
            f.write("No alerts triggered.\n")

    log.ok(f"{len(all_alerts)} alerts -> {config.ALERTS_PATH}")
    return all_alerts
