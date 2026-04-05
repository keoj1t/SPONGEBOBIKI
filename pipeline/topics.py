import os
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from core import config
from core import log

STOPWORDS_LIST = list(config.STOPWORDS)


def run_topic_analysis(df):
    log.section("TOPIC ANALYSIS (TF-IDF)")

    texts = df["text"].fillna("").astype(str)
    texts = texts[texts.str.len() >= 20]
    if len(texts) < 10:
        log.warn("Not enough text for TF-IDF")
        return

    os.makedirs(config.REPORTS_DIR, exist_ok=True)

    tfidf = TfidfVectorizer(
        max_features=200,
        stop_words=STOPWORDS_LIST,
        min_df=3,
        max_df=0.8,
        token_pattern=r"\b[a-zA-Z]{3,}\b",
    )
    matrix = tfidf.fit_transform(texts)
    feature_names = tfidf.get_feature_names_out()
    scores = matrix.mean(axis=0).A1
    top_idx = scores.argsort()[::-1][:50]

    emerging = []
    for idx in top_idx:
        emerging.append({
            "term": feature_names[idx],
            "tfidf_score": round(float(scores[idx]), 5),
        })
    emerging_df = pd.DataFrame(emerging)
    emerging_df.to_csv(
        os.path.join(config.REPORTS_DIR, "tfidf_top_terms.csv"),
        index=False, encoding="utf-8-sig",
    )

    dated = df[df["parsed_date"].notna()].copy()
    if len(dated) >= 40:
        dated = dated.sort_values("parsed_date")
        cutoff = len(dated) // 2
        older = dated.iloc[:cutoff]["text"].fillna("").str.lower()
        newer = dated.iloc[cutoff:]["text"].fillna("").str.lower()

        def count_words(series):
            counter = Counter()
            for t in series:
                words = re.findall(r"\b[a-zA-Z]{3,}\b", t)
                counter.update(w for w in words if w not in config.STOPWORDS)
            return counter

        old_counts = count_words(older)
        new_counts = count_words(newer)
        old_total = max(sum(old_counts.values()), 1)
        new_total = max(sum(new_counts.values()), 1)

        rising = []
        for word, new_c in new_counts.most_common(500):
            old_c = old_counts.get(word, 0)
            old_rate = old_c / old_total
            new_rate = new_c / new_total
            if new_c >= 5 and (old_rate == 0 or new_rate / old_rate >= 1.5):
                rising.append({
                    "term": word,
                    "old_count": old_c,
                    "new_count": new_c,
                    "growth": round(new_rate / max(old_rate, 1e-9), 1),
                })
        rising_df = pd.DataFrame(rising).sort_values("growth", ascending=False).head(30)
        rising_df.to_csv(
            os.path.join(config.REPORTS_DIR, "emerging_terms.csv"),
            index=False, encoding="utf-8-sig",
        )
        log.ok(f"Found {len(rising_df)} emerging terms")

    log.ok(f"TF-IDF done — top {len(emerging_df)} terms extracted")
