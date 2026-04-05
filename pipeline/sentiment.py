import os

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from core import config
from core import log

_analyzer = SentimentIntensityAnalyzer()


def _score(text):
    if not text or not isinstance(text, str) or len(text.strip()) < 5:
        return 0.0
    return _analyzer.polarity_scores(text)["compound"]


def _label(score):
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def run_sentiment(df):
    log.section("SENTIMENT ANALYSIS")

    df["sentiment_score"] = df["text"].fillna("").apply(_score)
    df["sentiment_label"] = df["sentiment_score"].apply(_label)

    by_platform = df.groupby("platform").agg(
        avg_sentiment=("sentiment_score", "mean"),
        positive_pct=("sentiment_label", lambda x: round((x == "positive").mean() * 100, 1)),
        negative_pct=("sentiment_label", lambda x: round((x == "negative").mean() * 100, 1)),
        neutral_pct=("sentiment_label", lambda x: round((x == "neutral").mean() * 100, 1)),
        count=("sentiment_score", "count"),
    ).reset_index().sort_values("avg_sentiment", ascending=False)

    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    by_platform.to_csv(
        os.path.join(config.REPORTS_DIR, "sentiment_by_platform.csv"),
        index=False, encoding="utf-8-sig",
    )

    dated = df[df["parsed_date"].notna()].copy()
    if not dated.empty:
        dated["week"] = dated["parsed_date"].dt.to_period("W").apply(lambda p: p.start_time)
        weekly = dated.groupby("week").agg(
            avg_sentiment=("sentiment_score", "mean"),
            positive_count=("sentiment_label", lambda x: (x == "positive").sum()),
            negative_count=("sentiment_label", lambda x: (x == "negative").sum()),
            neutral_count=("sentiment_label", lambda x: (x == "neutral").sum()),
            total=("sentiment_score", "count"),
        ).reset_index()
        weekly["week"] = weekly["week"].astype(str)
        weekly.to_csv(
            os.path.join(config.REPORTS_DIR, "sentiment_over_time.csv"),
            index=False, encoding="utf-8-sig",
        )

    overall = df["sentiment_label"].value_counts()
    log.ok(
        f"Sentiment done — positive: {overall.get('positive', 0)}, "
        f"negative: {overall.get('negative', 0)}, "
        f"neutral: {overall.get('neutral', 0)}"
    )
    return df
