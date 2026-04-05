import json
import os
from datetime import datetime

import pandas as pd

from core import config
from core import log


def _read_csv(name):
    path = os.path.join(config.REPORTS_DIR, name)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def _fmt(n):
    if isinstance(n, float):
        if n > 1000:
            return f"{n:,.0f}"
        return f"{n:.1f}"
    return f"{n:,}"


def generate_report():
    log.section("REPORT GENERATION")

    summary = _read_csv("dataset_summary.csv")
    platforms = _read_csv("platform_summary.csv")
    content = _read_csv("content_type_summary.csv")
    top = _read_csv("top_posts_by_engagement.csv")
    keywords = _read_csv("keyword_analysis.csv")
    words = _read_csv("top_words.csv")
    narratives = _read_csv("narrative_buckets.csv")
    crosstab = _read_csv("narrative_platform_crosstab.csv")
    stat_tests = _read_csv("statistical_tests.csv")
    quality_path = os.path.join(config.REPORTS_DIR, "data_quality.json")
    quality = {}
    if os.path.exists(quality_path):
        with open(quality_path, "r", encoding="utf-8") as f:
            quality = json.load(f)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    w = lines.append

    w(f"# Growth Intelligence Report")
    w(f"")
    w(f"*Generated: {ts}*")
    w("")

    w("## 1. Dataset Overview")
    w("")
    if not summary.empty:
        for _, r in summary.iterrows():
            w(f"- **{r['metric']}**: {_fmt(r['value'])}")
    w("")

    if not platforms.empty:
        w("### Platform breakdown")
        w("")
        w("| Platform | Posts | Avg Engagement | Median Eng | Total Eng |")
        w("|----------|------:|---------------:|-----------:|----------:|")
        for _, r in platforms.iterrows():
            w(f"| {r['platform']} | {_fmt(r['rows'])} | {_fmt(r['avg_engagement'])} | {_fmt(r['median_engagement'])} | {_fmt(r['total_engagement'])} |")
        w("")

    w("## 2. Content Type Performance")
    w("")
    if not content.empty:
        w("| Type | Count | Avg Engagement | Median |")
        w("|------|------:|---------------:|-------:|")
        for _, r in content.iterrows():
            w(f"| {r['content_type']} | {_fmt(r['rows'])} | {_fmt(r['avg_engagement'])} | {_fmt(r['median_engagement'])} |")
        w("")

    w("## 3. Top Posts by Engagement")
    w("")
    if not top.empty:
        for i, (_, r) in enumerate(top.head(10).iterrows(), 1):
            text_preview = str(r.get("text", ""))[:80].replace("\n", " ")
            w(f"{i}. **{r['platform']}** ({_fmt(r['engagement'])} eng) — {text_preview}...")
        w("")

    w("## 4. Keyword Analysis")
    w("")
    if not keywords.empty:
        w("| Keyword | Mentions | Avg Engagement | Total Eng |")
        w("|---------|:--------:|---------------:|----------:|")
        for _, r in keywords.head(15).iterrows():
            w(f"| {r['keyword']} | {_fmt(r['rows'])} | {_fmt(r['avg_engagement'])} | {_fmt(r['total_engagement'])} |")
        w("")

    w("## 5. Most Common Words")
    w("")
    if not words.empty:
        top_words = ", ".join(f"**{r['word']}** ({r['count']})" for _, r in words.head(15).iterrows())
        w(top_words)
        w("")

    w("## 6. Narrative Buckets")
    w("")
    if not narratives.empty:
        w("| Narrative | Posts | Avg Engagement | Median |")
        w("|-----------|------:|---------------:|-------:|")
        for _, r in narratives.iterrows():
            w(f"| {r['bucket']} | {_fmt(r['rows'])} | {_fmt(r['avg_engagement'])} | {_fmt(r['median_engagement'])} |")
        w("")

    w("## 7. Key Insights")
    w("")

    if not platforms.empty:
        best = platforms.iloc[0]
        w(f"- **{best['platform']}** leads in avg engagement ({_fmt(best['avg_engagement'])}).")
        worst = platforms.iloc[-1]
        w(f"- **{worst['platform']}** has the lowest engagement ({_fmt(worst['avg_engagement'])}).")

    if not content.empty:
        top_type = content.iloc[0]
        w(f"- **{top_type['content_type']}** is the highest-performing content format with avg engagement of {_fmt(top_type['avg_engagement'])}.")

    if not keywords.empty:
        top_kw = keywords.iloc[0]
        w(f"- Most mentioned keyword: **{top_kw['keyword']}** ({_fmt(top_kw['rows'])} posts, {_fmt(top_kw['avg_engagement'])} avg eng).")

    if not narratives.empty:
        top_nar = narratives.iloc[0]
        w(f"- Strongest narrative bucket: **{top_nar['bucket']}** (avg engagement {_fmt(top_nar['avg_engagement'])}).")

    # Dynamic insights from cross-tab
    if not crosstab.empty:
        best_combo = crosstab.loc[crosstab["avg_engagement"].idxmax()]
        w(f"- Best narrative×platform combo: **{best_combo['narrative']}** on **{best_combo['platform']}** "
          f"(avg {_fmt(best_combo['avg_engagement'])} engagement).")

    # Insight from statistical tests
    if not stat_tests.empty:
        sig_tests = stat_tests[stat_tests["significant"] == "Yes"]
        for _, t in sig_tests.iterrows():
            w(f"- {t['interpretation']} (p={t['p_value']}).")

    w("")

    w("## 8. Narrative × Platform Cross-Tabulation")
    w("")
    if not crosstab.empty:
        w("| Narrative | Platform | Posts | Avg Engagement | Total Engagement |")
        w("|-----------|----------|------:|---------------:|-----------------:|")
        for _, r in crosstab.head(20).iterrows():
            w(f"| {r['narrative']} | {r['platform']} | {_fmt(r['posts'])} | {_fmt(r['avg_engagement'])} | {_fmt(r['total_engagement'])} |")
    else:
        w("Cross-tabulation not generated yet.")
    w("")

    w("## 9. Statistical Tests")
    w("")
    if not stat_tests.empty:
        w("| Test | Comparison | Statistic | p-value | Significant | Interpretation |")
        w("|------|-----------|----------:|--------:|:-----------:|----------------|")
        for _, r in stat_tests.iterrows():
            w(f"| {r['test']} | {r['comparison']} | {r['statistic']} | {r['p_value']} | {r['significant']} | {r['interpretation']} |")
    else:
        w("Statistical tests not run yet.")
    w("")

    w("## 10. Data Quality")
    w("")
    if quality:
        w(f"- **Total rows**: {quality.get('rows_after', 'N/A')}")
        w(f"- **Date coverage**: {quality.get('date_coverage_pct', 'N/A')}%")
        w(f"- **URL coverage**: {quality.get('url_coverage_pct', 'N/A')}%")
        w(f"- **Negative engagement fixed**: {quality.get('negative_engagement_fixed', 0)}")
        w(f"- **Future dates cleared**: {quality.get('future_dates_cleared', 0)}")
        issues = quality.get("issues", [])
        if issues:
            w("")
            w("**Issues detected:**")
            for issue in issues:
                w(f"- ⚠ {issue}")
    else:
        w("Data quality report not generated yet.")
    w("")

    w("## 11. Alerts")
    w("")
    if os.path.exists(config.ALERTS_PATH):
        with open(config.ALERTS_PATH, "r", encoding="utf-8") as f:
            alerts = json.load(f)
        if alerts:
            for a in alerts:
                severity = a.get("severity", "info").upper()
                w(f"- **[{severity}]** {a.get('message', '')}")
        else:
            w("No alerts triggered.")
    else:
        w("Alert system has not run yet.")
    w("")

    w("## 12. Methodology")
    w("")
    w("**Data Collection:** 7 platforms scraped — Reddit (public JSON API), YouTube (native search + page scraping), "
      "TikTok/Twitter/Instagram/LinkedIn/Threads (Apify cloud actors, API tokens required).")
    w("")
    w("**Text Processing:** English-only filtering via langdetect (min 20 chars). "
      "Deduplication by first 200 characters of normalized text. Date standardization to YYYY-MM-DD.")
    w("")
    w("**Sentiment:** VADER lexicon-based analysis. Thresholds: positive ≥ 0.05, negative ≤ -0.05, neutral in between.")
    w("")
    w("**Engagement Normalization:** Z-score per platform (engagement - platform_mean) / platform_std. "
      "Enables fair cross-platform comparison independent of audience size.")
    w("")
    w("**Anomaly Detection Thresholds:**")
    w("- Engagement spikes: > rolling 7-day mean + 3σ AND ≥ 3x day-over-day increase")
    w("- Mention spikes: > rolling 7-day mean + 2.5σ")
    w("- Viral posts: > 50× platform median engagement")
    w("- Keyword trends: ≥ 2× frequency increase (older vs newer data half)")
    w("")
    w("**Statistical Tests:** Kruskal-Wallis H-test for multi-group comparison, "
      "Mann-Whitney U for two-group comparison, Chi-squared for categorical distributions, "
      "Spearman correlation for continuous relationships. Significance level: α = 0.05.")
    w("")
    w("**Topic Discovery:** TF-IDF vectorization (max 200 features, min_df=3, max_df=0.8). "
      "Emerging terms detected by comparing word frequencies in chronologically split halves (≥ 1.5× growth).")
    w("")

    report_text = "\n".join(lines)
    os.makedirs(os.path.dirname(config.REPORT_PATH), exist_ok=True)
    with open(config.REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    log.ok(f"Report saved -> {config.REPORT_PATH}")
    return report_text
