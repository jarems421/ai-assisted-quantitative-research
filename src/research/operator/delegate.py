"""Call existing Research OS command lines in-process, exactly as documented, under the operator boundary.

Each call runs the component's own ``main(argv)``, so validation, refusals and error strings stay the component's.
Only listed read-only or create-only commands are callable; anything that records a human act, imports a model reply,
dispatches a provider, runs a pipeline or acquires a source is refused here before the component is imported."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
import time

from .guard import BoundaryViolation

ENTRY = {'src.research.opportunity_scout': ('src.research.opportunity_scout.cli', {'validate', 'list', 'card', 'handoff'}),
         'src.research.opportunity_scout.critic_v1': ('src.research.opportunity_scout.critic_v1.cli', {'status'}),
         'src.research.opportunity_scout.automation_v001': ('src.research.opportunity_scout.automation_v001.__main__', {'status', 'report'}),
         'src.research.quarry_v1': ('src.research.quarry_v1.__main__', {'import-file', 'status', 'export', 'validate-export'}),
         'src.research.jev_navigation_v1': ('src.research.jev_navigation_v1.__main__', {'prepare', 'report'}),
         'src.research.jev_navigation_integration_v1': ('src.research.jev_navigation_integration_v1.__main__', {'compose-quarry'}),
         'src.research.discovery': ('src.research.discovery.cli', {'validate', 'checklist', 'source', 'init', 'add'}),
         'src.research.graph': ('src.research.graph.cli', {'same-gap', 'search', 'trace', 'failures'})}
STDERR_LIMIT = 4000


class NotPermitted(ValueError):
    pass


def shell(module, argv):
    """The equivalent command for manual debugging (PowerShell or POSIX quoting of spaces)."""
    quote = lambda x: f'"{x}"' if any(c in x for c in ' \t;&|') else x
    return ' '.join(['python', '-m', module, *map(quote, map(str, argv))])


def call(module, argv):
    if module not in ENTRY or not argv or argv[0] not in ENTRY[module][1]:
        raise NotPermitted(f'not an operator-permitted command: {module} {argv[:1]}')
    argv = [str(x) for x in argv]
    out, err, started = io.StringIO(), io.StringIO(), time.perf_counter()
    fault = None
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = importlib.import_module(ENTRY[module][0]).main(argv)
            except SystemExit as stop:  # argparse, Discovery refusals
                code = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 2)
                if isinstance(stop.code, str):
                    err.write(stop.code)
    except BoundaryViolation:
        raise
    except Exception as error:  # a component crash is a software finding, never a research result
        code, fault = None, f'{type(error).__name__}: {error}'
    text = out.getvalue()
    try:
        parsed = json.loads(text) if text.strip() else None
    except ValueError:
        parsed = None
    return {'command': shell(module, argv), 'module': module, 'argv': argv, 'exit_code': 0 if code is None and fault is None else code,
            'fault': fault, 'stdout_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'stdout_chars': len(text),
            'json': parsed, 'text': None if parsed is not None else text[:STDERR_LIMIT],
            'stderr': err.getvalue()[:STDERR_LIMIT], 'elapsed_seconds': round(time.perf_counter() - started, 3)}


def ok(result):
    return result['fault'] is None and result['exit_code'] == 0


def refusal(result):
    """The component's own refusal text: stderr first, then a JSON status/reason/error body."""
    body = result['json'] if isinstance(result['json'], dict) else {}
    return (result['stderr'].strip() or body.get('reason') or body.get('error') or result['fault'] or 'UNKNOWN').strip()
