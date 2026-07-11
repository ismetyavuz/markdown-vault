import subprocess
from pathlib import Path


def _run_git(args: list[str], cwd: str | Path) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "git not found"
    except subprocess.TimeoutExpired:
        return -1, "", "git timed out"


def is_git_repo(path: str | Path) -> bool:
    code, _, _ = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0


def get_status(path: str | Path) -> list[dict]:
    code, stdout, _ = _run_git(["status", "--porcelain"], cwd=path)
    if code != 0:
        return []
    entries = []
    for line in stdout.strip().splitlines():
        if len(line) >= 3:
            status_code = line[:2].strip()
            filepath = line[3:]
            entries.append({"status": status_code, "path": filepath})
    return entries


def get_diff(path: str | Path, filepath: str | None = None) -> str:
    args = ["diff"]
    if filepath:
        args.extend(["--", filepath])
    code, stdout, _ = _run_git(args, cwd=path)
    return stdout if code == 0 else ""


def get_log(path: str | Path, max_count: int = 20) -> list[dict]:
    code, stdout, _ = _run_git(
        ["log", f"--max-count={max_count}", "--format=%H|%s|%an|%ai"],
        cwd=path,
    )
    if code != 0:
        return []
    entries = []
    for line in stdout.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            entries.append({
                "hash": parts[0],
                "message": parts[1],
                "author": parts[2],
                "date": parts[3],
            })
    return entries


def commit(path: str | Path, message: str) -> tuple[bool, str]:
    code, stdout, stderr = _run_git(["commit", "-m", message], cwd=path)
    return code == 0, stderr or stdout


def stage_and_commit(path: str | Path, files: list[str], message: str) -> tuple[bool, str]:
    for f in files:
        code, _, err = _run_git(["add", f], cwd=path)
        if code != 0:
            return False, err
    return commit(path, message)
