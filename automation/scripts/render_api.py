"""Render API helpers for ephemeral static sites."""
from __future__ import annotations

import json
import os
import random
import secrets
import string
import time
from typing import Any

_NAME_ALPHABET = string.ascii_lowercase + string.digits

import requests

from lib_paths import CONFIG_DIR

API = "https://api.render.com/v1"


def _headers() -> dict[str, str]:
    key = os.environ.get("RENDER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("RENDER_API_KEY is not set")
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def _load_name_config() -> dict[str, list[str]]:
    path = CONFIG_DIR / "render-name-words.json"
    data = json.loads(path.read_text())

    def clean(items: list) -> list[str]:
        return [str(w).strip().lower() for w in items if str(w).strip()]

    words = clean(data.get("words") or [])
    suffixes = clean(data.get("suffixes") or [])
    if not words:
        raise RuntimeError(f"No words in {path}")
    if not suffixes:
        raise RuntimeError(f"No suffixes in {path}")
    return {"words": words, "suffixes": suffixes}


def _random_alnum(length: int) -> str:
    return "".join(secrets.choice(_NAME_ALPHABET) for _ in range(length))


def random_service_name() -> str:
    """e.g. lightwolfweb6t4jdu — two words + suffix + 6 alnum."""
    cfg = _load_name_config()
    w1, w2 = random.choice(cfg["words"]), random.choice(cfg["words"])
    suffix = random.choice(cfg["suffixes"])
    tail = _random_alnum(6)
    return f"{w1}{w2}{suffix}{tail}"


def create_static_site(
    *,
    name: str,
    repo: str,
    branch: str,
    build_command: str,
    publish_path: str,
    auto_deploy: str = "no",
) -> dict[str, Any]:
    if not repo.startswith("https://"):
        repo = f"https://github.com/{repo.strip().strip('/')}"
    body: dict[str, Any] = {
        "type": "static_site",
        "name": name,
        "repo": repo,
        "branch": branch or "main",
        "autoDeploy": auto_deploy,
        "serviceDetails": {
            "buildCommand": build_command,
            "publishPath": publish_path,
        },
    }
    owner = os.environ.get("RENDER_OWNER_ID", "").strip()
    if owner:
        body["ownerId"] = owner
    r = requests.post(f"{API}/services", headers={**_headers(), "Content-Type": "application/json"}, json=body, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"Render create failed {r.status_code}: {r.text}")
    return r.json()


def service_public_url(service: dict[str, Any]) -> str:
    slug = service.get("slug") or service.get("name") or service.get("service", {}).get("name")
    if not slug and "service" in service:
        slug = service["service"].get("name")
    if not slug:
        raise RuntimeError(f"Could not resolve service URL from: {service}")
    return f"https://{slug}.onrender.com"


def service_id(service: dict[str, Any]) -> str:
    if "id" in service:
        return service["id"]
    if "service" in service and "id" in service["service"]:
        return service["service"]["id"]
    raise RuntimeError(f"No service id in: {service}")


def trigger_deploy(service_id: str) -> None:
    r = requests.post(
        f"{API}/services/{service_id}/deploys",
        headers={**_headers(), "Content-Type": "application/json"},
        json={"clearCache": "clear"},
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Render deploy trigger failed {r.status_code}: {r.text}")


def wait_for_live_url(url: str, timeout_sec: int = 900, interval: int = 20) -> bool:
    """Best-effort: static site may 404 until first deploy finishes."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=15, allow_redirects=True)
            if r.status_code < 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False


def delete_service(service_id: str) -> None:
    r = requests.delete(f"{API}/services/{service_id}", headers=_headers(), timeout=60)
    if r.status_code not in (200, 204, 404):
        raise RuntimeError(f"Render delete failed {r.status_code}: {r.text}")
