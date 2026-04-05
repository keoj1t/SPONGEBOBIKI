import os

import pandas as pd
import numpy as np

from core import config
from core import log


def run_timeseries(df):
    log.section("TIME-SERIES ANALYSIS")

    dated = df[df["parsed_date"].notna()].copy()
    if dated.empty:
        log.warn("No dated rows for time-series")
        return

    os.makedirs(config.REPORTS_DIR, exist_ok=True)

    dated["week"] = dated["parsed_date"].dt.to_period("W").apply(lambda p: p.start_time)

    weekly_mentions = dated.groupby("week").agg(
        mentions=("week", "count"),
        total_engagement=("engagement", "sum"),
        avg_engagement=("engagement", "mean"),
    ).reset_index()
    weekly_mentions["week"] = weekly_mentions["week"].astype(str)

    if len(weekly_mentions) >= 3:
        x = np.arange(len(weekly_mentions))
        m_coef = np.polyfit(x, weekly_mentions["mentions"].values, 1)
        weekly_mentions["mentions_trend"] = np.polyval(m_coef, x)
        e_coef = np.polyfit(x, weekly_mentions["total_engagement"].values, 1)
        weekly_mentions["engagement_trend"] = np.polyval(e_coef, x)
    else:
        weekly_mentions["mentions_trend"] = weekly_mentions["mentions"]
        weekly_mentions["engagement_trend"] = weekly_mentions["total_engagement"]

    weekly_mentions.to_csv(
        os.path.join(config.REPORTS_DIR, "weekly_timeseries.csv"),
        index=False, encoding="utf-8-sig",
    )

    weekly_platform = dated.groupby(["week", "platform"]).size().reset_index(name="mentions")
    weekly_platform["week"] = weekly_platform["week"].astype(str)
    weekly_platform.to_csv(
        os.path.join(config.REPORTS_DIR, "weekly_by_platform.csv"),
        index=False, encoding="utf-8-sig",
    )

    log.ok(f"Time-series done — {len(weekly_mentions)} weeks")
