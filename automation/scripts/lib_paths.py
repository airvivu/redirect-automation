from pathlib import Path

# automation/scripts/this_file.py -> automation/
AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = AUTOMATION_ROOT / "config"
SCHEDULE_PATH = AUTOMATION_ROOT / "schedule.json"
REGISTRY_PATH = AUTOMATION_ROOT / "sites-registry.json"
SERVERS_PATH = CONFIG_DIR / "servers.json"
