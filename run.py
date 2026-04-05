import argparse
import os
import shutil
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from core import config
from core import log


def _check_environment():
    missing = []
    for pkg in ["pandas", "matplotlib", "langdetect", "vaderSentiment", "sklearn", "scipy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        log.warn(f"Missing packages: {', '.join(missing)} — run: pip install -r requirements.txt")
    return len(missing) == 0


def _backup_dataset():
    if not os.path.exists(config.MERGED_DATASET):
        return
    backup_dir = os.path.join(config.DATA_FINAL, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"final_dataset_eng_{ts}.csv")
    shutil.copy2(config.MERGED_DATASET, backup_path)
    # Keep only last 5 backups
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".csv")],
        reverse=True,
    )
    for old in backups[5:]:
        os.remove(os.path.join(backup_dir, old))
    log.ok(f"Backup saved -> {backup_path}")


def main():
    parser = argparse.ArgumentParser(description="Claude Growth Intelligence Pipeline")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip running scrapers, use existing CSVs")
    parser.add_argument("--append", action="store_true", help="Append to existing dataset instead of overwriting")
    args = parser.parse_args()

    start = time.time()
    log.section("GROWTH INTELLIGENCE PIPELINE")
    log.info(f"Mode: {'skip-scrape' if args.skip_scrape else 'full run'}")

    _check_environment()
    _backup_dataset()

    from core.wrapper import collect_raw_csvs, _run_scraper, _copy_to_raw

    if args.skip_scrape:
        log.info("Skipping scrapers — copying existing CSVs to data/raw/")
        collect_raw_csvs()
    else:
        log.section("SCRAPING")
        for name in config.SCRAPER_SCRIPTS:
            ok = _run_scraper(name)
            status = "ok" if ok else "FAILED"
            log.info(f"  {name}: {status}")
            _copy_to_raw(name)

    from pipeline.merge import merge_datasets
    rows, stats = merge_datasets(append=args.append)

    if not rows:
        log.fail("No data after merge. Stopping.")
        return 1

    import pandas as pd
    steps_ok = ["merge"]
    steps_fail = []

    df = pd.read_csv(config.MERGED_DATASET)
    for col in ["likes", "comments", "views", "engagement"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["parsed_date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    try:
        from pipeline.data_quality import run_data_quality
        df, quality_report = run_data_quality(df)
        df.to_csv(config.MERGED_DATASET, index=False, encoding="utf-8-sig")
        steps_ok.append("data_quality")
    except Exception as e:
        log.fail(f"Data quality failed: {e}")
        steps_fail.append("data_quality")

    try:
        from pipeline.sentiment import run_sentiment
        df = run_sentiment(df)
        df.to_csv(config.MERGED_DATASET, index=False, encoding="utf-8-sig")
        steps_ok.append("sentiment")
    except Exception as e:
        log.fail(f"Sentiment failed: {e}")
        steps_fail.append("sentiment")

    try:
        from pipeline.analyze import run_analysis
        df, analysis_results = run_analysis()
        steps_ok.append("analysis")
    except Exception as e:
        log.fail(f"Analysis failed: {e}")
        steps_fail.append("analysis")

    try:
        from pipeline.timeseries import run_timeseries
        run_timeseries(df)
        steps_ok.append("timeseries")
    except Exception as e:
        log.fail(f"Timeseries failed: {e}")
        steps_fail.append("timeseries")

    try:
        from pipeline.topics import run_topic_analysis
        run_topic_analysis(df)
        steps_ok.append("topics")
    except Exception as e:
        log.fail(f"Topics failed: {e}")
        steps_fail.append("topics")

    alerts = []
    try:
        from pipeline.alerts import run_alerts
        alerts = run_alerts()
        steps_ok.append("alerts")
    except Exception as e:
        log.fail(f"Alerts failed: {e}")
        steps_fail.append("alerts")

    try:
        from pipeline.report import generate_report
        generate_report()
        steps_ok.append("report")
    except Exception as e:
        log.fail(f"Report generation failed: {e}")
        steps_fail.append("report")

    from pipeline.scheduler import _log_run
    elapsed = time.time() - start
    _log_run("ok" if not steps_fail else "partial", elapsed)

    log.section("PIPELINE COMPLETE")
    log.ok(f"Total rows: {len(rows)}")
    log.ok(f"Steps OK: {', '.join(steps_ok)}")
    if steps_fail:
        log.warn(f"Steps FAILED: {', '.join(steps_fail)}")
    log.ok(f"Alerts: {len(alerts)}")
    log.ok(f"Time: {elapsed:.1f}s")
    log.info(f"Dashboard:  streamlit run app/dashboard.py")
    log.info(f"Report:     output/reports/auto_report.md")

    return 1 if steps_fail else 0


if __name__ == "__main__":
    sys.exit(main())
