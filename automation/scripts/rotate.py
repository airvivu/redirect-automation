#!/usr/bin/env python3
"""Create Render static site + update Redis on all servers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib_paths import SCHEDULE_PATH, SERVERS_PATH
from redis_update import set_redirect_url
from registry import add_site
from render_api import (
    create_static_site,
    random_service_name,
    service_id,
    service_public_url,
    trigger_deploy,
    wait_for_live_url,
)


def load_schedule() -> dict:
    return json.loads(SCHEDULE_PATH.read_text())


def load_render_prefix() -> str:
    cfg = json.loads(SERVERS_PATH.read_text())
    return cfg.get("render", {}).get("name_prefix", "rs-")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", help="owner/repo or full GitHub URL")
    p.add_argument("--branch", default=None)
    p.add_argument("--build-command", default=None)
    p.add_argument("--publish-path", default=None)
    args = p.parse_args()

    sched = load_schedule()
    repo = args.repo or sched.get("github_repo")
    if not repo:
        print("Missing github repo (arg or schedule.json)", file=sys.stderr)
        return 1

    branch = args.branch or sched.get("branch") or "main"
    build = args.build_command or sched.get("build_command") or "npm ci && npm run build"
    publish = args.publish_path or sched.get("publish_path") or "dist"
    prefix = load_render_prefix()
    name = random_service_name(prefix)

    print(f"Creating Render static site: {name} from {repo}")
    created = create_static_site(
        name=name,
        repo=repo,
        branch=branch,
        build_command=build,
        publish_path=publish,
        auto_deploy="no",
    )
    sid = service_id(created)
    url = service_public_url(created)
    print(f"Service id={sid} url={url}")

    print("Triggering deploy…")
    trigger_deploy(sid)
    print("Waiting for URL to respond (may take several minutes)…")
    wait_for_live_url(url)

    print("Updating Redis on all servers…")
    for line in set_redirect_url(url):
        print(line)

    add_site(sid, name, url)
    print(f"Done. Active redirect: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
