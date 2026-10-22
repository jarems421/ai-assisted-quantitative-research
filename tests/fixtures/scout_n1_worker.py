"""Fixed local reservation/crash worker for process assurance, never a model."""
import json
import os
from pathlib import Path
import sys

from src.research.opportunity_scout.n1_collector.collector import _collect_fixture


binding, approval = json.loads(Path(sys.argv[1]).read_bytes())
payload = Path(sys.argv[2]).read_bytes()
sys.stdin.buffer.read(1)  # Parent releases racing workers together.
try:
    crash = (lambda: os._exit(42)) if sys.argv[3] == 'crash-after-raw' else None
    result = _collect_fixture(binding, approval, payload, after_raw=crash)
    print(result['status'])
except (ValueError, OSError):
    raise SystemExit(2)
