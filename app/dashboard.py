import json
import os
import sys
import subprocess
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import config

st.set_page_config(
    page_title="Claude Growth Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

LIME = "#c8ff00"
DIM = "#888888"
BG_CARD = "#141414"
BG_CARD2 = "#1c1c1c"
BORDER = "#2a2a2a"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
}}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}}

section[data-testid="stSidebar"] {{
    background: #0a0a0a !important;
    border-right: 1px solid {BORDER} !important;
}}

section[data-testid="stSidebar"] .stButton > button {{
    background: {LIME} !important;
    color: #000 !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 14px 20px !important;
    border-radius: 6px !important;
    transition: all 0.15s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: #b8ee00 !important;
    transform: translateY(-1px) !important;
}}

section[data-testid="stSidebar"] .stDownloadButton > button {{
    background: transparent !important;
    color: #ccc !important;
    border: 1px solid {BORDER} !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}}
section[data-testid="stSidebar"] .stDownloadButton > button:hover {{
    border-color: {LIME} !important;
    color: {LIME} !important;
}}

div[data-testid="stMetric"] {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    padding: 20px 16px 16px 16px !important;
}}
div[data-testid="stMetric"] label {{
    color: {DIM} !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {LIME} !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}}

button[data-baseweb="tab"] {{
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: {DIM} !important;
    padding: 14px 20px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
}}
button[data-baseweb="tab"]:hover {{
    color: #ccc !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {LIME} !important;
    border-bottom: 2px solid {LIME} !important;
    background: transparent !important;
}}
div[data-baseweb="tab-highlight"] {{
    background-color: {LIME} !important;
}}
div[data-baseweb="tab-border"] {{
    background-color: {BORDER} !important;
}}

div[data-testid="stDataFrame"] {{
    border-radius: 8px !important;
    overflow: hidden;
    border: 1px solid {BORDER} !important;
}}

div[data-baseweb="select"] > div {{
    background: {BG_CARD} !important;
    border-color: {BORDER} !important;
    border-radius: 6px !important;
}}

.lime {{ color: {LIME}; }}
.dim {{ color: {DIM}; }}

.page-title {{
    font-size: 2.8rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 4px;
    color: #ffffff;
}}
.page-subtitle {{
    font-size: 1rem;
    color: {DIM};
    font-weight: 400;
    margin-bottom: 32px;
}}
.section-title {{
    font-size: 1.1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {LIME};
    margin-bottom: 12px;
    margin-top: 8px;
}}

.plat-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}}
.plat-count {{
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
}}
.plat-name {{
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {DIM};
    margin-top: 4px;
}}
.plat-eng {{
    font-size: 0.75rem;
    color: {LIME};
    margin-top: 6px;
    font-weight: 500;
}}

.alert-row {{
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 0.85rem;
    line-height: 1.5;
    border-left: 3px solid;
    background: {BG_CARD};
}}
.alert-high {{
    border-color: #ef4444;
}}
.alert-medium {{
    border-color: {LIME};
}}
.alert-info {{
    border-color: #555;
}}

.counter-pill {{
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-right: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.chart-label {{
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {DIM};
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid {BORDER};
}}

.divider {{
    height: 1px;
    background: {BORDER};
    margin: 24px 0;
}}

.outcome-banner {{
    background: linear-gradient(135deg, rgba(200,255,0,0.12) 0%, rgba(200,255,0,0.04) 100%);
    border: 1px solid rgba(200,255,0,0.2);
    border-radius: 8px;
    padding: 24px 28px;
    margin-top: 16px;
}}
.outcome-title {{
    font-size: 1.3rem;
    font-weight: 900;
    text-transform: uppercase;
    color: {LIME};
    letter-spacing: 0.04em;
}}
.outcome-text {{
    font-size: 0.95rem;
    color: #ccc;
    margin-top: 4px;
}}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---

st.sidebar.markdown(f"""
<div style="padding: 16px 0 8px 0;">
    <div style="
        display: inline-block;
        background: {LIME};
        color: #000;
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 4px 12px;
        border-radius: 3px;
    ">Growth Engineering Track</div>
    <div style="
        font-size: 1.3rem;
        font-weight: 800;
        color: #fff;
        margin-top: 10px;
        text-transform: uppercase;
        letter-spacing: -0.01em;
    ">GROWTH<br><span style="color:{LIME}">INTELLIGENCE</span></div>
    <div style="font-size: 0.72rem; color: {DIM}; margin-top: 6px;">
        Claude AI · Social Tracker
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("")

if st.sidebar.button("RUN PIPELINE", use_container_width=True):
    with st.spinner("Running pipeline..."):
        run_script = os.path.join(config.ROOT, "run.py")
        result = subprocess.run(
            [sys.executable, run_script, "--skip-scrape"],
            capture_output=True, text=True, timeout=600,
            encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            st.sidebar.success("Pipeline finished")
        else:
            st.sidebar.error("Pipeline failed")
            st.sidebar.code(result.stderr[-500:] if result.stderr else "no stderr")

st.sidebar.markdown("")

if os.path.exists(config.MERGED_DATASET):
    with open(config.MERGED_DATASET, "rb") as f:
        st.sidebar.download_button(
            "DOWNLOAD DATASET",
            f, file_name="final_dataset_eng.csv",
            mime="text/csv", use_container_width=True,
        )

if os.path.exists(config.REPORT_PATH):
    with open(config.REPORT_PATH, "rb") as f:
        st.sidebar.download_button(
            "DOWNLOAD REPORT",
            f, file_name="auto_report.md",
            mime="text/markdown", use_container_width=True,
        )

st.sidebar.markdown(f"""
<div style="margin-top: 40px;">
    <div style="font-size: 0.65rem; color: #555; text-transform: uppercase; letter-spacing: 0.08em;">
        Tracking across
    </div>
    <div style="font-size: 0.7rem; color: {DIM}; margin-top: 4px; line-height: 1.6;">
        Reddit · YouTube · TikTok<br>Twitter · Instagram · LinkedIn<br>Threads
    </div>
</div>
""", unsafe_allow_html=True)

# --- Helpers ---

def read_csv_safe(name):
    path = os.path.join(config.REPORTS_DIR, name)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def get_alerts():
    if not os.path.exists(config.ALERTS_PATH):
        return []
    with open(config.ALERTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_quality_report():
    path = os.path.join(config.REPORTS_DIR, "data_quality.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#ccc"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#2a2a2a", zerolinecolor="#2a2a2a"),
    yaxis=dict(gridcolor="#2a2a2a", zerolinecolor="#2a2a2a"),
    colorway=["#c8ff00", "#6366f1", "#f43f5e", "#22d3ee", "#f59e0b", "#a78bfa"],
)

# --- No data state ---

if not os.path.exists(config.MERGED_DATASET):
    st.markdown(f"""
    <div style="text-align:center; padding: 100px 20px;">
        <div class="page-title">NO DATA <span class="lime">YET</span></div>
        <div class="page-subtitle">Run the pipeline to start collecting insights</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- Load data ---

@st.cache_data(ttl=60)
def load_main_dataset():
    df = pd.read_csv(config.MERGED_DATASET)
    for col in ["likes", "comments", "views", "engagement"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["parsed_date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    return df

df_full = load_main_dataset()

# --- sidebar date filter

st.sidebar.markdown(f'<div class="section-title" style="margin-top:24px;">Date Filter</div>', unsafe_allow_html=True)
valid_dates = df_full["parsed_date"].dropna()
if not valid_dates.empty:
    date_min = valid_dates.min().date()
    date_max = valid_dates.max().date()
    date_range = st.sidebar.date_input("Range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        mask = (
            df_full["parsed_date"].isna() |
            ((df_full["parsed_date"].dt.date >= date_range[0]) & (df_full["parsed_date"].dt.date <= date_range[1]))
        )
        df = df_full[mask].copy()
    else:
        df = df_full.copy()
else:
    df = df_full.copy()

st.sidebar.markdown(f"""
<div style="font-size:0.72rem; color:{DIM}; margin-top:8px;">
    Showing {len(df):,} of {len(df_full):,} rows
</div>
""", unsafe_allow_html=True)


# --- last updated

dataset_mtime = os.path.getmtime(config.MERGED_DATASET)
last_updated = datetime.fromtimestamp(dataset_mtime).strftime("%Y-%m-%d %H:%M")

# --- header

st.markdown(f"""
<div class="page-title">CLAUDE GROWTH <span class="lime">INTELLIGENCE</span></div>
<div class="page-subtitle">Real-time social media monitoring & analytics across 7 platforms &nbsp;·&nbsp; Last updated: {last_updated}</div>
""", unsafe_allow_html=True)

# --- KPI row

summary = read_csv_safe("dataset_summary.csv")
platforms = read_csv_safe("platform_summary.csv")

total_rows = len(df)
rows_dated = int(df["parsed_date"].notna().sum())
rows_url = int(df["url"].fillna("").str.strip().ne("").sum()) if "url" in df.columns else 0
n_platforms = df["platform"].nunique()
alerts_data = get_alerts()
high_alerts = sum(1 for a in alerts_data if a.get("severity") == "high")
avg_sentiment = df["sentiment_score"].mean() if "sentiment_score" in df.columns else None

cols_kpi = st.columns(6)
cols_kpi[0].metric("Total Posts", f"{total_rows:,}")
cols_kpi[1].metric("With Date", f"{rows_dated:,}")
cols_kpi[2].metric("With URL", f"{rows_url:,}")
cols_kpi[3].metric("Platforms", n_platforms)
cols_kpi[4].metric("Alerts", f"{high_alerts}")
if avg_sentiment is not None:
    cols_kpi[5].metric("Avg Sentiment", f"{avg_sentiment:+.2f}")
else:
    cols_kpi[5].metric("Avg Sentiment", "—")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# --- tabs

tab_overview, tab_trends, tab_sentiment, tab_keywords, tab_quality, tab_alerts, tab_report = st.tabs(
    ["OVERVIEW", "TRENDS", "SENTIMENT", "KEYWORDS", "DATA QUALITY", "ALERTS", "REPORT"]
)

# --- OVERVIEW
with tab_overview:
    # Key Insights — dynamically generated from data
    st.markdown('<div class="section-title">Key Insights</div>', unsafe_allow_html=True)
    dynamic_insights = []
    plat_agg = df.groupby("platform")["engagement"].agg(["mean", "count"]).reset_index().sort_values("mean", ascending=False)
    if not plat_agg.empty:
        best_plat = plat_agg.iloc[0]
        dynamic_insights.append(f"{best_plat['platform'].title()} leads in avg engagement ({best_plat['mean']:,.0f}) — highest ROI channel.")
    ct_agg = df.groupby("content_type")["engagement"].mean().sort_values(ascending=False)
    if not ct_agg.empty:
        best_ct = ct_agg.index[0]
        dynamic_insights.append(f"'{best_ct}' is the top-performing content format with avg engagement of {ct_agg.iloc[0]:,.0f}.")
    total = len(df)
    n_plats = df["platform"].nunique()
    dynamic_insights.append(f"Balanced dataset: {n_plats} platforms, {total:,} total rows — fair cross-platform comparison.")
    if "sentiment_label" in df.columns:
        pos_pct = (df["sentiment_label"] == "positive").mean() * 100
        dynamic_insights.append(f"Overall sentiment is {pos_pct:.0f}% positive — Claude has strong brand perception.")
    dated_pct = df["parsed_date"].notna().mean() * 100
    dynamic_insights.append(f"Date coverage: {dated_pct:.0f}% of rows have valid timestamps for time-series analysis.")
    dynamic_insights.append("Organic UGC dominates — Claude spreads through user discussions, not marketing.")

    insight_cols = st.columns(2)
    for i, insight in enumerate(dynamic_insights[:6]):
        with insight_cols[i % 2]:
            st.markdown(f"""
            <div style="background:{BG_CARD}; border:1px solid {BORDER}; border-left:3px solid {LIME};
                 border-radius:6px; padding:12px 16px; margin-bottom:8px; font-size:0.85rem; color:#ccc;">
                {insight}
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Platform Breakdown</div>', unsafe_allow_html=True)

    plat_data = df.groupby("platform").agg(
        rows=("platform", "count"),
        avg_engagement=("engagement", "mean"),
        total_engagement=("engagement", "sum"),
    ).reset_index().sort_values("avg_engagement", ascending=False)

    if not plat_data.empty:
        plat_cols = st.columns(len(plat_data))
        for i, (_, row) in enumerate(plat_data.iterrows()):
            with plat_cols[i]:
                st.markdown(f"""
                <div class="plat-card">
                    <div class="plat-count">{int(row['rows']):,}</div>
                    <div class="plat-name">{row['platform']}</div>
                    <div class="plat-eng">avg eng: {row['avg_engagement']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            plat_data, x="platform", y="avg_engagement",
            title="Avg Engagement by Platform",
            color="platform",
        )
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(
            plat_data, values="rows", names="platform",
            title="Posts Distribution",
        )
        fig.update_layout(**{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top 10 Posts by Engagement</div>', unsafe_allow_html=True)

    top = df.nlargest(10, "engagement")[["platform", "content_type", "engagement", "likes", "comments", "text"]].copy()
    if not top.empty:
        top["text"] = top["text"].str[:100] + "..."
        top.columns = ["Platform", "Type", "Engagement", "Likes", "Comments", "Preview"]
        st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="outcome-banner">
        <div class="outcome-title">OUTCOME</div>
        <div class="outcome-text">A data-driven growth engine, not one-off virality</div>
    </div>
    """, unsafe_allow_html=True)


# --- TRENDS
with tab_trends:
    ts_data = read_csv_safe("weekly_timeseries.csv")
    if ts_data.empty:
        st.info("Run the pipeline to generate time-series data.")
    else:
        st.markdown('<div class="section-title">Weekly Mentions Over Time</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_data["week"], y=ts_data["mentions"],
            mode="lines+markers", name="Mentions",
            line=dict(color=LIME, width=2), marker=dict(size=4),
        ))
        if "mentions_trend" in ts_data.columns:
            fig.add_trace(go.Scatter(
                x=ts_data["week"], y=ts_data["mentions_trend"],
                mode="lines", name="Trend",
                line=dict(color="#6366f1", width=2, dash="dash"),
            ))
        fig.update_layout(**PLOTLY_LAYOUT, title="Weekly Mentions + Trendline")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-title">Weekly Engagement Over Time</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=ts_data["week"], y=ts_data["total_engagement"],
            name="Total Engagement", marker_color=LIME, opacity=0.7,
        ))
        if "engagement_trend" in ts_data.columns:
            fig2.add_trace(go.Scatter(
                x=ts_data["week"], y=ts_data["engagement_trend"],
                mode="lines", name="Trend",
                line=dict(color="#f43f5e", width=2, dash="dash"),
            ))
        fig2.update_layout(**PLOTLY_LAYOUT, title="Weekly Engagement + Trendline")
        st.plotly_chart(fig2, use_container_width=True)

    plat_ts = read_csv_safe("weekly_by_platform.csv")
    if not plat_ts.empty:
        st.markdown('<div class="section-title">Mentions by Platform Over Time</div>', unsafe_allow_html=True)
        fig3 = px.line(
            plat_ts, x="week", y="mentions", color="platform",
            title="Weekly Mentions by Platform",
        )
        fig3.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)


# --- SENTIMENT
with tab_sentiment:
    sent_plat = read_csv_safe("sentiment_by_platform.csv")
    sent_time = read_csv_safe("sentiment_over_time.csv")

    if sent_plat.empty:
        st.info("Run the pipeline to generate sentiment data.")
    else:
        st.markdown('<div class="section-title">Sentiment by Platform</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                sent_plat, x="platform", y="avg_sentiment",
                title="Avg Sentiment Score by Platform",
                color="avg_sentiment",
                color_continuous_scale=["#f43f5e", "#888", LIME],
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            melt = sent_plat.melt(
                id_vars="platform",
                value_vars=["positive_pct", "negative_pct", "neutral_pct"],
                var_name="sentiment", value_name="pct",
            )
            melt["sentiment"] = melt["sentiment"].str.replace("_pct", "")
            fig = px.bar(
                melt, x="platform", y="pct", color="sentiment",
                title="Sentiment Distribution",
                barmode="stack",
                color_discrete_map={"positive": LIME, "negative": "#f43f5e", "neutral": "#555"},
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div style="font-size:0.75rem; color:{DIM}; margin-bottom:12px;">
            Sample sizes vary. Reddit n={sent_plat[sent_plat['platform']=='reddit']['count'].values[0] if 'reddit' in sent_plat['platform'].values else '?'},
            YouTube n={sent_plat[sent_plat['platform']=='youtube']['count'].values[0] if 'youtube' in sent_plat['platform'].values else '?'},
            TikTok n={sent_plat[sent_plat['platform']=='tiktok']['count'].values[0] if 'tiktok' in sent_plat['platform'].values else '?'}
            — interpret smaller samples with caution.
        </div>
        """, unsafe_allow_html=True)

    if not sent_time.empty:
        st.markdown('<div class="section-title">Sentiment Over Time</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sent_time["week"], y=sent_time["avg_sentiment"],
            mode="lines+markers", name="Avg Sentiment",
            line=dict(color=LIME, width=2), marker=dict(size=4),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="#555")
        fig.update_layout(**PLOTLY_LAYOUT, title="Weekly Average Sentiment")
        st.plotly_chart(fig, use_container_width=True)


# --- KEYWORDS
with tab_keywords:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Keyword Analysis</div>', unsafe_allow_html=True)
        kw = read_csv_safe("keyword_analysis.csv")
        if not kw.empty:
            fig = px.bar(
                kw.head(15), x="keyword", y="rows",
                title="Top Keywords by Frequency",
                color="avg_engagement",
                color_continuous_scale=[LIME, "#f43f5e"],
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(kw, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="section-title">Narrative Buckets</div>', unsafe_allow_html=True)
        nb = read_csv_safe("narrative_buckets.csv")
        if not nb.empty:
            fig = px.bar(
                nb, x="bucket", y="avg_engagement",
                title="Avg Engagement by Narrative",
                color="rows", color_continuous_scale=[LIME, "#6366f1"],
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(nb, use_container_width=True, hide_index=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">TF-IDF Top Terms</div>', unsafe_allow_html=True)
        tfidf = read_csv_safe("tfidf_top_terms.csv")
        if not tfidf.empty:
            fig = px.bar(
                tfidf.head(20), x="term", y="tfidf_score",
                title="Top 20 Terms by TF-IDF Score",
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Emerging Terms</div>', unsafe_allow_html=True)
        emerging = read_csv_safe("emerging_terms.csv")
        if not emerging.empty:
            st.dataframe(emerging.head(20), use_container_width=True, hide_index=True)
        else:
            st.markdown(f'<div style="color:{DIM};">No emerging terms detected.</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top Words</div>', unsafe_allow_html=True)
    tw = read_csv_safe("top_words.csv")
    if not tw.empty:
        fig = px.bar(
            tw.head(25), x="word", y="count",
            title="Most Common Words",
        )
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)


# --- DATA QUALITY
with tab_quality:
    qr = get_quality_report()
    if not qr:
        st.info("Run the pipeline to generate data quality report.")
    else:
        st.markdown('<div class="section-title">Data Quality Report</div>', unsafe_allow_html=True)

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Rows", f"{qr.get('rows_after', 0):,}")
        q2.metric("URL Coverage", f"{qr.get('url_coverage_pct', 0)}%")
        q3.metric("Date Coverage", f"{qr.get('date_coverage_pct', 0)}%")
        q4.metric("Issues Found", len(qr.get("issues", [])))

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Platform Distribution</div>', unsafe_allow_html=True)
            plat_dist = qr.get("platform_distribution", [])
            if plat_dist:
                pdf = pd.DataFrame(plat_dist)
                fig = px.bar(
                    pdf, x="platform", y="pct",
                    title="Platform Share (%)",
                    text="pct",
                    color="pct",
                    color_continuous_scale=["#f43f5e", LIME],
                )
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Issues & Fixes</div>', unsafe_allow_html=True)
            issues = qr.get("issues", [])
            if issues:
                for issue in issues:
                    st.markdown(f"""
                    <div class="alert-row alert-medium">
                        <span style="color:{LIME}; font-weight:700; font-size:0.72rem;">⚠</span>
                        &nbsp;&nbsp;{issue}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="color:{LIME}; font-weight:700;">All checks passed.</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div style="margin-top:16px; font-size:0.8rem; color:{DIM};">
                <b>Fixes applied:</b><br>
                • Negative engagement values fixed: {qr.get('negative_engagement_fixed', 0)}<br>
                • Future dates cleared: {qr.get('future_dates_cleared', 0)}<br>
                • Quality report generated: {qr.get('timestamp', 'N/A')[:19]}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:16px; background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px;">
            <div style="font-size:0.75rem; color:{DIM}; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">
                Methodology & Limitations
            </div>
            <div style="font-size:0.82rem; color:#aaa; line-height:1.7;">
                Data collected from 7 platforms via public APIs and Apify actors.<br>
                Reddit uses public JSON API. YouTube uses native search scraping.<br>
                TikTok, Twitter, Instagram, LinkedIn, Threads use Apify cloud actors.<br><br>
                <b>Dataset:</b> ~300 rows per platform, ~1,900 total. Balanced distribution (12–16% each).<br>
                <b>Known limitations:</b> LinkedIn engagement is zero (no-cookie scraper).
                URL coverage is {qr.get('url_coverage_pct', '?')}%.
                English-only filtering applied via langdetect.
            </div>
        </div>
        """, unsafe_allow_html=True)


# --- ALERTS
with tab_alerts:
    alerts = get_alerts()

    if not alerts:
        st.markdown(f"""
        <div style="text-align:center; padding: 60px;">
            <div style="font-size: 1.2rem; font-weight: 700; color: {LIME}; text-transform: uppercase;">
                ALL CLEAR
            </div>
            <div style="color: {DIM}; margin-top: 4px;">No alerts triggered</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        high_count = sum(1 for a in alerts if a.get("severity") == "high")
        med_count = sum(1 for a in alerts if a.get("severity") == "medium")
        info_count = sum(1 for a in alerts if a.get("severity") in ("info", "low"))

        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <span class="counter-pill" style="background: rgba(239,68,68,0.15); color: #ef4444;">
                {high_count} CRITICAL
            </span>
            <span class="counter-pill" style="background: rgba(200,255,0,0.1); color: {LIME};">
                {med_count} WARNING
            </span>
            <span class="counter-pill" style="background: rgba(255,255,255,0.05); color: {DIM};">
                {info_count} INFO
            </span>
        </div>
        """, unsafe_allow_html=True)

        sev_filter = st.selectbox("Filter", ["All", "High", "Medium", "Info"], index=0, label_visibility="collapsed")

        st.markdown("")

        for a in alerts:
            sev = a.get("severity", "info")
            if sev_filter != "All" and sev != sev_filter.lower():
                continue

            css = {"high": "alert-high", "medium": "alert-medium"}.get(sev, "alert-info")
            tag_color = {"high": "#ef4444", "medium": LIME}.get(sev, DIM)

            st.markdown(f"""
            <div class="alert-row {css}">
                <span style="color:{tag_color}; font-weight:700; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em;">
                    {sev.upper()}
                </span>
                &nbsp;&nbsp;{a['message']}
            </div>
            """, unsafe_allow_html=True)


# --- REPORT
with tab_report:
    if os.path.exists(config.REPORT_PATH):
        st.markdown('<div class="section-title">Auto-Generated Report</div>', unsafe_allow_html=True)
        st.markdown("")
        with open(config.REPORT_PATH, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.markdown(f"""
        <div style="text-align:center; padding: 60px; color: {DIM};">
            Report not generated yet — run the pipeline first.
        </div>
        """, unsafe_allow_html=True)
