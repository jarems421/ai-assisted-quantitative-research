"""Offline metadata-only review helpers; no Claude, network or credential IO.

These helpers observe changes and reject contaminated monitoring windows. They
cannot attribute a writer, prove content equality, or authorise a hosted probe.
"""
from __future__ import annotations

from pathlib import Path
import stat

from . import schema as S
from .storage import unlinked

ACCOUNT_PATHS = (
    '.claude.json', '.claude/settings.json', '.claude/.credentials.json',
    '.claude-research.json', '.claude-research/.claude.json',
    '.claude-research/settings.json', '.claude-research/.credentials.json',
)


def account_metadata(home=None):
    """Only lstat: do not open, copy, hash or decode any account file."""
    root = Path.home() if home is None else Path(home)
    rows = {}
    for name in ACCOUNT_PATHS:
        path = root / name
        try:
            unlinked(path)
            value = path.lstat()
            rows[name] = {'state': 'REGULAR_FILE' if stat.S_ISREG(value.st_mode) else 'UNSUPPORTED_TYPE',
                          'size': value.st_size, 'mtime_ns': value.st_mtime_ns,
                          'ctime_ns': value.st_ctime_ns, 'file_id': value.st_ino, 'device': value.st_dev}
        except FileNotFoundError: rows[name] = {'state': 'ABSENT'}
        except (OSError, S.ScoutError): rows[name] = {'state': 'UNOBSERVABLE'}
    return {'schema': 'SCOUT_ACCOUNT_METADATA_V004_REVIEW', 'sampled_at': S.utc_now(), 'files': rows,
            'credential_contents_accessed': False, 'probe_authorised': False}


def compare_metadata(before, after):
    """A difference is a guard failure, never evidence of credential leakage."""
    expected = set(ACCOUNT_PATHS)
    if set(before.get('files', {})) != expected or set(after.get('files', {})) != expected:
        raise S.ScoutError('metadata samples must cover the full fixed account path set')
    if S.timestamp(before['sampled_at']) > S.timestamp(after['sampled_at']):
        raise S.ScoutError('metadata sample times are reversed')
    unknown = sorted(name for name in expected if before['files'][name]['state'] not in ('REGULAR_FILE', 'ABSENT')
                     or after['files'][name]['state'] not in ('REGULAR_FILE', 'ABSENT'))
    changed = sorted(name for name in expected if before['files'][name] != after['files'][name])
    return {'unchanged_observed_metadata': not changed and not unknown,
            'changed_paths': changed, 'unobservable_paths': unknown,
            'writer_attribution': S.UNKNOWN, 'content_equality': S.UNKNOWN,
            'credential_leakage': 'NOT_ESTABLISHED', 'probe_authorised': False}


def quiet_window_review(samples, process_samples, *, allowed_probe=None):
    """Review already-collected samples, without starting/stopping any process.

    process_samples rows are supplied metadata only: observable (bool), processes
    [{pid, started_at}]. Never collect command lines, environments or tokens.
    allowed_probe is the one parent-recorded {pid, started_at}, if a future probe
    has separate authority. Empty process data is not proof of a quiet window.
    """
    if len(samples) < 3 or len(samples) != len(process_samples):
        raise S.ScoutError('quiet-window review needs aligned before/during/after metadata and process samples')
    changes = [compare_metadata(a, b) for a, b in zip(samples, samples[1:])]
    unexpected, process_unknown = [], False
    probe_outside_active_sample = False
    for index, sample in enumerate(process_samples):
        if sample.get('observable') is not True or not isinstance(sample.get('processes'), list):
            process_unknown = True; continue
        for process in sample['processes']:
            if (not isinstance(process, dict) or set(process) != {'pid', 'started_at'}
                    or not isinstance(process['pid'], int) or isinstance(process['pid'], bool) or process['pid'] <= 0):
                raise S.ScoutError('process metadata is limited to positive PID and creation time')
            S.timestamp(process['started_at'])
            if process != allowed_probe: unexpected.append(process)
            elif index in (0, len(process_samples) - 1): probe_outside_active_sample = True
    flags = []
    if any(not c['unchanged_observed_metadata'] for c in changes): flags.append('ACCOUNT_METADATA_GUARD_FAILED')
    if process_unknown: flags.append('PROCESS_OBSERVABILITY_UNKNOWN')
    if unexpected: flags.append('CONCURRENT_OR_UNEXPECTED_CLAUDE_PROCESS')
    if probe_outside_active_sample: flags.append('PROBE_OUTSIDE_ACTIVE_SAMPLE')
    return {'window_observationally_clean': not flags, 'flags': flags,
            'comparisons': changes, 'unexpected_process_observations': len(unexpected),
            'writer_attribution': S.UNKNOWN, 'content_noninterference_proven': False,
            'monitoring_blind_spots': 'Changes and transient processes between samples may be missed.',
            'probe_authorised': False}
