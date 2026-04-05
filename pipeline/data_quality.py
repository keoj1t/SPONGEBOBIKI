import json
import os
from datetime import datetime, date

import pandas as pd

from core import config
from core import log

TODAY = date.today()


def run_data_quality(df):
    log.section("DATA QUALITY CHECK")
    issues = []
    fixes = {"rows_before": len(df)}

    neg_mask = df["engagement"] < 0
    neg_count = neg_mask.sum()
    if neg_count:
        df.loc[neg_mask, "engagement"] = 0
        df.loc[neg_mask, "likes"] = df.loc[neg_mask, "likes"].clip(lower=0)
        issues.append(f"Fixed {neg_count} rows with negative engagement (set to 0)")
    fixes["negative_engagement_fixed"] = int(neg_count)

    future_mask = pd.Series(False, index=df.index)
    if "parsed_date" not in df.columns:
        df["parsed_date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    valid_dates = df["parsed_date"].notna()
    future_mask = valid_dates & (df["parsed_date"].dt.date > TODAY)
    future_count = future_mask.sum()
    if future_count:
        df.loc[future_mask, "date"] = ""
        df.loc[future_mask, "parsed_date"] = pd.NaT
        issues.append(f"Cleared {future_count} future timestamps")
    fixes["future_dates_cleared"] = int(future_count)

    url_missing = df["url"].fillna("").str.strip().eq("").sum()
    url_present = len(df) - url_missing
    fixes["urls_present"] = int(url_present)
    fixes["urls_missing"] = int(url_missing)
    fixes["url_coverage_pct"] = round(url_present / max(len(df), 1) * 100, 1)
    if url_missing > len(df) * 0.5:
        issues.append(f"Low URL coverage: {fixes['url_coverage_pct']}% ({url_present}/{len(df)})")

    plat_counts = df["platform"].value_counts()
    total = len(df)
    imbalance = []
    for plat, cnt in plat_counts.items():
        pct = cnt / total * 100
        imbalance.append({"platform": plat, "count": int(cnt), "pct": round(pct, 1)})
        if pct > 70:
            issues.append(f"Platform imbalance: {plat} = {pct:.1f}% of dataset")
        elif cnt < 10:
            issues.append(f"Low sample: {plat} has only {cnt} rows")
    fixes["platform_distribution"] = imbalance

    date_coverage = int(df["parsed_date"].notna().sum())
    fixes["rows_with_date"] = date_coverage
    fixes["date_coverage_pct"] = round(date_coverage / max(len(df), 1) * 100, 1)

    fixes["rows_after"] = len(df)
    fixes["issues"] = issues
    fixes["timestamp"] = datetime.now().isoformat()

    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(config.REPORTS_DIR, "data_quality.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(fixes, f, indent=2, ensure_ascii=False)

    for issue in issues:
        log.warn(issue)
    log.ok(f"Data quality check done — {len(issues)} issues found")

    return df, fixes
