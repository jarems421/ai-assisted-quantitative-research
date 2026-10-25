"""Frozen exact payloads, owner gates, one claimed attempt and re-derived reporting."""
from __future__ import annotations

import http.client
import os
from datetime import datetime, timezone
from pathlib import Path
from src.research.spec import canonical, digest
from src.research.jev_navigation_v1 import contracts as K, navigation as N, workspace as W
from src.research.quarry_v1 import io
from . import quarry as Q
from . import provider as P

PLAN = 'JEV_PROVIDER_PLAN_V001'
CLASSIFICATIONS = ['SYNTHETIC', 'PUBLIC_REPOSITORY', 'LOCAL_PRIVATE']
APPROVAL = K.obj({'schema': {'const': 'JEV_PROVIDER_OWNER_APPROVAL_V001'}, 'fixture': {'enum': ['SYNTHETIC', 'LIVE']},
                  'owner': K.TEXT, 'approved_at': K.TEXT, 'expires_at': K.TEXT,
                  'plan_sha256': K.HASH, 'payload_sha256': K.HASH,
                  'allowed_data_classification': {'enum': CLASSIFICATIONS}, 'disclosure_approved': {'const': True},
                  'request_ceiling': {'const': 1}, 'spend_ceiling_micro_usd': {'type': 'integer', 'minimum': P.RESERVATION_MICRO_USD},
                  'account_context': K.TEXT, 'account_evidence_sha256': K.HASH,
                  'availability_model': {'enum': list(P.MODELS)}, 'availability_basis': {'const': 'ACCOUNT_SPECIFIC_VERSION_CONFIRMATION'},
                  'account_evidence_verified_at': K.TEXT, 'independent_billing_hard_limit_confirmed': {'const': True},
                  'remaining_account_hard_limit_micro_usd': {'type': 'integer', 'minimum': P.RESERVATION_MICRO_USD},
                  'price_usd_per_billion_input_tokens': {'const': 42}, 'output_tokens_free_confirmed': {'const': True},
                  'audit_root': K.TEXT})


def policy_hash():
    base = Path(__file__).parent
    files = sorted(base.glob('*.py')) + sorted((io.ROOT / 'src/research/quarry_v1').glob('*.py'))
    files.append(io.ROOT / 'docs/jev_navigation_provider_v001/typesafe_contract_v001.json')
    return digest({p.relative_to(io.ROOT).as_posix(): io.sha(io.read(p).replace(b'\r\n', b'\n')) for p in files})


def make_plan(navigation_workspace, target, model, quarry_export=None):
    K.need(model in P.MODELS, 'reviewed exact version required; aliases and substitution refused')
    nav, bundle = W.load(navigation_workspace)
    K.need(not (nav / 'response.raw').exists(), 'use a fresh navigation request; historical responses are unchanged')
    quarry = None
    if quarry_export is not None:
        checked = Q.validate(quarry_export)
        K.need(checked['bundle'] == bundle, 'Quarry export must be the exact navigation input')
        quarry = {'path': str(io.safe_path(quarry_export)), 'manifest_sha256': digest(checked['manifest'])}
    request = bundle['request']
    payload = {'model': model,
               'state': {'task': request['task'], 'subject': request['subject'], 'records': request['records'],
                         'deterministic': request['deterministic'], 'authorises': []}, 'questions': request['questions']}
    raw = canonical(payload)
    K.need(len(raw) <= 64 * 1024, 'payload exceeds conservative 64-KiB adapter bound; choose fewer passages')
    plan = {'schema': PLAN, 'workspace': str(io.safe_path(target)), 'navigation_workspace': str(nav),
            'navigation_bundle_sha256': digest(bundle), 'quarry': quarry, 'model': model,
            'data_classification': request['data_classification'], 'payload_sha256': io.sha(raw),
            'payload_bytes': len(raw), 'policy_sha256': policy_hash(), 'endpoint': 'https://' + P.HOST + P.PATH,
            'request_ceiling': 1, 'reserved_micro_usd': P.RESERVATION_MICRO_USD, 'actual_cost': 'UNKNOWN',
            'provider_request_binding': 'LOCAL_CAPTURE_ONLY_NOT_PROVIDER_AUTHENTICATED',
            'transport_limits': {'socket_inactivity_seconds': P.SOCKET_INACTIVITY_SECONDS,
                                 'strict_total_wall_deadline': 'NOT_ENFORCED',
                                 'response_byte_ceiling': P.MAX_RESPONSE, 'overflow_marker_bytes': 1},
            'enabled_by_default': False, 'authorises': []}
    return plan, raw, bundle


def prepare(navigation_workspace, out, *, model, quarry_export=None):
    plan, payload, _ = make_plan(navigation_workspace, out, model, quarry_export)
    target = io.new_directory(out, prefix='jev-provider-v1-')
    io.write(target / 'plan.json', plan)
    io.write(target / 'payload.bin', payload, raw=True)
    return {'plan_sha256': digest(plan), 'payload_sha256': plan['payload_sha256'], 'enabled': False, 'authorises': []}


def load(workspace):
    root = io.safe_path(workspace)
    plan = io.json_file(root / 'plan.json')
    expected, raw, bundle = make_plan(plan['navigation_workspace'], root, plan['model'], plan['quarry']['path'] if plan['quarry'] else None)
    K.need(plan == expected and io.read(root / 'payload.bin') == raw, 'stale/altered plan, payload, code, source version or Quarry package')
    return root, plan, raw, bundle


def instant(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    K.need(dt.tzinfo is not None, 'timezone required')
    return dt.astimezone(timezone.utc)


def approval_for(plan, path, account_evidence_path, *, synthetic):
    approval = io.json_file(path)
    K.validate(APPROVAL, approval)
    K.need((approval['fixture'] == 'SYNTHETIC') == synthetic, 'synthetic approval cannot activate live transport')
    K.need(not synthetic or plan['data_classification'] == 'SYNTHETIC', 'injected transports are synthetic-evidence fixtures only')
    K.need(approval['owner'].strip().upper() not in ('UNKNOWN', 'PENDING', 'TBD', 'CODEX', 'CHATGPT', 'ASSISTANT', 'AI'), 'named human owner required')
    K.need(approval['plan_sha256'] == digest(plan) and approval['payload_sha256'] == plan['payload_sha256'], 'exact plan/payload owner authorisation required')
    K.need(approval['allowed_data_classification'] == plan['data_classification'], 'data classification/disclosure not authorised')
    K.need(approval['availability_model'] == plan['model'], 'pinned model lacks account-specific availability verification')
    now = datetime.now(timezone.utc)
    K.need(instant(approval['approved_at']) <= now < instant(approval['expires_at']), 'owner authorisation outside approved time window')
    K.need(instant(approval['account_evidence_verified_at']) <= instant(approval['approved_at']) <= now
           and (now - instant(approval['account_evidence_verified_at'])).total_seconds() <= 86400, 'fresh account-specific verification required at activation')
    K.need(type(approval['request_ceiling']) is int and type(approval['spend_ceiling_micro_usd']) is int
           and type(approval['remaining_account_hard_limit_micro_usd']) is int
           and approval['remaining_account_hard_limit_micro_usd'] <= approval['spend_ceiling_micro_usd'], 'owner spend ceiling/hard account cap mismatch')
    raw = io.read(account_evidence_path, 1024 * 1024)
    K.need(io.sha(raw) == approval['account_evidence_sha256'], 'independently obtained account/version/pricing/hard-limit evidence changed')
    audit = io.safe_path(approval['audit_root'])
    K.need(audit.is_dir() and not audit.is_relative_to(Path(plan['workspace']))
           and (audit.is_relative_to(io.ROOT / '.research') or not any((p / '.git').exists() for p in (audit, *audit.parents))), 'owner-managed private audit directory required')
    return approval, raw, audit


def dispatch(workspace, approval_path, account_evidence_path, *, enabled=False, credential_env='TYPESAFE_API_KEY', fixture_transport=None):
    # No credentials, account evidence, DNS or HTTP are inspected unless explicitly enabled.
    K.need(enabled is True, 'PROVIDER_DISABLED: separate exact owner activation required')
    root, plan, payload, bundle = load(workspace)
    synthetic = fixture_transport is not None
    approval, evidence, audit = approval_for(plan, approval_path, account_evidence_path, synthetic=synthetic)
    if not synthetic:
        require_live_evaluation(root, plan, bundle)
    K.need(not (root / 'attempt.json').exists(), 'attempt already claimed; never retry/resume')
    # A plan has one durable claim in the independently supplied audit root as well as its workspace.
    claim = {'schema': 'JEV_PROVIDER_ATTEMPT_V001', 'plan_sha256': digest(plan), 'approval_sha256': digest(approval),
             'fixture': approval['fixture'], 'reserved_micro_usd': plan['reserved_micro_usd'], 'actual_cost': 'UNKNOWN',
             'evaluation_sha256': io.sha(io.read(root / 'evaluation.json')) if (root / 'evaluation.json').exists() else None,
             'claimed_at_utc': datetime.now(timezone.utc).isoformat(), 'authorises': []}
    io.write(audit / (digest(plan) + '.json'), claim)
    io.write(root / 'attempt.json', claim)
    io.write(root / 'approval.json', approval)
    io.write(root / 'account-evidence.bin', evidence, raw=True)
    status, fault, response_status, count = 'INTERRUPTED_OR_UNKNOWN', None, None, 0
    result = P.metadata(None)
    with (root / 'response.raw').open('xb') as handle:
        def emit(chunk):
            nonlocal count
            K.need(isinstance(chunk, bytes), 'raw bytes required')
            remaining = P.MAX_RESPONSE + 1 - count
            kept = chunk[:max(0, remaining)]
            handle.write(kept); handle.flush(); os.fsync(handle.fileno())
            count += len(kept)
            K.need(count <= P.MAX_RESPONSE, 'RESPONSE_OVERSIZE')
        try:
            if synthetic:
                key = 'SYNTHETIC_NO_CREDENTIAL'
            else:
                K.need(credential_env == 'TYPESAFE_API_KEY', 'only explicitly named provider environment credential supported')
                key = os.environ.get(credential_env)
                K.need(isinstance(key, str) and key and '\r' not in key and '\n' not in key, 'provider credential unavailable')
            io.write(root / 'dispatch-started.json', {'fixture': approval['fixture'], 'authorises': []})
            transport = fixture_transport if synthetic else P.capture
            response_status = transport(payload, key, emit)
            K.need(type(response_status) is int, 'HTTP status required')
            status = 'RAW_CAPTURED'
        except (http.client.HTTPException, OSError, ValueError, TypeError) as error:
            # Never persist exception text: transport exceptions can include account data.
            fault = type(error).__name__
            status = 'TRANSPORT_FAILED' if not isinstance(error, (ValueError, TypeError)) else 'REFUSED_OR_OVERSIZE'
    raw = io.read(root / 'response.raw', P.MAX_RESPONSE + 1)
    if status == 'RAW_CAPTURED':
        if response_status != 200:
            status = 'HTTP_FAILED'
        else:
            try:
                response = K.loads(raw)
                result = P.metadata(response)
                P.answers(bundle['request'], response, plan['model'])
                status = 'SYNTHETIC_VALID' if synthetic else 'PROVIDER_VALID'
            except (ValueError, TypeError, KeyError) as error:
                status, fault = 'INVALID_RESPONSE', type(error).__name__
    record = {'schema': 'JEV_PROVIDER_RESULT_V001', 'status': status, 'fault_type': fault, 'http_status': response_status,
              'fixture': approval['fixture'], 'plan_sha256': digest(plan), 'payload_sha256': plan['payload_sha256'],
              'raw_sha256': io.sha(raw), 'raw_bytes': len(raw), 'model_requested': plan['model'],
              'model_returned': result['model_returned'], 'usage': result['usage'], 'actual_cost': 'UNKNOWN',
              'metadata_faults': result['metadata_faults'], 'runtime_identity': result['runtime_identity'],
              'reserved_micro_usd': plan['reserved_micro_usd'], 'reservation_released': False,
              'provider_request_binding': plan['provider_request_binding'], 'authorises': []}
    io.write(root / 'result.json', record)
    io.write(root / 'completion.json', {'result_sha256': digest(record), 'raw_sha256': io.sha(raw),
                                       'claim_sha256': digest(claim), 'authorises': []})
    return record


def require_live_evaluation(root, plan, bundle):
    """Live navigation requires a prospectively frozen independently labelled evaluation.

    This verifies registration consistency, never the truth of human independence.
    Labels and the independent assembly record remain opaque, outside the payload.
    """
    from .evaluation import REGISTRATION
    K.need((root / 'evaluation.json').is_file(), 'LIVE_EVALUATION_REQUIRED: freeze independently labelled holdout before activation')
    frozen = io.json_file(root / 'evaluation.json')
    registration = frozen['registration']
    K.validate(REGISTRATION, registration)
    K.need(registration['fixture'] == 'INDEPENDENT_HUMAN_HOLDOUT', 'synthetic evaluation cannot activate live navigation')
    K.need(frozen['plan_sha256'] == digest(plan) and frozen['request_sha256'] == bundle['request_sha256']
           and frozen['record_ids'] == sorted(r['id'] for r in bundle['request']['records']), 'live evaluation does not bind exact request/universe')
    K.need(set(registration['additional_baseline_order']) == set(frozen['record_ids'])
           and all(type(b) is int and b <= len(frozen['record_ids']) for b in registration['inspection_budgets']), 'live evaluation baseline/budget mismatch')


def report(workspace):
    root, plan, _, bundle = load(workspace)
    answer_map, raw_hash, record = None, None, None
    attempted = (root / 'attempt.json').exists()
    claim = io.json_file(root / 'attempt.json') if attempted else None
    state = 'NOT_DISPATCHED'
    if attempted:
        state = 'INTERRUPTED_OR_UNKNOWN'
        if (root / 'completion.json').exists():
            record = io.json_file(root / 'result.json')
            completion = io.json_file(root / 'completion.json')
            K.need(completion == {'result_sha256': digest(record), 'raw_sha256': record['raw_sha256'],
                                  'claim_sha256': digest(claim), 'authorises': []}, 'completion/result/claim binding changed')
            raw = io.read(root / 'response.raw', P.MAX_RESPONSE + 1)
            raw_hash = io.sha(raw)
            # Failed attempts have the same reporting boundary as valid responses.
            # Re-derive only whitelisted metadata; never echo arbitrary stored JSON.
            reported_metadata = P.metadata(None)
            if record['status'] in ('SYNTHETIC_VALID', 'PROVIDER_VALID', 'INVALID_RESPONSE'):
                try:
                    reported_metadata = P.metadata(K.loads(raw))
                except (ValueError, TypeError):
                    pass
            K.need(all(record.get(k) == v for k, v in reported_metadata.items()), 'provider metadata inconsistent or unsafe')
            K.need(record['raw_sha256'] == raw_hash and record['raw_bytes'] == len(raw)
                   and record['plan_sha256'] == digest(plan) and record['payload_sha256'] == plan['payload_sha256'], 'result/raw/plan binding changed')
            claim = io.json_file(root / 'attempt.json')
            approval, evidence, audit = approval_for_report(root, plan)
            K.need(claim['approval_sha256'] == digest(approval) and claim['plan_sha256'] == digest(plan)
                   and io.json_file(audit / (digest(plan) + '.json')) == claim, 'attempt/audit binding changed')
            state = record['status']
            if state in ('SYNTHETIC_VALID', 'PROVIDER_VALID'):
                K.need((state == 'SYNTHETIC_VALID') == (claim['fixture'] == 'SYNTHETIC'), 'fixture kind changed')
                response = K.loads(raw)
                answer_map = P.answers(bundle['request'], response, plan['model'])
                K.need(record['model_returned'] == response['model'] and record['usage'] == response['usage']
                       and record['model_requested'] == plan['model'] and record['http_status'] == 200
                       and record['actual_cost'] == 'UNKNOWN' and record['reservation_released'] is False, 'provider provenance changed')
    result = N.report(bundle, answer_map, raw_hash)
    if answer_map:
        result['model_status'] = 'SYNTHETIC_TRANSPORT_FIXTURE_NOT_JEV_PERFORMANCE' if state == 'SYNTHETIC_VALID' else 'PROVIDER_CLASSIFICATIONS_UNCALIBRATED'
        for row in result['inspection_queue']:
            row['uncertainty'] = 'UNCALIBRATED_SYNTHETIC_TRANSPORT' if state == 'SYNTHETIC_VALID' else 'UNCALIBRATED_PROVIDER_CHOICES'
    result['provider'] = {'status': state, 'record': record, 'actual_cost': 'UNKNOWN', 'authorises': []}
    result['invalid_response_count'] = int(state == 'INVALID_RESPONSE')
    result['external_requests'] = {'at_least': 0, 'exact': 0} if not attempted or claim['fixture'] == 'SYNTHETIC' or not (root / 'dispatch-started.json').exists() else {'at_least': 1 if record and record['http_status'] is not None else 0, 'exact': None if not record or record['http_status'] is None else 1}
    return result


def approval_for_report(root, plan):
    """Read-only provenance validation survives expiry; it does not renew dispatch permission."""
    approval = io.json_file(root / 'approval.json')
    K.validate(APPROVAL, approval)
    evidence = io.read(root / 'account-evidence.bin', 1024 * 1024)
    K.need(approval['plan_sha256'] == digest(plan) and approval['payload_sha256'] == plan['payload_sha256']
           and approval['account_evidence_sha256'] == io.sha(evidence), 'stored authorisation/evidence changed')
    return approval, evidence, io.safe_path(approval['audit_root'])
