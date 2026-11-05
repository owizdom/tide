"""Tripwire (spec 0001 AT12): the run fails when zero tests ran or any test was skipped."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_stats = {"ran": 0, "skipped": 0}


def pytest_runtest_logreport(report):
    if report.when == "call":
        _stats["ran"] += 1
    if report.skipped:
        _stats["skipped"] += 1


def pytest_sessionfinish(session, exitstatus):
    if _stats["ran"] == 0 or _stats["skipped"]:
        print(f"\nTRIPWIRE: ran={_stats['ran']} skipped={_stats['skipped']}")
        session.exitstatus = 1
