"""
run_all.py - Run all data updaters in sequence.

Updates these tables in the project database (path comes from DB_PATH in .env):
  1. scrapers.tether -> tether table (USDT price)
  2. scrapers.gold   -> gold table   (18k gold price)
  3. scrapers.bama   -> ads table    (zero-km car ads from bama.ir)

Usage (from the project root):
    python run_all.py

A failure in one updater does not stop the others.
The exit code is 0 only if every updater succeeded.
"""

import subprocess
import sys
import time

from core.config import DB_PATH, PROJECT_ROOT

# Run order matters only for readability; the updaters are independent.
UPDATERS = [
    "scrapers.tether",
    "scrapers.gold",
    "scrapers.bama",
]


def run_updater(module):
    """Run one updater as `python -m <module>` from the project root."""
    print("\n" + "=" * 60, flush=True)
    print(f"START: {module}", flush=True)
    print("=" * 60, flush=True)

    started = time.time()
    result = subprocess.run([sys.executable, "-m", module], cwd=PROJECT_ROOT)
    elapsed = time.time() - started

    ok = result.returncode == 0
    status = "OK" if ok else f"FAILED (exit code {result.returncode})"
    print(f"\n{module}: {status} in {elapsed:.0f}s", flush=True)
    return ok, elapsed


def main():
    print("=" * 60)
    print("Full database update")
    print(f"Database: {DB_PATH}")
    print("=" * 60, flush=True)

    # sqlite silently creates an empty database if the file is missing,
    # so stop here if DB_PATH points to the wrong place.
    if not DB_PATH.is_file():
        print(f"ERROR: database file not found: {DB_PATH}")
        print("Check DB_PATH in .env.")
        sys.exit(1)

    results = {}
    for module in UPDATERS:
        results[module] = run_updater(module)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for module, (ok, elapsed) in results.items():
        print(f"  {'OK    ' if ok else 'FAILED'}  {module:<20} {elapsed:>5.0f}s")

    failed = [m for m, (ok, _) in results.items() if not ok]
    print("=" * 60)
    if failed:
        print(f"Done with errors in: {', '.join(failed)}")
        sys.exit(1)
    print("Done. All updaters succeeded.")


if __name__ == "__main__":
    main()