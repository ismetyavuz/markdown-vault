import os
from pathlib import Path

import yaml


CONFIG_DIR = Path.home() / ".config" / "markdown-vault"
CONFIG_FILE = CONFIG_DIR / "vaults.yaml"


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_vaults() -> list[dict]:
    if not CONFIG_FILE.exists():
        return []
    with open(CONFIG_FILE, "r") as f:
        data = yaml.safe_load(f) or {}
    vaults = data.get("vaults", [])
    seen = set()
    unique = []
    for v in vaults:
        path = os.path.abspath(v.get("path", ""))
        if path and path not in seen:
            seen.add(path)
            unique.append({"name": v.get("name", Path(path).name), "path": path})
    return unique


def save_vaults(vaults: list[dict]):
    _ensure_config_dir()
    seen = set()
    unique = []
    for v in vaults:
        path = os.path.abspath(v["path"])
        if path not in seen:
            seen.add(path)
            unique.append({"name": v.get("name", Path(path).name), "path": path})
    data = {"vaults": unique}
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def add_vault(name: str, path: str) -> list[dict]:
    vaults = load_vaults()
    vaults.append({"name": name, "path": os.path.abspath(path)})
    save_vaults(vaults)
    return vaults


def remove_vault(path: str) -> list[dict]:
    abs_path = os.path.abspath(path)
    vaults = [v for v in load_vaults() if v["path"] != abs_path]
    save_vaults(vaults)
    return vaults
