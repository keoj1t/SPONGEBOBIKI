import os
import subprocess
import sys
import shutil

from core import config
from core import log


def _run_scraper(name):
    script = config.SCRAPER_SCRIPTS.get(name)
    if not script or not os.path.exists(script):
        log.warn(f"Scraper script not found: {script}")
        return False

    workdir = os.path.dirname(script)
    log.info(f"Running {name} scraper -> {os.path.basename(script)}")

    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            log.fail(f"{name} scraper exited with code {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().splitlines()[-5:]:
                    log.warn(f"  {line}")
            return False

        log.ok(f"{name} scraper finished")
        return True

    except subprocess.TimeoutExpired:
        log.fail(f"{name} scraper timed out (600s)")
        return False
    except Exception as e:
        log.fail(f"{name} scraper error: {e}")
        return False


def _copy_to_raw(name):
    src = config.SCRAPER_OUTPUTS.get(name)
    if not src or not os.path.exists(src):
        log.warn(f"Output CSV missing for {name}: {src}")
        return False

    os.makedirs(config.DATA_RAW, exist_ok=True)
    dst = os.path.join(config.DATA_RAW, f"{name}.csv")
    if os.path.abspath(src) == os.path.abspath(dst):
        log.ok(f"{name} already in data/raw/")
        return True
    shutil.copy2(src, dst)
    log.ok(f"Copied {name} -> data/raw/{name}.csv")
    return True


def collect_raw_csvs():
    for name in config.SCRAPER_OUTPUTS:
        _copy_to_raw(name)
