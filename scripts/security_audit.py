"""Audit exactly the files staged for Git without printing credential values."""

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


paths = [part.decode("utf-8") for part in git("ls-files", "--cached", "-z").split(b"\0") if part]
blocked = []
for path in paths:
    lower = path.lower().replace("\\", "/")
    parts = lower.split("/")
    if lower.endswith(".env") or lower.endswith((".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm")):
        blocked.append(path)
    if any(part in {"node_modules", ".venv", "venv", "env", "dist", "build", "__pycache__", ".pytest_cache"} for part in parts):
        blocked.append(path)

env_file = ROOT / "backend" / ".env"
secret = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("AI_API_KEY="):
            secret = line.partition("=")[2].strip().strip('"').strip("'")
            break

patterns = [
    re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(rb"gh[pousr]_[0-9A-Za-z]{20,}"),
    re.compile(rb"github_pat_[0-9A-Za-z_]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
findings = []
for path in paths:
    blob = git("show", f":{path}")
    if secret and len(secret) >= 12 and secret.encode() in blob:
        findings.append(f"{path}: configured API key")
    if any(pattern.search(blob) for pattern in patterns):
        findings.append(f"{path}: credential pattern")

print(f"Staged files scanned: {len(paths)}")
print(f"Disallowed staged paths: {len(blocked)}")
print(f"Credential findings: {len(findings)}")
for item in sorted(set(blocked + findings)):
    print(item)
if blocked or findings:
    raise SystemExit(1)
