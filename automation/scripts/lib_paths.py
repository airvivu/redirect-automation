from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
SCHEDULE_PATH = ROOT / "schedule.json"
REGISTRY_PATH = ROOT / "sites-registry.json"
SERVERS_PATH = CONFIG_DIR / "servers.json"
