"""Review supplied fictional per-probe monitoring; no account/process collection."""
from pathlib import Path

from . import schema as S, v004_monitoring as M

VERSION = 'SCOUT_V004_QUIET_WINDOW_R1'


def review(window, *, session_id=None, previous_window_end=None):
    faults = []
    begin, end = S.UNKNOWN, S.UNKNOWN
    try:
        if window['schema'] != VERSION: raise S.ScoutError('wrong monitoring schema')
        samples, processes, phases = window['samples'], window['process_samples'], window['phases']
        if len(samples) != len(phases) or len(samples) != len(processes): raise S.ScoutError('unaligned observations')
        times = [S.timestamp(s['sampled_at']) for s in samples]
        begin, end = samples[0]['sampled_at'], samples[-1]['sampled_at']
        if session_id is not None and window.get('session_id') != session_id:
            faults.append('MONITORING_SESSION_MISMATCH')
        if previous_window_end is not None and times[0] <= S.timestamp(previous_window_end):
            faults.append('REUSED_OR_OVERLAPPING_MONITORING_WINDOW')
        for sample in samples:
            for row in sample['files'].values():
                if row.get('state') == 'REGULAR_FILE':
                    keys = {'size', 'mtime_ns', 'ctime_ns', 'file_id', 'device'}
                    if set(row) != keys | {'state'} or any(not isinstance(row.get(k), int) or isinstance(row.get(k), bool) or row[k] < 0 for k in keys):
                        faults.append('FILE_METADATA_INCOMPLETE')
                elif row != {'state': 'ABSENT'}: faults.append('FILE_METADATA_UNOBSERVABLE')
        if any(not 0 < (b - a).total_seconds() <= 5 for a, b in zip(times, times[1:])):
            faults.append('MONITORING_GAP_OR_REORDERING')
        indices = [phases.index(p) for p in ('baseline', 'active', 'cooldown')]
        if phases != sorted(phases, key=('baseline', 'active', 'cooldown').index):
            faults.append('MONITORING_PHASE_ORDER')
        for phase in ('baseline', 'cooldown'):
            ts = [t for t, p in zip(times, phases) if p == phase]
            if not ts or (ts[-1] - ts[0]).total_seconds() < 60: faults.append('QUIET_DURATION_INSUFFICIENT')
        if indices[0] != 0 or phases[-1] != 'cooldown': faults.append('IDLE_WINDOW_MISSING')
        probe = window['probe']
        if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in (probe['parent_pid'], window['parent_pid'])):
            faults.append('PROBE_PARENT_UNKNOWN_OR_CHANGED')
        if set(probe) != {'pid', 'started_at', 'parent_pid'} or probe['parent_pid'] != window['parent_pid']:
            faults.append('PROBE_PARENT_UNKNOWN_OR_CHANGED')
        S.timestamp(probe['started_at'])
        if not times[0] <= S.timestamp(probe['started_at']) <= times[indices[1]]:
            faults.append('PROBE_CREATION_OUTSIDE_WINDOW')
        if not any(probe in row['processes'] for row, phase in zip(processes, phases) if phase == 'active'):
            faults.append('ACTIVE_PROBE_NOT_OBSERVED')
        filtered = []
        for i, row in enumerate(processes):
            if S.timestamp(row['sampled_at']) != times[i]: faults.append('PROCESS_SAMPLE_TIME_MISMATCH')
            filtered_rows = []
            for p in row['processes']:
                if set(p) != {'pid', 'started_at', 'parent_pid'}: raise S.ScoutError('unexpected process fields')
                if p['pid'] == probe['pid'] and p['started_at'] == probe['started_at'] and p['parent_pid'] != probe['parent_pid']:
                    faults.append('PROBE_PARENT_UNKNOWN_OR_CHANGED')
                filtered_rows.append({k: p[k] for k in ('pid', 'started_at')})
            filtered.append({'observable': row['observable'], 'processes': filtered_rows})
        observed = M.quiet_window_review(samples, filtered,
                    allowed_probe={k: probe[k] for k in ('pid', 'started_at')})
        faults.extend(observed['flags'])
        for i, phase in enumerate(phases):
            if phase != 'active' and processes[i]['processes']: faults.append('PROCESS_IN_IDLE_PHASE')
        # Baseline comparisons also prevent a changed file being blessed after
        # the probe exits and a new adjacent baseline is silently substituted.
        if any(not M.compare_metadata(samples[0], s)['unchanged_observed_metadata'] for s in samples[1:]):
            faults.append('ORIGINAL_BASELINE_DRIFT')
        expected = str(Path(window['home']).absolute() / '.claude-research')
        if (window['requested_config_dir'] != expected or window['observed_config_dir'] != expected
                or window['account_source'] != 'subscription' or window['config_observation'] != 'RECORDED_FICTIONAL'):
            faults.append('RESEARCH_CONFIGURATION_NOT_ESTABLISHED')
    except (KeyError, ValueError, TypeError, AttributeError, IndexError):
        faults.append('MONITORING_UNKNOWN_OR_MALFORMED')
    return {'schema': VERSION, 'faults': sorted(set(faults)), 'sampled_window_clean': not faults,
            'window_begin': begin, 'window_end': end,
            'historical_writer': S.UNKNOWN, 'credential_leakage': 'NOT_ESTABLISHED',
            'content_noninterference_proven': False, 'hosted_authorised': False}
