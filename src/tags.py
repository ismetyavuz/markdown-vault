import os
import re
from pathlib import Path


WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def parse_wikilinks(text: str) -> list[tuple[str, str | None]]:
    return [(m.group(1), m.group(2)) for m in WIKILINK_RE.finditer(text)]


def resolve_link(page_name: str, current_file: Path, vault_paths: list[str]) -> Path | None:
    current_dir = current_file.parent
    candidates = [
        current_dir / f"{page_name}.md",
        current_dir / page_name,
    ]
    for vp in vault_paths:
        vault = Path(vp)
        candidates.append(vault / f"{page_name}.md")
        candidates.append(vault / page_name)
    for c in candidates:
        if c.exists() and c.suffix == ".md":
            return c
    return None


def find_backlinks(target_file: Path, vault_paths: list[str]) -> list[Path]:
    backlinks = []
    target_stem = target_file.stem
    for vp in vault_paths:
        for root, _dirs, files in os.walk(vp):
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = Path(root) / fname
                if fpath == target_file:
                    continue
                try:
                    text = fpath.read_text(encoding="utf-8")
                except Exception:
                    continue
                links = parse_wikilinks(text)
                for page, _alias in links:
                    if page == target_stem:
                        backlinks.append(fpath)
                        break
    return backlinks
