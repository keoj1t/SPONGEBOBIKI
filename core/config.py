import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_FINAL = os.path.join(ROOT, "data", "final")
REPORTS_DIR = os.path.join(ROOT, "output", "reports")
CHARTS_DIR = os.path.join(ROOT, "output", "charts")
ALERTS_DIR = os.path.join(ROOT, "output", "alerts")
LOGS_DIR = os.path.join(ROOT, "output", "logs")

SCRAPER_OUTPUTS = {
    "reddit":    os.path.join(ROOT, "data", "raw", "reddit.csv"),
    "youtube":   os.path.join(ROOT, "data", "raw", "youtube.csv"),
    "tiktok":    os.path.join(ROOT, "data", "raw", "tiktok.csv"),
    "twitter":   os.path.join(ROOT, "data", "raw", "twitter.csv"),
    "instagram": os.path.join(ROOT, "data", "raw", "instagram.csv"),
    "linkedin":  os.path.join(ROOT, "data", "raw", "linkedin.csv"),
    "threads":   os.path.join(ROOT, "data", "raw", "threads.csv"),
}

SCRAPER_SCRIPTS = {
    "reddit":    os.path.join(ROOT, "scrapers", "reddit.py"),
    "youtube":   os.path.join(ROOT, "scrapers", "youtube.py"),
    "tiktok":    os.path.join(ROOT, "scrapers", "tiktok.py"),
    "twitter":   os.path.join(ROOT, "scrapers", "twitter.py"),
    "instagram": os.path.join(ROOT, "scrapers", "instagram.py"),
    "linkedin":  os.path.join(ROOT, "scrapers", "linkedin.py"),
    "threads":   os.path.join(ROOT, "scrapers", "threads.py"),
}

MERGED_DATASET = os.path.join(DATA_FINAL, "final_dataset_eng.csv")
REPORT_PATH = os.path.join(REPORTS_DIR, "auto_report.md")
ALERTS_PATH = os.path.join(ALERTS_DIR, "alerts.json")

FINAL_COLUMNS = [
    "platform", "text", "likes", "comments", "views",
    "date", "engagement", "content_type", "url", "text_length",
]

LANGUAGE = "en"
MIN_TEXT_LENGTH_FOR_DETECTION = 20

TOP_N_POSTS = 20
TOP_N_WORDS = 40

KEYWORDS = [
    "switch", "switched", "chatgpt", "gpt", "compare", "comparison",
    "trust", "safe", "safety", "enterprise", "productivity", "workflow",
    "code", "coding", "developer", "developers", "api", "reasoning",
    "context", "tutorial", "review", "vs", "better", "faster", "roi",
    "time", "hours", "cost", "save", "saved",
]

STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "your", "you",
    "are", "was", "but", "not", "all", "has", "had", "its", "they", "their",
    "them", "his", "her", "our", "out", "who", "how", "why", "what", "when",
    "where", "about", "into", "than", "then", "just", "also", "can", "could",
    "would", "should", "will", "more", "some", "very", "much", "like", "use",
    "using", "used", "over", "under", "only", "even", "really", "because",
    "been", "being", "after", "before", "while", "does", "did", "doing",
    "make", "made", "many", "most", "such", "these", "those", "there", "here",
    "it", "is", "a", "an", "of", "to", "in", "on", "at", "as", "or", "by",
    "if", "we", "i", "he", "she", "they", "my", "me", "so", "no", "yes",
    "claude", "anthropic", "chatgpt", "gpt", "ai",
}

NARRATIVE_BUCKETS = {
    "comparison":         r"\b(vs|versus|better than|compared to|comparison|chatgpt|gpt)\b",
    "switching":          r"\b(switched|switching|moved from|left .* for|from chatgpt to)\b",
    "productivity_roi":   r"\b(saved|save|hours|time saved|roi|cost|faster|productivity)\b",
    "trust_safety":       r"\b(trust|safe|safety|honest|reliable|uncertainty|careful)\b",
    "coding_dev":         r"\b(code|coding|developer|developers|api|debug|repo|engineering)\b",
    "education_tutorial": r"\b(how to|tutorial|guide|learn|explained|breakdown|review)\b",
}

ALERT_ENGAGEMENT_SPIKE_MULTIPLIER = 3.0
ALERT_MENTION_SPIKE_MULTIPLIER = 3.0
ALERT_TOP_KEYWORD_WINDOW = 10
