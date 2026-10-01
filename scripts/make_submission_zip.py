#!/usr/bin/env python3
"""Create a clean submission ZIP without local secrets or bulky runtime files."""
from __future__ import annotations

import fnmatch
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'dist'
OUT_DIR.mkdir(exist_ok=True)
ZIP = OUT_DIR / 'zelfstandige-zorgagent-inleverpakket.zip'

EXCLUDE_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'dist', 'data',
}
EXCLUDE_FILES = {
    '.env',
    'identity.db',
    'actual-workflow.json',
}
EXCLUDE_PATTERNS = [
    '*.pyc', '*.pyo', '*.zip', '*.log', '*.secret', '*identity*.sqlite', '*identity*.db',
]

def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return True
    if path.name in EXCLUDE_FILES:
        return True
    rel_text = rel.as_posix()
    return any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel_text, pattern) for pattern in EXCLUDE_PATTERNS)

with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('PAKKET-GEGENEREERD.txt',
                'Gegenereerd op ' + datetime.now(timezone.utc).isoformat() + '\n'
                'Uitgesloten: .env, credentials, lokale data/, identity-databases, caches, virtuele omgevingen, node_modules en oude zipbestanden.\n')
    for path in sorted(ROOT.rglob('*')):
        if path.is_dir() or excluded(path):
            continue
        zf.write(path, path.relative_to(ROOT).as_posix())

print(ZIP)
