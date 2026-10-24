"""Bounded explicit local files and create-only writes. No ambient source discovery."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from src.research.spec import canonical
from src.research.jev_navigation_v1.contracts import loads, need

ROOT = Path(__file__).resolve().parents[3]
MAX_FILE = 16 * 1024 * 1024
BLOCKED = {'.git', '.ssh', '.aws', '.azure', '.codex', '.claude', '.config', '.netrc', 'keys'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(value):
    path = Path(value).absolute()
    need(not str(value).startswith(('\\\\', '//')), 'network filesystem paths refused')
    for part in (path, *path.parents):
        need(part.name.lower() not in BLOCKED and not part.name.lower().startswith(('.env', '.claude.')), 'credential/internal path refused')
        need(not part.is_symlink() and not part.is_junction(), 'linked paths refused')
    return path.resolve()


def read(path, maximum=MAX_FILE):
    path = safe_path(path)
    need(path.is_file(), 'explicit regular local file required')
    with path.open('rb') as handle:
        before = os.fstat(handle.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, 'bounded regular file required')
        raw = handle.read(maximum + 1)
        after = os.fstat(handle.fileno())
    need(len(raw) <= maximum and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'oversize or changed source')
    return raw


def child(root, name):
    base = safe_path(root)
    need(isinstance(name, str) and '\\' not in name and ':' not in name, 'portable relative path required')
    relative = Path(name)
    need(not relative.is_absolute() and '..' not in relative.parts, 'path escape refused')
    path = safe_path(base / relative)
    need(path.is_relative_to(base), 'path escape refused')
    return path


def new_directory(out, prefix='quarry-v1-'):
    target = safe_path(out)
    need(not target.exists(), 'create-only directory already exists')
    if target.is_relative_to(ROOT):
        parts = target.relative_to(ROOT).parts
        need(len(parts) >= 2 and parts[0] == '.research' and parts[1].startswith(prefix), 'use ignored .research/' + prefix + '*')
    else:
        need(not any((p / '.git').exists() for p in target.parents), 'another Git checkout refused')
    target.mkdir(parents=True, exist_ok=False)
    return target


def write(path, value, *, raw=False):
    path = safe_path(path)
    with path.open('xb') as handle:
        handle.write(value if raw else canonical(value))
        handle.flush()
        os.fsync(handle.fileno())


def json_file(path):
    return loads(read(path, 1024 * 1024))


def seal(root, names, schema):
    manifest = {'schema': schema, 'files': {n: sha(read(child(root, n))) for n in sorted(names)}, 'authorises': []}
    write(Path(root) / 'manifest.json', manifest)
    return manifest


def verify_seal(root, schema):
    manifest = json_file(child(root, 'manifest.json'))
    need(isinstance(manifest, dict) and set(manifest) == {'schema', 'files', 'authorises'} and manifest['schema'] == schema and manifest['authorises'] == [], 'invalid manifest')
    need(isinstance(manifest['files'], dict) and manifest['files'], 'empty manifest')
    for name, expected in manifest['files'].items():
        need(sha(read(child(root, name))) == expected, 'TAMPERED: ' + name)
    return manifest
