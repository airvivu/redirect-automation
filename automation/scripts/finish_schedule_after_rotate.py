#!/usr/bin/env python3
"""Set last_create_at / next_create_at after an immediate rotate."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from lib_paths import SCHEDULE_PATH


def main() -> None:
    data = json.loads(SCHEDULE_PATH.read_text())
    interval = int(data.get("create_interval_minutes") or 10)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    data["last_create_at"] = now.isoformat()
    data["next_create_at"] = (now + timedelta(minutes=interval)).isoformat()
    SCHEDULE_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"next_create_at={data['next_create_at']}")


if __name__ == "__main__":
    main()
