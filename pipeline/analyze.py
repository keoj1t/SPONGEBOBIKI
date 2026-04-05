import os
import re
import warnings
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from core import config
from core import log


def _save_csv(df, name):
    path = os.path.join(config.REPORTS_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _save_chart(name):
    path = os.path.join(config.CHARTS_DIR, name)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def _tokenize(text):
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
    return [w for w in words if w not in config.STOPWORDS]


def load_dataset():
    df = pd.read_csv(config.MERGED_DATASET)
    for col in ["likes", "comments", "views", "engagement"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df["parsed_date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df["date_only"] = df["parsed_date"].dt.date.astype("string")
    if "text_length" not in df.columns:
        df["text_length"] = df["text"].apply(len)
    return df


def dataset_summary(df):
    rows = [
        {"metric": "total_rows", "value": len(df)},
        {"metric": "rows_with_date", "value": int(df["parsed_date"].notna().sum())},
        {"metric": "rows_with_url", "value": int(df["url"].fillna("").str.strip().ne("").sum())},
    ]
    out = pd.DataFrame(rows)
    _save_csv(out, "dataset_summary.csv")
    return out


def platform_summary(df):
    g = df.groupby("platform").agg(
        rows=("platform", "count"),
        avg_engagement=("engagement", "mean"),
        median_engagement=("engagement", "median"),
        total_engagement=("engagement", "sum"),
        avg_likes=("likes", "mean"),
        avg_comments=("comments", "mean"),
        avg_views=("views", "mean"),
        avg_text_length=("text_length", "mean"),
    ).reset_index().sort_values("avg_engagement", ascending=False)
    _save_csv(g, "platform_summary.csv")

    plt.figure(figsize=(9, 5))
    plt.bar(g["platform"], g["avg_engagement"])
    plt.title("Avg Engagement by Platform")
    plt.xlabel("Platform")
    plt.ylabel("Avg Engagement")
    plt.xticks(rotation=45)
    _save_chart("avg_engagement_by_platform.png")

    plt.figure(figsize=(9, 5))
    plt.bar(g["platform"], g["rows"])
    plt.title("Posts by Platform")
    plt.xlabel("Platform")
    plt.ylabel("Rows")
    plt.xticks(rotation=45)
    _save_chart("rows_by_platform.png")

    return g


def content_type_summary(df):
    g = df.groupby("content_type").agg(
        rows=("content_type", "count"),
        avg_engagement=("engagement", "mean"),
        median_engagement=("engagement", "median"),
        total_engagement=("engagement", "sum"),
    ).reset_index().sort_values("avg_engagement", ascending=False)
    _save_csv(g, "content_type_summary.csv")

    plt.figure(figsize=(9, 5))
    plt.bar(g["content_type"], g["avg_engagement"])
    plt.title("Avg Engagement by Content Type")
    plt.xlabel("Content Type")
    plt.ylabel("Avg Engagement")
    plt.xticks(rotation=45)
    _save_chart("avg_engagement_by_content_type.png")
    return g


def top_posts(df):
    top = df.sort_values("engagement", ascending=False).head(config.TOP_N_POSTS).copy()
    cols = ["platform", "content_type", "engagement", "likes", "comments", "views", "date", "url", "text"]
    _save_csv(top[cols], "top_posts_by_engagement.csv")

    chart = top.head(10).copy()
    chart["label"] = chart.apply(lambda x: f"{x['platform']} | {str(x['text'])[:40]}...", axis=1)
    plt.figure(figsize=(11, 6))
    plt.barh(chart["label"][::-1], chart["engagement"][::-1])
    plt.title("Top 10 Posts by Engagement")
    plt.xlabel("Engagement")
    _save_chart("top_10_posts.png")
    return top


def keyword_analysis(df):
    text_s = df["text"].fillna("").astype(str)
    rows = []
    for kw in config.KEYWORDS:
        mask = text_s.str.contains(rf"\b{re.escape(kw)}\b", case=False, na=False)
        sub = df[mask]
        rows.append({
            "keyword": kw,
            "rows": len(sub),
            "avg_engagement": sub["engagement"].mean() if len(sub) else 0,
            "median_engagement": sub["engagement"].median() if len(sub) else 0,
            "total_engagement": sub["engagement"].sum() if len(sub) else 0,
        })
    out = pd.DataFrame(rows).sort_values(["rows", "avg_engagement"], ascending=False)
    _save_csv(out, "keyword_analysis.csv")

    chart = out.head(15)
    plt.figure(figsize=(10, 5))
    plt.bar(chart["keyword"], chart["rows"])
    plt.title("Top Keywords by Frequency")
    plt.xlabel("Keyword")
    plt.ylabel("Rows")
    plt.xticks(rotation=45)
    _save_chart("keyword_frequency.png")
    return out


def word_frequency(df):
    tokens = []
    for t in df["text"].fillna(""):
        tokens.extend(_tokenize(t))
    counter = Counter(tokens)
    top = counter.most_common(config.TOP_N_WORDS)
    out = pd.DataFrame(top, columns=["word", "count"])
    _save_csv(out, "top_words.csv")

    chart = out.head(20)
    plt.figure(figsize=(11, 5))
    plt.bar(chart["word"], chart["count"])
    plt.title("Top Words")
    plt.xlabel("Word")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    _save_chart("top_words.png")
    return out


def daily_activity(df):
    dated = df[df["parsed_date"].notna()].copy()
    if dated.empty:
        return pd.DataFrame()
    g = dated.groupby("date_only").agg(
        rows=("date_only", "count"),
        total_engagement=("engagement", "sum"),
        avg_engagement=("engagement", "mean"),
    ).reset_index()
    _save_csv(g, "daily_activity.csv")

    plt.figure(figsize=(11, 5))
    plt.plot(g["date_only"], g["rows"], marker=".", markersize=3)
    plt.title("Posts per Day")
    plt.xlabel("Date")
    plt.ylabel("Posts")
    plt.xticks(rotation=45)
    _save_chart("posts_per_day.png")
    return g


def narrative_buckets(df):
    text_s = df["text"].fillna("").astype(str)
    rows = []
    for bucket, pattern in config.NARRATIVE_BUCKETS.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            mask = text_s.str.contains(pattern, case=False, na=False, regex=True)
        sub = df[mask]
        rows.append({
            "bucket": bucket,
            "rows": len(sub),
            "avg_engagement": sub["engagement"].mean() if len(sub) else 0,
            "median_engagement": sub["engagement"].median() if len(sub) else 0,
            "total_engagement": sub["engagement"].sum() if len(sub) else 0,
        })
    out = pd.DataFrame(rows).sort_values("avg_engagement", ascending=False)
    _save_csv(out, "narrative_buckets.csv")

    plt.figure(figsize=(10, 5))
    plt.bar(out["bucket"], out["avg_engagement"])
    plt.title("Avg Engagement by Narrative Bucket")
    plt.xlabel("Bucket")
    plt.ylabel("Avg Engagement")
    plt.xticks(rotation=45)
    _save_chart("narrative_buckets.png")
    return out


def engagement_normalization(df):
    plat_stats = df.groupby("platform")["engagement"].agg(["mean", "std"]).reset_index()
    plat_stats.columns = ["platform", "plat_mean", "plat_std"]
    plat_stats["plat_std"] = plat_stats["plat_std"].replace(0, 1)

    merged = df.merge(plat_stats, on="platform", how="left")
    df["engagement_zscore"] = ((merged["engagement"] - merged["plat_mean"]) / merged["plat_std"]).round(3)

    top_norm = df.nlargest(20, "engagement_zscore")[
        ["platform", "content_type", "engagement", "engagement_zscore", "text"]
    ].copy()
    top_norm["text"] = top_norm["text"].str[:80]
    _save_csv(top_norm, "top_posts_normalized.csv")

    plat_norm = df.groupby("platform").agg(
        avg_zscore=("engagement_zscore", "mean"),
        median_zscore=("engagement_zscore", "median"),
        rows=("platform", "count"),
    ).reset_index().sort_values("avg_zscore", ascending=False)
    _save_csv(plat_norm, "platform_normalized.csv")

    plt.figure(figsize=(9, 5))
    plt.bar(plat_norm["platform"], plat_norm["avg_zscore"])
    plt.title("Normalized Engagement by Platform (Z-Score)")
    plt.xlabel("Platform")
    plt.ylabel("Avg Z-Score")
    plt.axhline(y=0, color="#888", linestyle="--", linewidth=0.8)
    plt.xticks(rotation=45)
    _save_chart("normalized_engagement.png")

    log.ok(f"Engagement normalization done — z-scores computed per platform")
    return plat_norm


def narrative_cross_tab(df):
    text_s = df["text"].fillna("").astype(str)
    rows = []

    for bucket, pattern in config.NARRATIVE_BUCKETS.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            mask = text_s.str.contains(pattern, case=False, na=False, regex=True)
        sub = df[mask]
        if sub.empty:
            continue
        for plat, grp in sub.groupby("platform"):
            rows.append({
                "narrative": bucket,
                "platform": plat,
                "posts": len(grp),
                "avg_engagement": round(grp["engagement"].mean(), 1),
                "median_engagement": round(grp["engagement"].median(), 1),
                "total_engagement": int(grp["engagement"].sum()),
            })

    out = pd.DataFrame(rows).sort_values(["narrative", "avg_engagement"], ascending=[True, False])
    _save_csv(out, "narrative_platform_crosstab.csv")

    # Heatmap data
    if not out.empty:
        pivot = out.pivot_table(
            index="narrative", columns="platform",
            values="avg_engagement", fill_value=0,
        )
        plt.figure(figsize=(10, 6))
        plt.imshow(pivot.values, cmap="YlGn", aspect="auto")
        plt.colorbar(label="Avg Engagement")
        plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45)
        plt.yticks(range(len(pivot.index)), pivot.index)
        plt.title("Narrative × Platform: Avg Engagement")
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if val > 0:
                    plt.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7)
        _save_chart("narrative_platform_heatmap.png")

    log.ok(f"Cross-tabulation done — {len(out)} narrative×platform combinations")
    return out


def statistical_tests(df):
    results = []

    # Kruskal-Wallis: engagement differs across platforms?
    platform_groups = [grp["engagement"].values for _, grp in df.groupby("platform") if len(grp) >= 5]
    if len(platform_groups) >= 2:
        stat, p_value = stats.kruskal(*platform_groups)
        results.append({
            "test": "Kruskal-Wallis H-test",
            "comparison": "Engagement across platforms",
            "statistic": round(stat, 2),
            "p_value": round(p_value, 6),
            "significant": "Yes" if p_value < 0.05 else "No",
            "interpretation": "Platform engagement differences are statistically significant"
                              if p_value < 0.05 else "No significant difference across platforms",
        })

    # Chi-squared: sentiment distribution across platforms?
    if "sentiment_label" in df.columns:
        contingency = pd.crosstab(df["platform"], df["sentiment_label"])
        if contingency.shape[0] >= 2 and contingency.shape[1] >= 2:
            chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
            results.append({
                "test": "Chi-squared test",
                "comparison": "Sentiment distribution across platforms",
                "statistic": round(chi2, 2),
                "p_value": round(p_val, 6),
                "significant": "Yes" if p_val < 0.05 else "No",
                "interpretation": "Sentiment differs significantly across platforms"
                                  if p_val < 0.05 else "No significant sentiment difference",
            })

    # Mann-Whitney U: visual content vs text content
    visual_types = {"video", "reel", "carousel_album"}
    visual = df[df["content_type"].isin(visual_types)]["engagement"]
    text = df[~df["content_type"].isin(visual_types)]["engagement"]
    if len(visual) >= 5 and len(text) >= 5:
        u_stat, p_val = stats.mannwhitneyu(visual, text, alternative="two-sided")
        results.append({
            "test": "Mann-Whitney U test",
            "comparison": "Visual vs text content engagement",
            "statistic": round(u_stat, 2),
            "p_value": round(p_val, 6),
            "significant": "Yes" if p_val < 0.05 else "No",
            "interpretation": "Visual content significantly outperforms text"
                              if p_val < 0.05 else "No significant difference",
        })

    # Correlation: text length vs engagement
    if "text_length" in df.columns and len(df) >= 20:
        corr, p_val = stats.spearmanr(df["text_length"], df["engagement"])
        results.append({
            "test": "Spearman correlation",
            "comparison": "Text length vs engagement",
            "statistic": round(corr, 4),
            "p_value": round(p_val, 6),
            "significant": "Yes" if p_val < 0.05 else "No",
            "interpretation": f"{'Positive' if corr > 0 else 'Negative'} correlation (r={corr:.3f})"
                              if p_val < 0.05 else "No significant correlation",
        })

    out = pd.DataFrame(results)
    _save_csv(out, "statistical_tests.csv")
    log.ok(f"Statistical tests done — {len(results)} tests, {sum(1 for r in results if r['significant'] == 'Yes')} significant")
    return out


def run_analysis():
    log.section("ANALYSIS")
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    os.makedirs(config.CHARTS_DIR, exist_ok=True)

    df = load_dataset()
    log.info(f"Loaded {len(df)} rows")

    results = {}
    results["summary"] = dataset_summary(df)
    results["platforms"] = platform_summary(df)
    results["content_types"] = content_type_summary(df)
    results["top_posts"] = top_posts(df)
    results["keywords"] = keyword_analysis(df)
    results["words"] = word_frequency(df)
    results["daily"] = daily_activity(df)
    results["narratives"] = narrative_buckets(df)
    results["normalized"] = engagement_normalization(df)
    results["crosstab"] = narrative_cross_tab(df)
    results["stats"] = statistical_tests(df)

    log.ok(f"Analysis done — {len(os.listdir(config.CHARTS_DIR))} charts, CSVs in reports/")
    return df, results
