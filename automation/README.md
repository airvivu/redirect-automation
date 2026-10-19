# Render → Redis redirect automation

Creates ephemeral **Render static sites** from a GitHub repo, sets **`https://….onrender.com`** on all VPS Redis branch-2 keys via **SSH**, and deletes old Render services after a lifetime.

## Flow

1. **GitHub Actions** runs `rotate.py` → Render API (new random name `rs-<hex>`) → deploy → **SSH** `redis-cli SET` on each server in `config/servers.json`.
2. **Cleanup** removes Render services older than `delete_lifetime_minutes` (never deletes the **active** site).
3. **Scheduler** (every 5 min) runs cleanup + create when `schedule.json` says so.

## One-time setup

### 1. GitHub secrets (repo settings → Secrets)

| Secret | Value |
|--------|--------|
| `RENDER_API_KEY` | From [Render account API keys](https://dashboard.render.com/u/settings#api-keys) |
| `RENDER_OWNER_ID` | Optional; Render workspace/owner id if create API requires it |
| `SSH_PRIVATE_KEY` | Full **`~/.ssh/id_ed25519`** (same key as Cyberduck / your VPS) |

### 2. Render

- Connect your GitHub account in Render so it can clone the **source repo** you deploy.
- Repos must be buildable with the **build command** and **publish path** you pass.

### 3. Servers

Edit `automation/config/servers.json` — host IP + **per-server Redis key**.

### 4. Enable Actions

Push this repo to GitHub. Workflows:

| Workflow | Purpose |
|----------|---------|
| **Redirect — rotate once** | Manual / UI one-shot |
| **Redirect — save schedule** | Auto intervals + enable |
| **Redirect — auto scheduler** | Cron `*/5 * * * *` |

### 5. Control page (optional)

Host `automation/web/index.html` via **GitHub Pages** (folder `/automation/web` or copy to `docs/`).

- Enter **automation repo** (`owner/oct-front`), **source repo**, PAT with **Actions: write**.
- **One-time** → `redirect-rotate-once.yml`
- **Save schedule** → `redirect-save-schedule.yml` + turn **Auto enabled** on

## Manual CLI (from Mac)

```bash
export RENDER_API_KEY=...
pip install -r automation/scripts/requirements.txt
python automation/scripts/rotate.py --repo owner/my-landing
python automation/scripts/cleanup.py --lifetime-minutes 15
```

Requires SSH agent with your VPS key (`ssh daichisite`, `ssh deanna` working).

## Notes

- **Random names** — `rs-` + 16 hex chars; tracked in `sites-registry.json`.
- **Multiple servers** — one SSH key; different **Redis keys** per row in `servers.json`.
- **First deploy** can take several minutes; script waits for HTTP < 500 on the `.onrender.com` URL.
- Render **free tier limits** apply; cleanup avoids pile-up of old static sites.
