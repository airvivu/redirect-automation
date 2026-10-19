"""Push branch-2 URL to all VPS Redis keys over SSH."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from lib_paths import SERVERS_PATH


def load_servers() -> list[dict]:
    data = json.loads(SERVERS_PATH.read_text())
    return data["servers"]


def set_redirect_url(url: str) -> list[str]:
    logs: list[str] = []
    for s in load_servers():
        host = s["host"]
        user = s.get("ssh_user", "root")
        key = s["redis_key"]
        name = s.get("name", host)
        # Escape single quotes in URL for remote shell
        safe = url.replace("'", "'\"'\"'")
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            f"{user}@{host}",
            f"redis-cli SET {key} '{safe}'",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(f"{name}: ssh/redis failed: {proc.stderr or proc.stdout}")
        logs.append(f"{name}: SET {key} OK")
    return logs
