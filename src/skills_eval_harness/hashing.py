"""Canonical hashing and atomic artifact helpers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

EXCLUDED_NAMES = {".git", "__pycache__", ".DS_Store"}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()

def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def sha256_tree(root: Path) -> str:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    digest = hashlib.sha256()
    files = sorted(p for p in root.rglob("*") if p.is_file() and not EXCLUDED_NAMES.intersection(p.relative_to(root).parts))
    for path in files:
        relative = path.relative_to(root).as_posix().encode()
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()

def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)

def atomic_write_json(path: Path, value: object) -> None:
    atomic_write(path, canonical_json(value))

tree_sha256 = sha256_tree
