"""Offline Discovery Lab walkthrough: four synthetic campaigns and one retrospective control.

Runs under the repository's network guard with a fixed synthetic clock. Synthetic records are
fabricated and labelled; the SH09 control reuses repository evidence at its recorded depth only and
does not re-adjudicate SH09. No source acquisition, market data or experiment is involved.
"""
from __future__ import annotations

import copy
import hashlib
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.research.sec_pilot.parsing import offline
from src.research.discovery import records as R
from src.research.discovery.ledger import Ledger
from src.research.discovery.report import compare, summary, table
from src.research.discovery.review import checklist, source_next

ROOT = Path(__file__).resolve().parents[3]
WALKTHROUGH = ROOT / 'docs/strategy/discovery_lab_walkthrough.md'
U = R.UNKNOWN
AUTHORITY = 'docs/strategy/owner_discovery_lab_2026-10-21.md (offline engineering only; zero acquisition)'
BUDGET = {'analyst_hours': 2, 'source_starts': 0, 'external_bytes': 0}


class Clock:
    """Deterministic event times so the walkthrough regenerates byte-for-byte."""

    def __init__(self):
        self.t = datetime(2000, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        self.t += timedelta(minutes=1)
        return self.t.isoformat()


def rec(record_type, /, **fields):
    r = copy.deepcopy(R.template(record_type)); unknown = set(fields) - set(r)
    if unknown:raise KeyError(f'{record_type} has no fields {sorted(unknown)}')
    r.update(fields); return r


def syn(locator, depth='VERIFIED_ORIGINAL_FIELD', kind='ORIGINAL_DOCUMENT', passage='Synthetic fixture passage.'):
    return {'locator': 'synthetic://' + locator, 'kind': kind, 'depth': depth, 'passage': passage,
            'sha256': hashlib.sha256(locator.encode()).hexdigest() if depth in R.ORIGINAL else None,
            'archive': None, 'synthetic': True, 'reused_from': None}


def clk(value=U, basis=U, evidence=()):
    return {'value': value, 'basis': basis, 'evidence': list(evidence)}


def clocks(occurred, version=U, retrieved=U, public=None):
    return {'economic_occurrence': clk(occurred, 'DOCUMENT_DATE', [syn('dates/' + occurred)]) if occurred != U else clk(),
            'first_public': public or clk(),
            'source_version': clk(version, 'DATASET_VERSION', [syn('versions/' + version)]) if version != U else clk(),
            'retrieval': clk(retrieved, 'RETRIEVAL_RECEIPT', [syn('receipts/' + retrieved)]) if retrieved != U else clk()}


def entity(kind, eid, name):
    return {'type': kind, 'id': eid, 'name': name}


def joins(**status):
    out = {d: {'status': 'NOT_REQUIRED', 'evidence': [], 'note': 'Not required for this single-entity claim.'} for d in R.JOIN_DIMENSIONS}
    for d, s in status.items():
        out[d] = {'status': s, 'evidence': [syn(f'joins/{d}')] if s == 'VERIFIED' else [],
                  'note': 'Synthetic join evidence.' if s == 'VERIFIED' else 'Join not yet evidenced.'}
    return out


def passport(sid, name, *, field, units, depth='VERIFIED_ORIGINAL_FIELD', scheme='SYN_FACILITY', object_type='FACILITY',
             revision='VERIFIED_ORIGINAL_RECORD', publication='INDEXED_DESCRIPTION_ONLY', omissions=(), proxies=(), nxt=U):
    ev = lambda d, tag: [syn(f'{sid}/{tag}', d, 'SCHEMA' if d == 'SCHEMA_ONLY' else 'INDEX_ENTRY' if d == 'INDEXED_DESCRIPTION_ONLY'
                             else 'ORIGINAL_DOCUMENT')] if d not in ('UNVERIFIED',) else []
    return rec('source', id=sid, name=name, publisher='Synthetic publisher (fictional)', locator=f'synthetic://{sid}',
               family='synthetic administrative register', domain='synthetic fixture', formats=['CSV'],
               quantities=[{'field': field, 'meaning': f'{field} as defined by the synthetic publisher', 'units': units,
                            'denominator': 'per identified object', 'depth': depth, 'evidence': ev(depth, 'field')}],
               granularity='object-date', identifiers=[{'scheme': scheme, 'object_type': object_type, 'depth': 'VERIFIED_ORIGINAL_RECORD',
                                                        'evidence': ev('VERIFIED_ORIGINAL_RECORD', 'ids')}] if depth != 'SCHEMA_ONLY' else [],
               history={'coverage': 'synthetic 1995-2000', 'depth': 'VERIFIED_ORIGINAL_RECORD' if depth != 'SCHEMA_ONLY' else 'UNVERIFIED',
                        'evidence': ev('VERIFIED_ORIGINAL_RECORD', 'history') if depth != 'SCHEMA_ONLY' else []},
               revision_policy={'description': 'Synthetic revision behaviour', 'depth': revision, 'evidence': ev(revision, 'revisions')},
               publication_clock={'description': 'Synthetic posting practice', 'frequency': 'irregular', 'release_lag': U,
                                  'depth': publication, 'evidence': ev(publication, 'clock')},
               access={'status': 'OPEN', 'permitted_use': 'Synthetic fixture only', 'evidence': []},
               exposure_links=['A synthetic listed company may hold the identified object'], omissions=list(omissions),
               misleading_proxies=list(proxies), next_observation=nxt)


def propositions(effect, info, residual):
    return {'economic_effect': {'statement': effect, 'status': 'UNTESTED'},
            'informational_advantage': {'statement': info, 'status': 'UNVERIFIED'},
            'residual_investment_value': {'statement': residual, 'status': 'UNTESTED'}}


def selection(**overrides):
    s = {'famous_case': False, 'purposive_control': False, 'outcome_inspected_before_freeze': False, 'returns_inspected': False,
         'prior_related_claims': [], 'notes': 'Synthetic claim frozen before any synthetic outcome record was examined.'}
    s.update(overrides); return s


def substitute(checked, description, locator=None):
    return {'description': description, 'checked': checked, 'evidence': [syn(locator, 'VERIFIED_ORIGINAL_RECORD')] if checked else [],
            'not_checked_reason': None if checked else 'Not checked in this fixture; the review must acknowledge it.'}


def reviewer(kind='SYNTHETIC_FIXTURE'):
    return {'name': 'Synthetic reviewer (fixture stand-in for a human)' if kind == 'SYNTHETIC_FIXTURE' else 'Claude (assistant draft)', 'kind': kind}


def not_checked(*categories):
    notes = {'COMPETITOR': 'Closest substitute not checked.', 'OUTCOME': 'No observed outcome value yet.',
             'HISTORICAL_SOURCE': 'No original historical predictor record.', 'PUBLIC_TIME': 'First-public time not certified.'}
    return [{'category': c, 'note': notes[c]} for c in categories]


class Walk:
    def __init__(self):
        self.lines = []

    def h(self, title, level=2):
        self.lines += ['', '#' * level + ' ' + title, '']

    def say(self, text):
        self.lines += ['', text, '']

    def ok(self, label, event):
        self.lines.append(f"- Accepted: {label} (event {event['seq']}, hash `{event['hash'][:12]}`)")
        return event

    def refuse(self, label, action):
        try:action()
        except ValueError as error:
            self.lines.append(f'- **Refused as intended:** {label}. Reason: {error}')
            return
        raise AssertionError(f'{label} was accepted but must be refused')

    def checklist(self, s, cid, version=None):
        ck = checklist(s, cid, version)
        rows = [[k, v['mechanical'], '; '.join(v['blockers']) or '-', v['human_judgment']] for k, v in ck['requirements'].items()]
        self.lines += ['', f"Checklist for {cid} v{ck['version']} (software_certifies_M = {ck['software_certifies_M']}):", '',
                       table(['M requirement', 'Mechanical state', 'Blockers', 'Human judgment'], rows), '',
                       f"Gaps: {'; '.join(ck['gaps']) or 'none'}. H gaps: {'; '.join(ck['h_gaps']) or 'none'}. "
                       f"Human H: {ck['h_human_judgment']}.", '',
                       f"Next: `{ck['next']['blocker']}` ({ck['next']['requirement'] or 'review'}). {ck['next']['instruction']}", '']
        return ck


def observation_first(w, path, clock):
    w.h('1. Observation-first: a recorded state change at a synthetic facility')
    w.say('Starts from an original record. The claim is frozen before its outcome is examined; '
          'evidence then accrues as a clarification, and a post-outcome change of financial object becomes a separate reformulation.')
    camp = rec('campaign', id='DLC-SYN-OBS', title='Synthetic observation-first walkthrough', method='OBSERVATION_FIRST', fixture='SYNTHETIC',
               question='Does a recorded throughput restriction at a synthetic facility change its synthetic listed operator\'s measurable shipments?',
               authority=AUTHORITY, budget=dict(BUDGET), notes=['Fabricated fixture; no real entities.'])
    led = Ledger.create(path, camp, clock); w.lines.append('- Accepted: campaign DLC-SYN-OBS (event 0)')
    src = passport('SRC-SYN-REGISTER', 'Synthetic facility throughput register', field='permitted_throughput', units='tonnes/day',
                   proxies=['Permitted throughput is a ceiling, not actual shipments'], nxt='Archived register version showing its posting date.')
    w.ok('Source Passport SRC-SYN-REGISTER; next rung ' + source_next(src)[0], led.append('source', src))
    w.ok('Source Passport SRC-SYN-ISSUER', led.append('source', passport('SRC-SYN-ISSUER', 'Synthetic issuer quarterly operating report',
                                                                       field='facility_shipments', units='tonnes/quarter', scheme='SYN_LISTED', object_type='LISTED_COMPANY')))
    facility = entity('FACILITY', 'SYN_FACILITY:F-001', 'Synthetic Terminal North'); alpha = entity('LISTED_COMPANY', 'SYN_LISTED:ALPHA', 'Alpha Synthetic Holdings (fictional)')
    restrict = rec('observation', id='OBS-SYN-RESTRICT', source_id='SRC-SYN-REGISTER', kind='STATE_CHANGE',
                   statement='Permitted throughput at facility F-001 reduced.', value={'from': 1200, 'to': 700}, units='tonnes/day',
                   denominator='single facility', entity=facility, depth='VERIFIED_ORIGINAL_FIELD', evidence=[syn('register/F-001/2000-03-03')],
                   clocks=clocks('2000-03-01', '2000-03-03', '2000-04-01T00:00:00+00:00'), as_of_status='VERIFIED_ONLY_RETROSPECTIVELY',
                   why_informative='A state change in a binding ceiling, not a static level.', alternative_explanations=['The ceiling may exceed actual use.'],
                   outcome_independent=True, missing_evidence=['First-public time of the register version.'])
    w.ok('Observation OBS-SYN-RESTRICT (first-public time stays UNKNOWN)', led.append('observation', restrict))
    w.ok('Observation OBS-SYN-INSPECT, kept as an observation only', led.append('observation', rec(
        'observation', id='OBS-SYN-INSPECT', source_id='SRC-SYN-REGISTER', kind='QUANTITY', statement='Routine inspections at F-001 in 1999.',
        value=4, units='inspections/year', denominator='single facility', entity=facility, depth='VERIFIED_ORIGINAL_RECORD',
        evidence=[syn('register/F-001/inspections')], clocks=clocks('1999-12-31', retrieved='2000-04-01T00:00:00+00:00'),
        why_informative='Context only; not promoted.', outcome_independent=U)))
    w.refuse('a relationship inferred from coincident names but marked VERIFIED', lambda: led.append('relationship', rec(
        'relationship', id='REL-SYN-NAMES', source_entity=facility, target_entity=alpha, type='OPERATION', basis='NAME_MATCH_ONLY',
        status='VERIFIED', direction='Facility name resembles a subsidiary name.', evidence=[syn('search/names', 'UNVERIFIED', 'NAME_MATCH')])))
    operates = rec('relationship', id='REL-SYN-OPERATES', source_entity=facility, target_entity=alpha, type='OPERATION',
                   direction='Alpha operates F-001; throughput limits Alpha shipments from F-001.',
                   scope={'asset': 'SYN_FACILITY:F-001', 'contract': 'NOT_APPLICABLE', 'product': 'bulk product', 'geography': 'synthetic port'},
                   period={'start': '1995-01-01', 'end': 'OPEN'}, basis='DOCUMENTED', status='VERIFIED', evidence=[syn('issuer/annual/1999/properties', 'VERIFIED_ORIGINAL_RECORD')],
                   quantity_transfer={'status': 'NOT_APPLICABLE', 'method': 'NONE', 'evidence': [], 'note': 'Single operated facility; no allocation.'},
                   limitations=['Operation does not establish the facility share of revenue.'])
    w.ok('Relationship REL-SYN-OPERATES from documentary evidence', led.append('relationship', operates))
    base = rec('candidate', id='CAND-SYN-OBS-1', method='OBSERVATION_FIRST', entry_record='OBS-SYN-RESTRICT',
               population='Single synthetic facility F-001 and its listed operator.',
               predictor={'observation_ids': ['OBS-SYN-RESTRICT'], 'quantity': 'Change in permitted throughput at F-001', 'units': 'tonnes/day', 'transformation': 'NONE'},
               exposure={'company': alpha, 'relationship_ids': ['REL-SYN-OPERATES'], 'claim_basis': 'GROSS', 'allocation_required': False,
                         'gross': {'value': 40, 'units': 'USD million annual facility revenue (synthetic)'}, 'net': U,
                         'materiality': 'Synthetic: F-001 is described as one of two Alpha terminals.'},
               mechanism='A binding throughput ceiling lowers deliverable shipments from F-001 within the quarter.',
               outcome={'quantity': 'Reported F-001 shipments', 'units': 'tonnes/quarter', 'route': 'Issuer quarterly operating report table',
                        'source_id': 'SRC-SYN-ISSUER', 'status': 'ROUTE_ONLY', 'value': U, 'derived_from_observations': [], 'evidence': [],
                        'independence': 'Measured by the issuer, not derived from the register ceiling.'},
               joins=joins(legal_entity='VERIFIED', period='UNVERIFIED'),
               information_event={'description': 'Register version posted with the reduced ceiling', 'decision_time': '2000-03-03', 'basis': 'Dataset version date; first-public time unknown.'},
               public_time_route='Archived dated register versions; posting time not yet certified.',
               horizon='A quarterly shipment outcome could be revised within weeks of the posting.',
               closest_substitute=substitute(False, 'Issuer releases about F-001 operations.'),
               increment='Ceiling cut quantified before any issuer shipment commentary (if none exists).',
               falsification='Show that the quarterly report does not break out F-001 shipments in tonnes.',
               missing_variables=['F-001 shipments for the quarter'], selection=selection(),
               propositions=propositions('Ceiling cut reduces F-001 shipments.', 'Register posting precedes issuer commentary.', 'Not assessed.'),
               recommendation={'action': 'REQUEST_M_REVIEW', 'reason': 'Predictor observed; outcome route needs one check.'})
    bad = copy.deepcopy(base); bad['outcome']['derived_from_observations'] = ['OBS-SYN-RESTRICT']
    w.refuse('an outcome derived from the predictor observation', lambda: led.append('candidate', bad))
    w.ok('Candidate CAND-SYN-OBS-1 v1', led.append('candidate', base))
    w.ok('Freeze CAND-SYN-OBS-1 v1 before examining any outcome', led.freeze('CAND-SYN-OBS-1'))
    w.checklist(led.load(), 'CAND-SYN-OBS-1')
    w.ok('Assistant information-sceptic review (acknowledges unchecked competitor/outcome/public time)', led.append('review', rec(
        'review', id='REV-SYN-OBS-INFO', candidate_id='CAND-SYN-OBS-1', version=1, kind='SCEPTIC', role='information', reviewer=reviewer('ASSISTANT'),
        judgments={'challenges': ['The operator may have announced the restriction itself.'], 'verdict': 'CHALLENGE_UNRESOLVED',
                   'reason': 'Issuer releases not yet checked.'}, not_checked=not_checked('COMPETITOR', 'OUTCOME', 'PUBLIC_TIME'),
        conclusion='Information increment unverified.')))
    m_bad = rec('review', id='REV-SYN-OBS-M0', candidate_id='CAND-SYN-OBS-1', version=1, reviewer=reviewer(),
                judgments={k: {'judgment': 'EVIDENCED', 'reason': 'Fields populated.', 'evidence_refs': ['OBS-SYN-RESTRICT']} for k in R.M_REQUIREMENTS},
                not_checked=not_checked('COMPETITOR', 'OUTCOME', 'PUBLIC_TIME'), conclusion='Rubber stamp.')
    w.refuse('an M review marking blocked requirements EVIDENCED', lambda: led.append('review', m_bad))
    m_pass = dict(rec('disposition', id='DSP-SYN-OBS-X', candidate_id='CAND-SYN-OBS-1', version=1, decision='M_PASSED', reason_type='EVIDENCE_COMPLETE',
                      reason='Populated fields.', scope='v1', decided_by=reviewer()))
    w.refuse('an M PASSED disposition while blockers remain', lambda: led.append('disposition', m_pass))
    assistant = dict(m_pass, id='DSP-SYN-OBS-Y', decision='HOLD', reason_type='UNRESOLVED', decided_by=reviewer('ASSISTANT'))
    w.refuse('a disposition decided by an assistant', lambda: led.append('disposition', assistant))
    w.ok('Human-equivalent VERIFY disposition: one decisive check proposed, nothing authorised', led.append('disposition', rec(
        'disposition', id='DSP-SYN-OBS-1', candidate_id='CAND-SYN-OBS-1', version=1, decision='VERIFY', reason_type='UNRESOLVED',
        reason='Outcome route and period alignment are the only blockers.', scope='CAND-SYN-OBS-1 v1', decided_by=reviewer(),
        verify={'decisive_question': 'Does the quarterly report state F-001 shipments in tonnes for the affected quarter?',
                'proposed_check': 'Open the one quarterly report covering March 2000.', 'cost': {'analyst_hours': 0.5, 'source_starts': 1, 'bytes': U},
                'authority': 'PROPOSAL_ONLY'})))
    w.say('In this fixture the proposed check is treated as separately authorised and its synthetic result recorded. '
          'Recording evidence without changing the claim is a clarification, not a new claim.')
    w.ok('Effort: 25 analyst minutes on the proposed outcome check', led.append('effort', rec(
        'effort', id='EFF-SYN-OBS-1', candidate_id='CAND-SYN-OBS-1', description='Read the synthetic quarterly report table.',
        analyst_minutes=25, outcome='SUCCESS', targeted_variable='F-001 shipments')))
    w.ok('Outcome observation OBS-SYN-SHIP', led.append('observation', rec(
        'observation', id='OBS-SYN-SHIP', source_id='SRC-SYN-ISSUER', kind='QUANTITY', statement='Reported F-001 shipments, quarter ending 2000-03-31.',
        value=61000, units='tonnes/quarter', denominator='single facility', entity=facility, depth='VERIFIED_ORIGINAL_FIELD',
        evidence=[syn('issuer/q1-2000/table-3')], clocks=clocks('2000-03-31', '2000-04-28', '2000-05-01T00:00:00+00:00'),
        why_informative='Outcome record for the frozen claim.', outcome_independent=False)))
    v2 = copy.deepcopy(base); v2.update(version=2, supersedes=1, revision_reason='Record the observed outcome and period join; claim unchanged.')
    v2['outcome'].update(status='OBSERVED_VALUE', value=61000, derived_from_observations=['OBS-SYN-SHIP'], evidence=[syn('issuer/q1-2000/table-3')])
    v2['joins'] = joins(legal_entity='VERIFIED', period='VERIFIED')
    v2['closest_substitute'] = substitute(True, 'Alpha release of 2000-03-03 announcing the ceiling and expected shipment impact.', 'issuer/release/2000-03-03')
    w.ok('Candidate CAND-SYN-OBS-1 v2 (derived revision kind: CLARIFICATION)', led.append('candidate', v2))
    w.ok('Freeze v2', led.freeze('CAND-SYN-OBS-1'))
    w.checklist(led.load(), 'CAND-SYN-OBS-1')
    w.ok('Human-equivalent M review: all six EVIDENCED, unchecked public time acknowledged', led.append('review', rec(
        'review', id='REV-SYN-OBS-M', candidate_id='CAND-SYN-OBS-1', version=2, reviewer=reviewer(),
        judgments={k: {'judgment': 'EVIDENCED', 'reason': 'Synthetic evidence inspected for this requirement.', 'evidence_refs': ['OBS-SYN-RESTRICT', 'OBS-SYN-SHIP', 'REL-SYN-OPERATES']} for k in R.M_REQUIREMENTS},
        checked=[{'item': 'Register field and issuer table', 'evidence_refs': ['OBS-SYN-RESTRICT', 'OBS-SYN-SHIP']}],
        not_checked=not_checked('PUBLIC_TIME'), conclusion='Measurement object exists in the synthetic fixture.')))
    w.ok('Human-equivalent H review: UNCONVINCING, because the issuer explained the effect the same day', led.append('review', rec(
        'review', id='REV-SYN-OBS-H', candidate_id='CAND-SYN-OBS-1', version=2, kind='H', reviewer=reviewer(),
        judgments={'judgment': 'UNCONVINCING', 'information_event': 'Register posting on 2000-03-03.',
                   'expectation_mechanism': 'None beyond the issuer release on the same day.', 'reason': 'Issuer-explained; no increment shown.'},
        not_checked=not_checked('PUBLIC_TIME'), conclusion='M does not imply H.')))
    w.ok('Disposition M_PASSED (records measurement only; authorises nothing)', led.append('disposition', rec(
        'disposition', id='DSP-SYN-OBS-2', candidate_id='CAND-SYN-OBS-1', version=2, decision='M_PASSED', reason_type='EVIDENCE_COMPLETE',
        reason='All six requirements evidenced by human-equivalent review.', scope='CAND-SYN-OBS-1 v2 measurement only', decided_by=reviewer())))
    w.ok('Disposition REJECT for investment priority (COMPETITION); the M record is retained', led.append('disposition', rec(
        'disposition', id='DSP-SYN-OBS-3', candidate_id='CAND-SYN-OBS-1', version=2, decision='REJECT', reason_type='COMPETITION',
        reason='The issuer quantified the effect when the ceiling was posted.', scope='Investment priority of v2; measurement result unchanged.', decided_by=reviewer())))
    v3 = copy.deepcopy(v2); v3.update(version=3, supersedes=2, after_outcome_seen=True,
                                      revision_reason='After seeing the outcome, switch the financial object to segment revenue.')
    v3['outcome'].update(quantity='Alpha bulk segment revenue', units='USD million/quarter', status='ROUTE_ONLY', value=U,
                         derived_from_observations=[], evidence=[])
    w.ok('Candidate v3 after the outcome was seen (derived: MATERIAL_REVISION, REFORMULATION, post-outcome)', led.append('candidate', v3))
    w.ok('Freeze v3', led.freeze('CAND-SYN-OBS-1'))
    return led


def relationship_first(w, path, clock):
    w.h('2. Relationship-first: a documented contract with an undocumented allocation')
    camp = rec('campaign', id='DLC-SYN-REL', title='Synthetic relationship-first walkthrough', method='RELATIONSHIP_FIRST', fixture='SYNTHETIC',
               question='Does a cut to a shared synthetic programme ceiling change one listed supplier\'s programme revenue?',
               authority=AUTHORITY, budget=dict(BUDGET), notes=['Fabricated fixture; no real entities.'])
    led = Ledger.create(path, camp, clock); w.lines.append('- Accepted: campaign DLC-SYN-REL (event 0)')
    src = passport('SRC-SYN-AWARDS', 'Synthetic programme award notices', field='programme_ceiling', units='USD million',
                   scheme='SYN_CONTRACT', object_type='CONTRACT', revision='UNVERIFIED', nxt='Find whether amended notices keep prior versions.')
    w.ok('Source Passport SRC-SYN-AWARDS; next rung ' + source_next(src)[0], led.append('source', src))
    programme = entity('CONTRACT', 'SYN_CONTRACT:P-77', 'Synthetic framework programme P-77'); beta = entity('LISTED_COMPANY', 'SYN_LISTED:BETA', 'Beta Synthetic Industries (fictional)')
    supply = rec('relationship', id='REL-SYN-SUPPLY', source_entity=programme, target_entity=beta, type='SUPPLIER_CUSTOMER',
                 direction='Beta is one of three named suppliers under P-77.', scope={'asset': 'NOT_APPLICABLE', 'contract': 'SYN_CONTRACT:P-77', 'product': 'synthetic services', 'geography': 'synthetic state'},
                 period={'start': '1998-06-01', 'end': '2001-05-31'}, basis='DOCUMENTED', status='VERIFIED', evidence=[syn('awards/P-77/notice', 'VERIFIED_ORIGINAL_RECORD')],
                 quantity_transfer={'status': 'UNVERIFIED', 'method': 'PROPORTIONAL_ASSUMPTION', 'evidence': [], 'note': 'Ceiling shared by three suppliers; Beta share unpublished.'},
                 limitations=['A ceiling is not realised revenue.'])
    w.ok('Relationship REL-SYN-SUPPLY: relationship VERIFIED, allocation UNVERIFIED', led.append('relationship', supply))
    forced = copy.deepcopy(supply); forced.update(version=2, supersedes=1, revision_reason='Assume one third each.')
    forced['quantity_transfer'].update(status='VERIFIED')
    w.refuse('a proportional allocation relabelled VERIFIED', lambda: led.append('relationship', forced))
    w.ok('Observation OBS-SYN-CEILING', led.append('observation', rec(
        'observation', id='OBS-SYN-CEILING', source_id='SRC-SYN-AWARDS', kind='STATE_CHANGE', statement='P-77 programme ceiling amended.',
        value={'from': 300, 'to': 180}, units='USD million', denominator='whole programme, three suppliers', entity=programme,
        depth='VERIFIED_ORIGINAL_FIELD', evidence=[syn('awards/P-77/amendment-2')], clocks=clocks('2000-02-15', '2000-02-20', '2000-04-02T00:00:00+00:00'),
        as_of_status='VERIFIED_ONLY_RETROSPECTIVELY', why_informative='Ceiling cut on a named supplier programme.', outcome_independent=True)))
    cand = rec('candidate', id='CAND-SYN-REL-1', method='RELATIONSHIP_FIRST', entry_record='REL-SYN-SUPPLY', population='Programme P-77 and listed supplier Beta.',
               predictor={'observation_ids': ['OBS-SYN-CEILING'], 'quantity': 'Change in P-77 programme ceiling', 'units': 'USD million', 'transformation': 'NONE'},
               exposure={'company': beta, 'relationship_ids': ['REL-SYN-SUPPLY'], 'claim_basis': 'GROSS', 'allocation_required': True, 'gross': U, 'net': U,
                         'materiality': 'Synthetic: Beta lists P-77 among major programmes without amounts.'},
               mechanism='A lower shared ceiling reduces orders available to each supplier.',
               outcome={'quantity': 'Beta revenue from P-77', 'units': 'USD million/year', 'route': 'Issuer annual programme disclosure, if any',
                        'source_id': U, 'status': 'ROUTE_ONLY', 'value': U, 'derived_from_observations': [], 'evidence': [], 'independence': 'Issuer-reported revenue.'},
               joins=joins(legal_entity='VERIFIED', cohort='UNVERIFIED'),
               information_event={'description': 'Amendment notice posted', 'decision_time': '2000-02-20', 'basis': 'Notice version date.'},
               public_time_route='Dated award amendments; posting clock unverified.', horizon=U,
               closest_substitute=substitute(False, 'Supplier commentary on P-77.'), increment=U,
               falsification='Show that no public record allocates the P-77 ceiling or orders among suppliers.',
               missing_variables=['Beta share of P-77 orders'], selection=selection(),
               propositions=propositions('Ceiling cut lowers Beta P-77 revenue.', U, U), recommendation={'action': 'HOLD', 'reason': 'Allocation missing.'})
    w.ok('Candidate CAND-SYN-REL-1 v1 (entry: the relationship)', led.append('candidate', cand))
    w.ok('Freeze v1', led.freeze('CAND-SYN-REL-1'))
    w.checklist(led.load(), 'CAND-SYN-REL-1')
    w.ok('Assistant measurement-sceptic review', led.append('review', rec(
        'review', id='REV-SYN-REL-MEAS', candidate_id='CAND-SYN-REL-1', version=1, kind='SCEPTIC', role='measurement', reviewer=reviewer('ASSISTANT'),
        judgments={'challenges': ['Programme ceiling is aggregate; Beta share is unobserved.'], 'verdict': 'CHALLENGE_UNRESOLVED', 'reason': 'No allocation source.'},
        not_checked=not_checked('COMPETITOR', 'OUTCOME', 'PUBLIC_TIME'), conclusion='Aggregate-to-company allocation is the decisive gap.')))
    w.ok('Effort: 40 analyst minutes on the allocation question', led.append('effort', rec(
        'effort', id='EFF-SYN-REL-1', candidate_id='CAND-SYN-REL-1', description='Read synthetic notices for supplier shares.', analyst_minutes=40,
        outcome='NOT_FOUND', targeted_variable='Beta share of P-77')))
    w.ok('Disposition HOLD: decisive allocation unobserved; no automatic source work', led.append('disposition', rec(
        'disposition', id='DSP-SYN-REL-1', candidate_id='CAND-SYN-REL-1', version=1, decision='HOLD', reason_type='OBSERVATION',
        reason='Supplier allocation of the shared ceiling is undocumented.', scope='CAND-SYN-REL-1 v1', decided_by=reviewer())))
    return led


def event_first(w, path, clock):
    w.h('3. Event/expectation-first: a certified licence event the issuer already explained')
    camp = rec('campaign', id='DLC-SYN-EVT', title='Synthetic event-first walkthrough', method='EVENT_FIRST', fixture='SYNTHETIC',
               question='Could a published synthetic licence suspension inform a listed holder\'s production before the holder explains it?',
               authority=AUTHORITY, budget=dict(BUDGET), notes=['Fabricated fixture; no real entities.'])
    led = Ledger.create(path, camp, clock); w.lines.append('- Accepted: campaign DLC-SYN-EVT (event 0)')
    src = passport('SRC-SYN-LICENCES', 'Synthetic licence bulletin', field='licence_status', units='status', scheme='SYN_LICENCE', object_type='LICENCE',
                   publication='VERIFIED_ORIGINAL_RECORD', nxt='Record licence events as they post.')
    w.ok('Source Passport SRC-SYN-LICENCES; next rung ' + source_next(src)[0], led.append('source', src))
    licence = entity('LICENCE', 'SYN_LICENCE:L-9', 'Synthetic extraction licence L-9'); gamma = entity('LISTED_COMPANY', 'SYN_LISTED:GAMMA', 'Gamma Synthetic Resources (fictional)')
    certificate = clk('2000-05-02', 'PUBLICATION_RECORD', [syn('licences/bulletin/2000-05-02', 'VERIFIED_ORIGINAL_RECORD', 'PUBLICATION_RECORD')])
    event = rec('observation', id='OBS-SYN-SUSPEND', source_id='SRC-SYN-LICENCES', kind='EVENT', statement='Licence L-9 suspended.',
                value={'from': 'ACTIVE', 'to': 'SUSPENDED'}, units='licence status', denominator='single licence', entity=licence, depth='VERIFIED_ORIGINAL_FIELD',
                evidence=[syn('licences/bulletin/2000-05-02/L-9')], clocks=clocks('2000-05-01', '2000-05-02', '2000-05-03T00:00:00+00:00', certificate),
                as_of_status='VERIFIED_AS_OF', why_informative='Dated regulatory state change with a certified publication record.', outcome_independent=True)
    cached = copy.deepcopy(event); cached['id'] = 'OBS-SYN-CACHED'; cached['clocks']['first_public'] = clk('2000-05-02', 'WEB_CACHE', [syn('cache/snapshot')])
    w.refuse('a first-public time inferred from a web cache', lambda: led.append('observation', cached))
    no_cert = copy.deepcopy(event); no_cert['id'] = 'OBS-SYN-NOCERT'; no_cert['clocks']['first_public'] = clk()
    w.refuse('VERIFIED_AS_OF without a first-public certificate', lambda: led.append('observation', no_cert))
    w.ok('Event observation OBS-SYN-SUSPEND with certified first-public time', led.append('observation', event))
    w.ok('Relationship REL-SYN-LICENSEE recorded honestly as NAME_MATCH_ONLY / UNVERIFIED', led.append('relationship', rec(
        'relationship', id='REL-SYN-LICENSEE', source_entity=licence, target_entity=gamma, type='REGULATOR_LICENSEE',
        direction='Bulletin licensee name resembles a Gamma subsidiary.', basis='NAME_MATCH_ONLY', status='UNVERIFIED',
        evidence=[syn('licences/bulletin/2000-05-02/licensee', 'UNVERIFIED', 'NAME_MATCH')], limitations=['Name similarity is not ownership.'])))
    cand = rec('candidate', id='CAND-SYN-EVT-1', method='EVENT_FIRST', entry_record='OBS-SYN-SUSPEND', population='Licence L-9 and its purported listed holder.',
               predictor={'observation_ids': ['OBS-SYN-SUSPEND'], 'quantity': 'Licence status change', 'units': 'licence status', 'transformation': 'NONE'},
               exposure={'company': gamma, 'relationship_ids': ['REL-SYN-LICENSEE'], 'claim_basis': 'GROSS', 'allocation_required': False, 'gross': U, 'net': U, 'materiality': U},
               mechanism='Suspension halts extraction under L-9 for the quarter.',
               outcome={'quantity': 'Gamma reported production', 'units': 'units/quarter', 'route': 'Issuer quarterly production report', 'source_id': U,
                        'status': 'UNVERIFIED', 'value': U, 'derived_from_observations': [], 'evidence': [], 'independence': 'Issuer production, separate from licence status.'},
               joins=joins(legal_entity='UNVERIFIED'),
               information_event={'description': 'Bulletin publication of the suspension', 'decision_time': '2000-05-02', 'basis': 'Certified bulletin date.'},
               public_time_route='Certified bulletin publication record.', horizon='Suspension could revise quarterly production expectations within days.',
               closest_substitute=substitute(True, 'Gamma release on 2000-05-02 disclosing the suspension and expected production loss.', 'gamma/release/2000-05-02'),
               increment='None identified: the issuer disclosed the same event and its effect on the same day.',
               falsification='Check whether the holder disclosed the suspension no later than the bulletin.',
               missing_variables=['Documented licensee-to-Gamma ownership'], selection=selection(),
               propositions=propositions('Suspension lowers production.', 'Contradicted by same-day issuer disclosure.', 'Not assessed.'),
               recommendation={'action': 'STOP', 'reason': 'Issuer-explained event.'})
    cand['propositions']['informational_advantage']['status'] = 'CONTRADICTED'
    w.ok('Candidate CAND-SYN-EVT-1 v1 (entry: the EVENT observation)', led.append('candidate', cand))
    w.ok('Freeze v1', led.freeze('CAND-SYN-EVT-1'))
    w.checklist(led.load(), 'CAND-SYN-EVT-1')
    w.ok('Assistant information-sceptic review: FATAL_TO_CLAIM (issuer explained)', led.append('review', rec(
        'review', id='REV-SYN-EVT-INFO', candidate_id='CAND-SYN-EVT-1', version=1, kind='SCEPTIC', role='information', reviewer=reviewer('ASSISTANT'),
        judgments={'challenges': ['Same-day issuer disclosure of the event and its effect.'], 'verdict': 'FATAL_TO_CLAIM', 'reason': 'No informational increment.'},
        checked=[{'item': 'Gamma release 2000-05-02', 'evidence_refs': ['synthetic://gamma/release/2000-05-02']}], not_checked=not_checked('OUTCOME'),
        conclusion='Reject the informational proposition for this claim version.')))
    w.ok('Effort: 20 analyst minutes on the substitute check', led.append('effort', rec(
        'effort', id='EFF-SYN-EVT-1', candidate_id='CAND-SYN-EVT-1', description='Compare bulletin and issuer release dates.',
        analyst_minutes=20, outcome='SUCCESS', targeted_variable='Issuer disclosure timing')))
    w.ok('Disposition REJECT (COMPETITION), scoped to this claim version', led.append('disposition', rec(
        'disposition', id='DSP-SYN-EVT-1', candidate_id='CAND-SYN-EVT-1', version=1, decision='REJECT', reason_type='COMPETITION',
        reason='The listed company disclosed the event and its effect when it was published.',
        scope='CAND-SYN-EVT-1 v1 only; the licence bulletin source is not rejected.', decided_by=reviewer())))
    return led


def hypothesis_first(w, path, clock):
    w.h('4. Hypothesis-first baseline: a mechanism whose distinctive variable is never observed')
    camp = rec('campaign', id='DLC-SYN-HYP', title='Synthetic hypothesis-first baseline', method='HYPOTHESIS_FIRST', fixture='SYNTHETIC',
               question='Does reservoir drawdown raise a synthetic utility\'s replacement-power purchases?',
               authority=AUTHORITY, budget=dict(BUDGET), notes=['Fabricated fixture; no real entities.'])
    led = Ledger.create(path, camp, clock); w.lines.append('- Accepted: campaign DLC-SYN-HYP (event 0)')
    delta = entity('LISTED_COMPANY', 'SYN_LISTED:DELTA', 'Delta Synthetic Power (fictional)')
    cand = rec('candidate', id='CAND-SYN-HYP-1', method='HYPOTHESIS_FIRST', entry_record=None, population='Synthetic hydro plant H-3 owned by Delta.',
               predictor={'observation_ids': [], 'quantity': 'Plant-level weekly hydro generation', 'units': 'MWh/week', 'transformation': 'NONE'},
               exposure={'company': delta, 'relationship_ids': [], 'claim_basis': 'NET', 'allocation_required': False, 'gross': U, 'net': U,
                         'materiality': 'Synthetic: hydro is described as material to Delta supply.'},
               mechanism='Drawdown lowers H-3 output, so Delta buys replacement power at higher cost.',
               outcome={'quantity': 'Delta purchased-power cost', 'units': 'USD million/quarter', 'route': 'Issuer quarterly cost disclosure', 'source_id': U,
                        'status': 'ROUTE_ONLY', 'value': U, 'derived_from_observations': [], 'evidence': [], 'independence': 'Issuer cost line.'},
               joins=joins(legal_entity='UNVERIFIED', period='UNVERIFIED'), public_time_route=U, horizon=U,
               closest_substitute=substitute(False, 'Utility hydro commentary.'), increment=U,
               falsification='Show that no original record reports H-3 weekly generation.',
               missing_variables=['H-3 weekly generation', 'Delta ownership share of H-3'], selection=selection(),
               propositions=propositions('Lower hydro output raises net purchase costs.', U, U), recommendation={'action': 'HOLD', 'reason': 'Predictor unobserved.'})
    w.ok('Candidate CAND-SYN-HYP-1 v1 recorded before any observation (mechanism-first)', led.append('candidate', cand))
    w.ok('Effort: one search with UNKNOWN bytes (kept unknown, not zero)', led.append('effort', rec(
        'effort', id='EFF-SYN-HYP-1', candidate_id='CAND-SYN-HYP-1', kind='SEARCH', description='Search for plant-level generation records.',
        analyst_minutes=30, bytes=U, outcome='NOT_FOUND', targeted_variable='H-3 weekly generation')))
    w.ok('Effort: analyst time with UNKNOWN minutes', led.append('effort', rec(
        'effort', id='EFF-SYN-HYP-2', candidate_id='CAND-SYN-HYP-1', description='Read synthetic data dictionary.', analyst_minutes=U,
        outcome='PARTIAL', targeted_variable='H-3 weekly generation')))
    src = passport('SRC-SYN-HYDRO', 'Synthetic generation statistics portal', field='weekly_generation', units='MWh/week', depth='SCHEMA_ONLY',
                   scheme='SYN_PLANT', revision='UNVERIFIED', publication='UNVERIFIED', nxt='Obtain one original row for H-3.')
    w.ok('Source Passport SRC-SYN-HYDRO; next rung ' + source_next(src)[0], led.append('source', src))
    w.ok('Observation OBS-SYN-SCHEMA at SCHEMA_ONLY depth (field described, never observed)', led.append('observation', rec(
        'observation', id='OBS-SYN-SCHEMA', source_id='SRC-SYN-HYDRO', kind='QUANTITY', statement='Data dictionary defines weekly generation by plant.',
        units='MWh/week', denominator='per plant', entity=entity('FACILITY', 'SYN_PLANT:H-3', 'Synthetic hydro plant H-3'), depth='SCHEMA_ONLY',
        evidence=[syn('hydro/dictionary', 'SCHEMA_ONLY', 'SCHEMA')], clocks=clocks(U), why_informative='Would be the distinctive predictor if rows existed.')))
    v2 = copy.deepcopy(cand); v2.update(version=2, supersedes=1, revision_reason='Link the only located source before freezing.')
    v2['predictor']['observation_ids'] = ['OBS-SYN-SCHEMA']
    w.ok('Candidate v2 before freezing (derived: PRE_FREEZE_REVISION)', led.append('candidate', v2))
    w.ok('Freeze v2', led.freeze('CAND-SYN-HYP-1'))
    w.checklist(led.load(), 'CAND-SYN-HYP-1')
    w.ok('Disposition REJECT (OBSERVATION), scoped to this source and claim', led.append('disposition', rec(
        'disposition', id='DSP-SYN-HYP-1', candidate_id='CAND-SYN-HYP-1', version=2, decision='REJECT', reason_type='OBSERVATION',
        reason='The distinctive plant-level variable appears only in a schema; no record was observed.',
        scope='CAND-SYN-HYP-1 v2 with SRC-SYN-HYDRO; not a claim that no generation data exist anywhere.', decided_by=reviewer())))
    return led


def reused(locator, depth, kind, passage, reused_from, sha=None):
    return {'locator': locator, 'kind': kind, 'depth': depth, 'passage': passage, 'sha256': sha, 'archive': None,
            'synthetic': False, 'reused_from': reused_from}


def retrospective_sh09(w, path, clock):
    w.h('5. Retrospective control: SH09 re-expressed as records')
    w.say('Purposive, previously inspected and unsuitable for untouched validation. Records restate the [SH09 report](sh09_verification_report.md) '
          'at its recorded depth; nothing is re-acquired, and the original STOP decision is cited rather than re-adjudicated. '
          'The question is only whether the mechanical checklist surfaces the recorded failure before deep research.')
    report, receipt = 'docs/strategy/sh09_verification_report.md', 'docs/strategy/sh09_verification_receipt.json'
    camp = rec('campaign', id='DLC-RETRO-SH09', title='Retrospective SH09 checklist control', method='HYPOTHESIS_FIRST', fixture='RETROSPECTIVE_INSPECTED',
               question='Would the Discovery Lab checklist have identified the SH09 measurement failure from recorded evidence?',
               authority='docs/strategy/owner_discovery_lab_2026-10-21.md (reuse of existing records only)', budget={'analyst_hours': 1, 'source_starts': 0, 'external_bytes': 0},
               notes=['Original disposition: STOP / M NOT PASSED / H NOT ESTABLISHED in sh09_verification_report.md; not re-adjudicated.'])
    led = Ledger.create(path, camp, clock); w.lines.append('- Accepted: campaign DLC-RETRO-SH09 (event 0)')
    wt = 'https://www.wtoffshore.com/investors/sec-filings/all-sec-filings/content/0001104659-23-126389/0001104659-23-126389.pdf'
    wt_sha = '1d468393d22cfafe99b67b1432a38bcfc0630b85e4e76620a8e9ff5285451651'
    src = rec('source', id='SRC-SH09-WT', name='W&T December 2023 8-K and purchase agreement', publisher='W&T Offshore', locator=wt,
              family='issuer SEC filing', domain='offshore asset sale', formats=['PDF'],
              quantities=[{'field': 'Item 1.01 pending purchase price', 'meaning': 'Conditional purchase price for six named fields', 'units': 'USD',
                           'denominator': 'whole transaction', 'depth': 'VERIFIED_ORIGINAL_FIELD',
                           'evidence': [reused(wt, 'VERIFIED_ORIGINAL_FIELD', 'ORIGINAL_DOCUMENT', 'Item 1.01: $72m pending purchase.', receipt, wt_sha)]},
                          {'field': 'Exhibit A leases/units; Schedule 7.14 financial support', 'meaning': 'Sold lease set and support instruments',
                           'units': 'lease identifiers; USD', 'denominator': 'transaction', 'depth': 'UNVERIFIED', 'evidence': []}],
              granularity='transaction', identifiers=[], history={'coverage': 'single filing', 'depth': 'UNVERIFIED', 'evidence': []},
              revision_policy={'description': U, 'depth': 'UNVERIFIED', 'evidence': []},
              publication_clock={'description': 'SEC acceptance clock not acquired', 'frequency': 'event', 'release_lag': U, 'depth': 'UNVERIFIED', 'evidence': []},
              access={'status': 'OPEN', 'permitted_use': 'Recorded in SH09 receipt; private original', 'evidence': []},
              exposure_links=['Chevron predecessor obligations per later Chevron correspondence'],
              omissions=['Item 9.01 omits Exhibit A (leases/units), Exhibit C (excluded assets) and Schedule 7.14 (financial support)'],
              misleading_proxies=['Six field names are not lease identifiers'], next_observation='Original December 12 motion with its lease attachment.')
    w.ok('Source Passport SRC-SH09-WT; next rung ' + source_next(src)[0], led.append('source', src))
    letter = 'https://chevroncorp.gcs-web.com/static-files/51fe92ca-3680-42a4-b804-2c9433cfe667'
    cvx = rec('source', id='SRC-SH09-CVX', name='Chevron November 2024 correspondence', publisher='Chevron', locator=letter,
              family='issuer correspondence', domain='predecessor decommissioning', formats=['PDF'],
              quantities=[{'field': 'Cox-estate leases with outstanding obligations', 'meaning': 'Later issuer account of the liability chain',
                           'units': 'leases', 'denominator': 'Chevron chain of title', 'depth': 'RETROSPECTIVE_DESCRIPTION',
                           'evidence': [reused(letter, 'RETROSPECTIVE_DESCRIPTION', 'RETROSPECTIVE_ACCOUNT', '134 leases with outstanding obligations; ~$170m security.', 'docs/strategy/short_horizon_discovery_report.md')]}],
              granularity='lease (described, not listed)', identifiers=[], history={'coverage': U, 'depth': 'UNVERIFIED', 'evidence': []},
              revision_policy={'description': U, 'depth': 'UNVERIFIED', 'evidence': []},
              publication_clock={'description': 'Later correspondence; not an earlier predictor', 'frequency': 'event', 'release_lag': U, 'depth': 'UNVERIFIED', 'evidence': []},
              access={'status': 'BLOCKED', 'permitted_use': 'Earlier browser projection reused; 2026-10-21 request returned 403',
                      'evidence': [reused(letter, 'ACCESS_BLOCKED', 'ORIGINAL_DOCUMENT', 'HTTP 403 error body.', receipt)]},
              exposure_links=['Chevron (CIK 93410) predecessor obligations'], omissions=['Lease list and security allocation not supplied'],
              misleading_proxies=['$170m nominal security is not recoverable net security per lease'], next_observation='None within existing authority.')
    w.ok('Source Passport SRC-SH09-CVX; next rung ' + source_next(cvx)[0], led.append('source', cvx))
    cohort = entity('COHORT', 'NAME:Cox estate leases in Chevron chain of title', 'Cox estate leases with outstanding obligations')
    chevron = entity('LISTED_COMPANY', 'CIK:0000093410', 'Chevron Corporation')
    w.ok('Observation OBS-SH09-LEASES at RETROSPECTIVE_DESCRIPTION depth', led.append('observation', rec(
        'observation', id='OBS-SH09-LEASES', source_id='SRC-SH09-CVX', kind='STATE_CHANGE',
        statement='Leases expected to find buyers were left unsold or abandoned (later issuer account).', value='134 leases (later description)',
        units='leases', entity=cohort, depth='RETROSPECTIVE_DESCRIPTION',
        evidence=[reused(letter, 'RETROSPECTIVE_DESCRIPTION', 'RETROSPECTIVE_ACCOUNT', 'December 12, 2023 motion to abandon described later.', 'docs/strategy/short_horizon_discovery_report.md')],
        clocks={'economic_occurrence': clk('2023-12-12', 'RETROSPECTIVE_ACCOUNT', [reused(letter, 'RETROSPECTIVE_DESCRIPTION', 'RETROSPECTIVE_ACCOUNT', 'Reported motion date.', report)]),
                'first_public': clk(), 'source_version': clk('2024-11-12', 'DOCUMENT_DATE', [reused(letter, 'RETROSPECTIVE_DESCRIPTION', 'RETROSPECTIVE_ACCOUNT', 'Letter date.', report)]),
                'retrieval': clk()},
        why_informative='The intended distinctive state change (expected sale to unsold) for the predecessor.',
        alternative_explanations=['Management expectation change is not an established public surprise.'],
        prior_disclosure='Chevron quarterly filings reportedly discussed possible exposure (not re-audited).', outcome_independent=U,
        missing_evidence=['Original December 12 motion and lease attachment', 'Pre-January-2 public availability'])))
    w.ok('Relationship REL-SH09-PREDECESSOR at retrospective depth (UNVERIFIED; aggregate security not allocated)', led.append('relationship', rec(
        'relationship', id='REL-SH09-PREDECESSOR', source_entity=cohort, target_entity=chevron, type='PREDECESSOR_OBLIGATION',
        direction='Obligations may return to Chevron as a former owner.', basis='INFERRED', status='UNVERIFIED',
        evidence=[reused(letter, 'RETROSPECTIVE_DESCRIPTION', 'RETROSPECTIVE_ACCOUNT', '205 leases in chain of title; 134 with outstanding obligations.', 'docs/strategy/short_horizon_discovery_report.md')],
        quantity_transfer={'status': 'UNVERIFIED', 'method': 'AGGREGATE_AS_COHORT', 'evidence': [], 'note': '~$170m security is not allocated to leases or netted.'},
        limitations=['Ownership history alone does not establish accrued obligation, co-obligors or recoverable security.'])))
    w.ok('Effort: reuse of recorded SH09 evidence (zero new bytes)', led.append('effort', rec(
        'effort', id='EFF-SH09-REUSE', kind='DOCUMENT_REUSE', description='Restate recorded SH09 evidence.', analyst_minutes=U,
        receipt=receipt, outcome='SUCCESS')))
    cand = rec('candidate', id='CAND-SH09-1', method='HYPOTHESIS_FIRST', entry_record=None, after_outcome_seen=True,
               population='Cox-estate leases with Chevron predecessor obligations, December 2023.',
               predictor={'observation_ids': ['OBS-SH09-LEASES'], 'quantity': 'Change in Chevron recoverable-net predecessor cleanup exposure',
                          'units': 'USD', 'transformation': 'Lease engineering cost net of applicable recoverable security'},
               exposure={'company': chevron, 'relationship_ids': ['REL-SH09-PREDECESSOR'], 'claim_basis': 'NET', 'allocation_required': True,
                         'gross': U, 'net': U, 'materiality': 'Aggregate CVX accounting consequence reported later; not lease-matched.'},
               mechanism='Assets expected to transfer to a solvent buyer are abandoned, returning obligations to the predecessor.',
               outcome={'quantity': 'Lease-matched liability revision, provision, payment or recovery', 'units': 'USD', 'route': 'Not identified at lease level',
                        'source_id': U, 'status': 'UNVERIFIED', 'value': U, 'derived_from_observations': [], 'evidence': [],
                        'independence': 'The January 2 combined charge is not cleanup-only or lease-matched.'},
               joins=joins(legal_entity='UNVERIFIED', cohort='UNVERIFIED', period='UNVERIFIED', accounting_basis='UNVERIFIED'),
               information_event={'description': 'Abandonment motion becoming public before 2024-01-02', 'decision_time': '2024-01-02', 'basis': 'Stipulated issuer-disclosure boundary.'},
               public_time_route='Court/claims-agent filing route identified; the filing itself was not acquired.', horizon=U,
               closest_substitute={'description': 'W&T transaction disclosure; GOMDecom and King & Spalding analyses', 'checked': True,
                                   'evidence': [reused(wt, 'VERIFIED_ORIGINAL_RECORD', 'ORIGINAL_DOCUMENT', 'Pending purchase and liability boundaries.', receipt, wt_sha)],
                                   'not_checked_reason': None},
               increment=U, falsification='Already located original December 12 motion plus lease attachment and pre-January-2 public evidence.',
               missing_variables=['Original asset list', 'Dated predecessor obligations', '2023 cost vintage', 'Applicable recoverable security', 'Lease-matched outcome'],
               selection=selection(famous_case=True, purposive_control=True, outcome_inspected_before_freeze=True,
                                   notes='Formed after Chevron disclosed its charge; purposive control only.'),
               propositions=propositions('Returning obligations raise predecessor cost.', U, U), recommendation={'action': 'STOP', 'reason': 'Cited from the SH09 report.'})
    w.ok('Candidate CAND-SH09-1 v1 (post-outcome, purposive)', led.append('candidate', cand))
    w.ok('Freeze v1', led.freeze('CAND-SH09-1'))
    ck = w.checklist(led.load(), 'CAND-SH09-1')
    blocked = sum(1 for r in ck['requirements'].values() if r['blockers'])
    w.say(f'The checklist blocks {blocked} of six requirements from recorded evidence alone, including the missing original lease list, '
          'the unallocated aggregate security and the absent lease-matched outcome: the failure the SH09 verification established after its source work. '
          'This is a regression check of the instrument, not new evidence about SH09.')
    return led


def tamper_check(w, path):
    w.h('6. Integrity: editing a frozen claim in the file is detected')
    lines = path.read_bytes().splitlines()
    for i, line in enumerate(lines):
        if b'"type":"candidate"' in line and b'CAND-SYN-OBS-1' in line:
            lines[i] = line.replace(b'tonnes/day', b'tonnes/week', 1); break
    copy_path = path.with_name('tampered.jsonl'); copy_path.write_bytes(b'\n'.join(lines) + b'\n')
    w.refuse('loading a copy whose frozen candidate units were edited', lambda: Ledger(copy_path).load())


def run(directory):
    """Build all walkthrough ledgers in ``directory`` and return the walkthrough Markdown."""
    directory = Path(directory); clock = Clock(); w = Walk()
    w.lines += ['# Discovery Lab offline walkthrough', '',
                'Generated by `python -m src.research.discovery demo --write` and verified by `demo --check`. A fixed synthetic clock makes it '
                'byte-reproducible. Everything ran under the repository network guard: zero source acquisition, no market data, no experiment. '
                'Sections 1-4 are fabricated fixtures, one per discovery method with equal budgets; section 5 restates recorded SH09 evidence. '
                'See the [operator guide](discovery_lab_guide.md).']
    with offline():
        ledgers = [observation_first(w, directory / 'DLC-SYN-OBS.jsonl', clock), relationship_first(w, directory / 'DLC-SYN-REL.jsonl', clock),
                   event_first(w, directory / 'DLC-SYN-EVT.jsonl', clock), hypothesis_first(w, directory / 'DLC-SYN-HYP.jsonl', clock),
                   retrospective_sh09(w, directory / 'DLC-RETRO-SH09.jsonl', clock)]
        tamper_check(w, directory / 'DLC-SYN-OBS.jsonl')
        states = [led.load() for led in ledgers]
        w.h('7. Campaign summaries')
        for s in states:
            w.lines += [line.replace('# ', '### ', 1) if line.startswith('# ') else line.replace('## ', '#### ', 1) if line.startswith('## ') else line
                        for line in summary(s).splitlines()] + ['']
        w.h('8. Method comparison')
        w.lines += [line.replace('# ', '### ', 1) if line.startswith('# ') else line.replace('## ', '#### ', 1) if line.startswith('## ') else line
                    for line in compare(states).splitlines()]
    return '\n'.join(w.lines).rstrip() + '\n'


def generate():
    with tempfile.TemporaryDirectory() as tmp:return run(tmp)


def check():
    if not WALKTHROUGH.exists() or WALKTHROUGH.read_text(encoding='utf-8') != generate():
        raise ValueError('docs/strategy/discovery_lab_walkthrough.md differs from the generated walkthrough; run demo --write')
    return {'walkthrough': 'PASS', 'network': 'blocked', 'acquisition': 0}
