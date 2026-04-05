import os
import sys
import time
from datetime import datetime

from core import config
from core import log

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


SCHEDULE_LOG = os.path.join(config.ROOT, "output", "schedule_log.txt")


def _log_run(status, elapsed=0, error=""):
    os.makedirs(os.path.dirname(SCHEDULE_LOG), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] status={status} elapsed={elapsed:.1f}s"
    if error:
        entry += f" error={error}"
    with open(SCHEDULE_LOG, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def _pipeline_job():
    from run import main as run_pipeline
    start = time.time()
    try:
        sys.argv = ["run.py", "--skip-scrape"]
        code = run_pipeline()
        elapsed = time.time() - start
        _log_run("ok" if code == 0 else f"exit-{code}", elapsed)
    except Exception as e:
        _log_run("error", time.time() - start, str(e))


def start_scheduler(interval_minutes=60):
    if not HAS_APSCHEDULER:
        log.warn("apscheduler not installed — scheduling unavailable")
        return None

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _pipeline_job,
        "interval",
        minutes=interval_minutes,
        id="pipeline_refresh",
        replace_existing=True,
    )
    scheduler.start()
    log.ok(f"Scheduler started — pipeline runs every {interval_minutes} min")
    return scheduler


def get_schedule_history(max_lines=20):
    if not os.path.exists(SCHEDULE_LOG):
        return []
    with open(SCHEDULE_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines[-max_lines:]]


def get_last_run_time():
    if not os.path.exists(SCHEDULE_LOG):
        return None
    with open(SCHEDULE_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return None
    last = lines[-1].strip()
    try:
        ts_str = last.split("]")[0].replace("[", "").strip()
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        return None
