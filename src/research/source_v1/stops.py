"""Stop reconciliation: machine-readable historical stop records plus a required named-human attestation.

A record that names URLs yields host-level stops (unclear scope is host-level). A record that names no host
cannot be interpreted by software and stays UNRESOLVED until the attestation resolves it. A snapshot is
COMPLETE only with an attestation that binds exactly its inputs; retrieval refuses anything else. Software
adds stops and never removes them; lifting one is a separate, future owner record. Private stop contents are
never copied: entries carry the input's label and hash only.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit
from src.research.spec import digest
from src.research.quarry_v1 import io as Q
from . import contracts as C, store as S

URL = re.compile(r'https?://[^\s"\'<>\\]+', re.I)
HOST = re.compile(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+|\[?[0-9a-f:.]+\]?')
RULE = 'Unclear scope is host-level. Software adds stops and never removes them.'


def entry(scope, host, route, reason, origin, label, evidence, attested_by=None):
    core = {'scope': scope, 'host': host.lower(), 'route': route, 'reason': reason, 'origin': origin,
            'evidence': {'label': label, 'sha256': evidence}, 'attested_by': attested_by}
    return {'stop_id': 'STP-' + digest(core)[:20], **core}


def hosts_in(value):
    """Hosts of every http(s) URL in any string of a JSON value."""
    found = set()
    if isinstance(value, dict):
        for k, v in value.items():
            found |= hosts_in(k) | hosts_in(v)
    elif isinstance(value, list):
        for v in value:
            found |= hosts_in(v)
    elif isinstance(value, str):
        for url in URL.findall(value):
            try:
                host = (urlsplit(url).hostname or '').lower()
            except ValueError:
                continue
            if HOST.fullmatch(host):
                found.add(host)
    return found


def classify(raw, label, evidence):
    """(kind, entries). kind is QUARRY_REGISTRY, URL_RECORD or UNRESOLVED."""
    try:
        value = C.parse(raw, 'stop record')
    except ValueError:
        return 'UNRESOLVED', []
    if isinstance(value, dict) and value.get('schema') == 'QUARRY_ROUTE_REGISTRY_V001' and isinstance(value.get('routes'), list):
        out = []
        for route in value['routes']:
            if isinstance(route, dict) and route.get('stops'):
                for host in sorted(hosts_in(route.get('locator', ''))):
                    out.append(entry('HOST', host, None, f"Quarry route {route.get('id')} carries a stop; scope unclear, recorded host-level",
                                     'MACHINE_RECORD', label, evidence))
        return 'QUARRY_REGISTRY', out
    hosts = sorted(hosts_in(value))
    if not hosts:
        return 'UNRESOLVED', []
    return 'URL_RECORD', [entry('HOST', h, None, 'A persisted stop record names this host; scope unclear, recorded host-level',
                                'MACHINE_RECORD', label, evidence) for h in hosts]


PATTERN = '*stop*.json'


def scan(directory):
    root = Q.safe_path(directory)
    C.need(root.is_dir(), 'stop directory not found')
    return sorted(p for p in root.rglob(PATTERN) if p.is_file())


def build(inputs=(), base=None, *, attestation=None, previous=None, from_dirs=(), clock=S.now):
    files = [Path(p) for p in inputs]
    dirs = [str(Q.safe_path(d)) for d in from_dirs]
    for directory in dirs:
        files += scan(directory)
    C.need(files or attestation, 'no stop records or attestation supplied')
    entries, records, seen = {}, [], set()
    previous_sha = None
    if previous:
        raw, prior = S.load(previous, 'previous stop snapshot', S.MAX_RECORD)
        C.need(isinstance(prior, dict) and prior.get('schema') == C.SNAPSHOT, 'previous snapshot required')
        previous_sha = S.sha(raw)
        entries.update({e['stop_id']: e for e in prior['entries']})
    for path in files:
        raw = S.read(path)
        evidence = S.sha(raw)
        if evidence in seen:
            continue
        seen.add(evidence)
        kind, found = classify(raw, str(path), evidence)
        records.append({'label': str(path), 'sha256': evidence, 'kind': kind,
                        'resolution': 'UNRESOLVED' if kind == 'UNRESOLVED' else 'MACHINE', 'stops_found': len(found)})
        entries.update({e['stop_id']: e for e in found})
    attestation_sha = attester = None
    if attestation:
        raw, value = S.load(attestation, 'stop attestation')
        C.attestation(value)
        attestation_sha, attester = S.sha(raw), value['attested_by']
        C.need(set(value['inputs']) == {r['sha256'] for r in records}, 'the attestation must bind exactly the snapshot inputs')
        resolutions = {r['input_sha256']: r for r in value['resolutions']}
        C.need(len(resolutions) == len(value['resolutions']) and set(resolutions) <= set(value['inputs']),
               'one resolution per known input')
        for record in records:
            r = resolutions.get(record['sha256'])
            if r is None:
                continue
            record['resolution'] = 'HUMAN_ATTESTED'
            record['task_scoped_reason'] = r['task_scoped_reason']
            for host in r['hosts']:
                e = entry('HOST', host, None, 'Attested host scope of this stop record', 'HUMAN_ATTESTED', record['label'], record['sha256'], attester)
                entries[e['stop_id']] = e
            for route in r['routes']:
                e = entry('ROUTE', C.host_of(route), route, 'Attested route scope of this stop record', 'HUMAN_ATTESTED',
                          record['label'], record['sha256'], attester)
                entries[e['stop_id']] = e
        for d in value['documented_stops']:
            e = entry('ROUTE' if d['route'] else 'HOST', d['host'], d['route'], d['reason'], 'HUMAN_ATTESTED',
                      'documented: ' + d['citation'], attestation_sha, attester)
            entries[e['stop_id']] = e
    unresolved = [r['sha256'] for r in records if r['resolution'] == 'UNRESOLVED']
    snapshot = {'schema': C.SNAPSHOT, 'status': 'COMPLETE' if attestation and not unresolved else 'ATTESTATION_REQUIRED',
                'built_at': clock(), 'sources': {'from_dirs': dirs, 'pattern': PATTERN},
                'inputs': records, 'unresolved_inputs': unresolved, 'attestation_sha256': attestation_sha,
                'attested_by': attester, 'previous_snapshot_sha256': previous_sha,
                'entries': sorted(entries.values(), key=lambda e: e['stop_id']), 'rule': RULE, 'authorises': []}
    path = S.records(base) / 'stops' / 'snapshots' / (digest(snapshot)[:24] + '.json')
    sha = S.write_new(path, snapshot)
    return {'path': str(path), 'sha256': sha, 'status': snapshot['status'], 'entries': len(snapshot['entries']),
            'unresolved_inputs': unresolved, 'authorises': []}


def snapshot(ref):
    """Load a request's snapshot by exact hash; refuse anything but a COMPLETE attested snapshot."""
    raw, value = S.load(ref['path'], 'stop snapshot', S.MAX_RECORD)
    C.need(S.sha(raw) == ref['sha256'], 'STOP_SNAPSHOT_CHANGED: snapshot bytes differ from the request hash')
    C.need(isinstance(value, dict) and value.get('schema') == C.SNAPSHOT and isinstance(value.get('entries'), list), 'stop snapshot required')
    C.need(value.get('status') == 'COMPLETE' and value.get('attestation_sha256') and not value.get('unresolved_inputs'),
           'STOP_ATTESTATION_MISSING: the stop snapshot lacks a complete named-human attestation')
    fresh(value)
    return raw, value


def fresh(value):
    """Software-enforced freshness of the snapshot's own declared inputs at run time.

    Every recorded input must still exist unchanged, and no new stop record may have appeared in a declared
    directory. Stops recorded elsewhere, or known only from reports, rest on the human attestation.
    """
    known = {r['sha256'] for r in value['inputs']}
    for record in value['inputs']:
        path = Path(record['label'])
        C.need(path.is_file() and S.sha(S.read(path)) == record['sha256'],
               f"STOP_SNAPSHOT_STALE: stop record {record['label']} is missing or changed; rebuild and re-attest")
    for directory in value.get('sources', {}).get('from_dirs', []):
        for path in scan(directory):
            C.need(S.sha(S.read(path)) in known, f'STOP_SNAPSHOT_STALE: new stop record {path}; rebuild and re-attest')


def register(base, clock=S.now):
    return S.Journal(S.records(base) / 'stops' / 'register.jsonl', clock)


def findings(base):
    return [e['record'] for e in register(base).load() if e['type'] == 'STOP_FOUND']


def finding(scope, host, route, reason, label, evidence):
    """The deterministic core of a new stop finding: the same evidence always gives the same stop id."""
    return entry(scope, host, route, reason, 'NEW_FINDING', label, evidence)


def record(journal, core, attempt_id, observed_at):
    value = {'schema': C.FINDING, **core, 'observed_at': observed_at, 'attempt_id': attempt_id}
    journal.append('STOP_FOUND', value)
    return value


def ensure(journal, core, attempt_id, clock):
    """Record a finding unless the register already holds that stop id (repeated reconciliation adds nothing)."""
    existing = {f['stop_id']: f for f in [e['record'] for e in journal.load() if e['type'] == 'STOP_FOUND']}
    return existing.get(core['stop_id']) or record(journal, core, attempt_id, clock())


def blocking(url, host, entries):
    host, key = host.lower(), C.dispatch_key(url)
    for e in entries:
        if (e['scope'] == 'HOST' and e['host'] == host) or (e['scope'] == 'ROUTE' and e['route'] and C.dispatch_key(e['route']) == key):
            return e
    return None
