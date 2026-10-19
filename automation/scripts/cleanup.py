#!/usr/bin/env python3
"""Delete expired Render static sites (not the active redirect)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib_paths import REGISTRY_PATH, SCHEDULE_PATH
from registry import load, save, sites_to_delete
from render_api import delete_service


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lifetime-minutes", type=int, default=None)
    args = p.parse_args()

    sched = json.loads(SCHEDULE_PATH.read_text())
    lifetime = args.lifetime_minutes or int(sched.get("delete_lifetime_minutes") or 15)

    doomed = sites_to_delete(lifetime)
    if not doomed:
        print("No expired sites to delete.")
        return 0

    data = load()
    remove_ids = {d["service_id"] for d in doomed}
    for site in doomed:
        print(f"Deleting Render service {site['name']} ({site['service_id']})")
        delete_service(site["service_id"])

    data["sites"] = [s for s in data.get("sites", []) if s["service_id"] not in remove_ids]
    save(data)
    print(f"Removed {len(doomed)} site(s) from registry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
