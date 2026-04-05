import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMerge:
    def test_safe_int_normal(self):
        from pipeline.merge import safe_int
        assert safe_int("123") == 123
        assert safe_int("1,234") == 1234
        assert safe_int(0) == 0

    def test_safe_int_edge_cases(self):
        from pipeline.merge import safe_int
        assert safe_int(None) == 0
        assert safe_int("nan") == 0
        assert safe_int("") == 0
        assert safe_int("none") == 0
        assert safe_int("abc") == 0

    def test_normalize_date(self):
        from pipeline.merge import normalize_date
        assert normalize_date("2024-03-15") == "2024-03-15"
        assert normalize_date("2024-03-15T10:30:00Z") == "2024-03-15"
        assert normalize_date("") == ""
        assert normalize_date(None) == ""

    def test_clean_text(self):
        from pipeline.merge import clean_text
        assert clean_text(None) == ""
        assert clean_text("") == ""
        assert clean_text("  hello  world  ") == "hello world"

    def test_deduplicate(self):
        from pipeline.merge import deduplicate
        rows = [
            {"text": "Hello world", "platform": "reddit"},
            {"text": "hello world", "platform": "youtube"},
            {"text": "Different text", "platform": "reddit"},
        ]
        result = deduplicate(rows)
        assert len(result) == 2


class TestSentiment:
    def test_score_positive(self):
        from pipeline.sentiment import _score
        score = _score("This is amazing and wonderful!")
        assert score > 0

    def test_score_negative(self):
        from pipeline.sentiment import _score
        score = _score("This is terrible and awful!")
        assert score < 0

    def test_score_empty(self):
        from pipeline.sentiment import _score
        assert _score("") == 0.0
        assert _score(None) == 0.0

    def test_label(self):
        from pipeline.sentiment import _label
        assert _label(0.5) == "positive"
        assert _label(-0.5) == "negative"
        assert _label(0.0) == "neutral"


class TestAlerts:
    def test_check_viral_posts(self):
        import pandas as pd
        from pipeline.alerts import check_viral_posts

        df = pd.DataFrame({
            "platform": ["reddit"] * 50 + ["youtube"] * 10 + ["youtube"],
            "engagement": [10] * 50 + [100] * 10 + [50000],
            "text": [f"post {i}" for i in range(61)],
        })
        alerts = check_viral_posts(df)
        assert len(alerts) >= 1
        assert alerts[0]["type"] == "viral_post"
        assert alerts[0]["platform"] == "youtube"


class TestDateParsing:
    def test_normalize_date_iso(self):
        from pipeline.merge import normalize_date
        assert normalize_date("2024-03-15T10:30:00Z") == "2024-03-15"

    def test_normalize_date_space_separated(self):
        from pipeline.merge import normalize_date
        assert normalize_date("2024-03-15 10:30:00") == "2024-03-15"


class TestSearchEngine:
    def test_import(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scrapers"))
        from search_engine import search
        assert callable(search)
