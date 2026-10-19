from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from lib_paths import REGISTRY_PATH


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"active_url": None, "active_service_id": None, "sites": []}
    return json.loads(REGISTRY_PATH.read_text())


def save(data: dict[str, Any]) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n")


def add_site(service_id: str, name: str, url: str) -> dict[str, Any]:
    data = load()
    entry = {"service_id": service_id, "name": name, "url": url, "created_at": _now()}
    data["sites"].append(entry)
    data["active_url"] = url
    data["active_service_id"] = service_id
    save(data)
    return data


def sites_to_delete(delete_lifetime_minutes: int) -> list[dict]:
    data = load()
    active_id = data.get("active_service_id")
    cutoff = datetime.now(timezone.utc).timestamp() - delete_lifetime_minutes * 60
    doomed: list[dict] = []
    kept: list[dict] = []
    for site in data.get("sites", []):
        created = datetime.fromisoformat(site["created_at"].replace("Z", "+00:00"))
        if site["service_id"] == active_id:
            kept.append(site)
            continue
        if created.timestamp() <= cutoff:
            doomed.append(site)
        else:
            kept.append(site)
    return doomed
