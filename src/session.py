"""Markdown Vault — session state persistence.

Saves and restores the full application state (window geometry, open tabs,
view modes, split positions, sidebar visibility) to a JSON file so that
restarting the app recreates the exact previous session.

Session file: ``~/.config/markdown-vault/session.json``
"""

import json
import logging
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

SESSION_FILE = config.CONFIG_DIR / "session.json"


def save_session(
    width: int,
    height: int,
    sidebar_visible: bool,
    tabs: list[dict],
    active_tab: str | None,
    expanded_vaults: list[str] | None = None,
) -> None:
    """Write the current session state to disk.

    *tabs* is a list of dicts, each with keys:
        ``path``, ``view_mode``, ``split_position``
    *expanded_vaults* lists the vault directory paths that were expanded.
    """
    config._ensure_config_dir()
    data = {
        "window": {"width": width, "height": height},
        "sidebar_visible": sidebar_visible,
        "active_tab": active_tab,
        "tabs": tabs,
        "expanded_vaults": expanded_vaults or [],
    }
    try:
        SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.debug("Session saved to %s", SESSION_FILE)
    except OSError as exc:
        logger.warning("Failed to save session: %s", exc)


def load_session() -> dict:
    """Read the persisted session state, or return sensible defaults."""
    if not SESSION_FILE.exists():
        return _defaults()
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Corrupt session file, using defaults: %s", exc)
        return _defaults()
    data.setdefault("window", {"width": 1200, "height": 800})
    data.setdefault("sidebar_visible", False)
    data.setdefault("active_tab", None)
    data.setdefault("tabs", [])
    data.setdefault("expanded_vaults", [])
    return data


def _defaults() -> dict:
    return {
        "window": {"width": 1200, "height": 800},
        "sidebar_visible": False,
        "active_tab": None,
        "tabs": [],
        "expanded_vaults": [],
    }
