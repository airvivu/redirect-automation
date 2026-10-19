#!/usr/bin/env python3
"""Delete one Render static site and update sites-registry.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from registry import load, save
from render_api import delete_service
from redis_update import set_redirect_url


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--service-id", required=True)
    args = p.parse_args()
    sid = args.service_id.strip()

    data = load()
    sites = data.get("sites", [])
    match = next((s for s in sites if s["service_id"] == sid), None)
    if not match:
        print(f"Service {sid} not in registry (will still try Render delete).")
    else:
        print(f"Removing {match.get('name')} {match.get('url')}")

    delete_service(sid)

    data["sites"] = [s for s in sites if s["service_id"] != sid]
    if data.get("active_service_id") == sid:
        if data["sites"]:
            latest = data["sites"][-1]
            data["active_service_id"] = latest["service_id"]
            data["active_url"] = latest["url"]
        else:
            data["active_service_id"] = None
            data["active_url"] = None
    save(data)
    print("Registry updated.")
    new_url = data.get("active_url")
    if new_url:
        print(f"Updating Redis to remaining active URL: {new_url}")
        for line in set_redirect_url(new_url):
            print(line)
    elif data.get("active_service_id") is None:
        fallback = "https://google.com"
        print(f"No sites left; Redis set to fallback {fallback}")
        for line in set_redirect_url(fallback):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
