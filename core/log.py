import logging
import os
import sys
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_ROOT, "output", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

_file_handler = logging.FileHandler(
    os.path.join(_LOG_DIR, "pipeline.log"), encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s"))

_logger = logging.getLogger("growth_intel")
_logger.setLevel(logging.DEBUG)
_logger.addHandler(_file_handler)


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def info(msg):
    print(f"[{_ts()}]  {msg}", flush=True)
    _logger.info(msg)


def ok(msg):
    print(f"[{_ts()}]  OK  {msg}", flush=True)
    _logger.info(f"OK  {msg}")


def warn(msg):
    print(f"[{_ts()}]  WARN  {msg}", file=sys.stderr, flush=True)
    _logger.warning(msg)


def fail(msg):
    print(f"[{_ts()}]  FAIL  {msg}", file=sys.stderr, flush=True)
    _logger.error(msg)


def section(title):
    print(f"\n{'=' * 60}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'=' * 60}", flush=True)
    _logger.info(f"=== {title} ===")
