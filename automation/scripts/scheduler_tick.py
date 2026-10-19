#!/usr/bin/env python3
"""Run scheduled create if due; always run cleanup."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib_paths import SCHEDULE_PATH


def main() -> int:
    sched = json.loads(SCHEDULE_PATH.read_text())
    scripts = Path(__file__).resolve().parent

    # Cleanup every tick
    subprocess.check_call([sys.executable, str(scripts / "cleanup.py")])

    if not sched.get("enabled"):
        print("Schedule disabled; skip create.")
        return 0

    if not sched.get("github_repo"):
        print("No github_repo in schedule; skip create.")
        return 0

    interval = int(sched.get("create_interval_minutes") or 10)
    now = datetime.now(timezone.utc)
    next_at = sched.get("next_create_at")
    if next_at:
        due = now >= datetime.fromisoformat(next_at.replace("Z", "+00:00"))
    else:
        due = True

    if not due:
        print(f"Next create at {next_at}; skip.")
        return 0

    print("Schedule due — running rotate.py")
    subprocess.check_call([sys.executable, str(scripts / "rotate.py")])

    sched["last_create_at"] = now.replace(microsecond=0).isoformat()
    sched["next_create_at"] = (now + timedelta(minutes=interval)).replace(microsecond=0).isoformat()
    SCHEDULE_PATH.write_text(json.dumps(sched, indent=2) + "\n")
    print(f"Next create scheduled at {sched['next_create_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
