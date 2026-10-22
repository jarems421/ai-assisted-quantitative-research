"""Deterministic pilot inventory/accounting and duplicate flags, never idea scores."""
import copy
from itertools import permutations
import math

from src.research.spec import digest
from .. import engine as E, schema as S
from ..storage import ROOT
from ..v004_r3 import policy
from .prompts import A, B

ARMS = ('SCOUT_PROMPTS_V001', A, B)
STATUSES = ('UNDISPATCHED', 'INTERRUPTED', 'ERROR', 'INVALID', 'VALID')


def protocol():
    value = S.json_loads((ROOT / 'docs/opportunity_scout/prompt_evaluation_v001.json').read_text(encoding='utf-8'))
    if (value['arms'] != list(ARMS) or value['primary_lane'] != 'FORGE' or value['attempts_per_arm'] != 6
            or value['cards_per_attempt'] != 2 or value['total_intended_attempts'] != 18
            or value['total_intended_card_slots'] != 36 or value['hosted_authorised'] is not False):
        raise S.ScoutError('pilot protocol differs from versioned inventory/order')
    return value


def order():
    counts, rows = dict.fromkeys(ARMS, 0), []
    for block, indices in enumerate(permutations(range(3)), 1):
        for position, index in enumerate(indices, 1):
            arm = ARMS[index]; counts[arm] += 1
            rows.append({'block': block, 'position_in_block': position, 'arm': arm,
                         'slot': f'PROMPT-PILOT-{index + 1}-{counts[arm]:02d}',
                         'lane': 'FORGE', 'intended_cards': 2})
    return rows


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def total_or_unknown(values):
    return sum(values) if all(numeric(v) for v in values) else S.UNKNOWN


def inventory(records):
    """Supplied recorded metadata only. No model requests or reviewer labels.

    Unlisted slots remain UNDISPATCHED. Zero dispatched work is not a complete
    comparison or a zero-cost successful experiment. Known subtotals are labelled.
    """
    scheduled = order(); expected = {r['slot'] for r in scheduled}; seen = {}
    fields = {'slot', 'status', 'cards_returned', 'usage', 'model_usage', 'generation_seconds',
              'generation_human_minutes', 'review_minutes', 'cli_list_price_usd',
              'subscription_charge', 'subscription_currency'}
    for r in records:
        if set(r) != fields or r['slot'] not in expected or r['slot'] in seen or r['status'] not in STATUSES:
            raise S.ScoutError('unknown/duplicate slot, status or accounting fields')
        if r['status'] == 'UNDISPATCHED':
            raise S.ScoutError('omit undispatched records; never invent zero usage/effort')
        if type(r['cards_returned']) is not int or r['cards_returned'] < 0:
            raise S.ScoutError('nonnegative returned-card count required; preserve surplus')
        if r['status'] == 'VALID' and r['cards_returned'] != 2:
            raise S.ScoutError('VALID requires exact two-card cardinality; quality remains unreviewed')
        for key in ('generation_seconds', 'generation_human_minutes', 'review_minutes', 'cli_list_price_usd', 'subscription_charge'):
            if r[key] != S.UNKNOWN and not numeric(r[key]):
                raise S.ScoutError('effort/cost must be nonnegative finite or UNKNOWN')
        if not isinstance(r['subscription_currency'], str) or not r['subscription_currency'].strip():
            raise S.ScoutError('currency must be an observed label or UNKNOWN')
        if r['subscription_charge'] != S.UNKNOWN and r['subscription_currency'] == S.UNKNOWN:
            raise S.ScoutError('attributable charge needs its observed currency')
        if r['model_usage'] is not None and (not isinstance(r['model_usage'], dict) or set(r['model_usage']) != set(policy.MODEL_COMPONENTS)):
            raise S.ScoutError('model corroboration must contain all components or be explicitly unreported')
        seen[r['slot']] = copy.deepcopy(r)
    rows = []
    for row in scheduled:
        r = seen.get(row['slot'])
        kwargs = {'model_usage': r['model_usage']} if r and r['model_usage'] is not None else {}
        rows.append({**row, 'status': r['status'] if r else 'UNDISPATCHED', 'record': r,
                     'resource': policy.assess_final_usage(r['usage'], has_output=r['cards_returned'] > 0, **kwargs) if r else None})
    arms = {}
    stops, activity_after_stop = [], []
    for row in rows:
        if row['record']:
            if stops:
                activity_after_stop.append(row['slot'])
            reasons = []
            if row['status'] in ('INTERRUPTED', 'ERROR'):
                reasons.append(row['status'])
            if row['resource']['classification'] == 'MEASUREMENT_INTEGRITY_STOP':
                reasons.append('MEASUREMENT_INTEGRITY_STOP')
            if row['resource']['emergency_detected']:
                reasons.append('RESOURCE_EMERGENCY_STOP')
            if reasons:
                stops.append({'slot': row['slot'], 'reasons': reasons})
    for arm in ARMS:
        selected = [r for r in rows if r['arm'] == arm]; used = [r for r in selected if r['record']]
        resources = [r['resource']['reported_combined_total'] for r in used]
        human = [r['record'][k] for r in used for k in ('generation_human_minutes', 'review_minutes')]
        arms[arm] = {'reserved_attempts': len(selected), 'intended_card_slots': 2 * len(selected),
                     'consumed_attempts': len(used), 'undispatched_attempts': len(selected) - len(used),
                     'valid_attempts': sum(r['status'] == 'VALID' for r in used),
                     'invalid_error_interrupted_attempts': sum(r['status'] != 'VALID' for r in used),
                     'returned_cards_including_invalid_surplus': sum(r['record']['cards_returned'] for r in used),
                     'reported_token_total': total_or_unknown(resources) if used else S.UNKNOWN,
                     'known_token_subtotal_not_complete_total': sum(v for v in resources if policy.count(v)),
                     'total_human_minutes': total_or_unknown(human) if used else S.UNKNOWN,
                     'total_generation_seconds': total_or_unknown([r['record']['generation_seconds'] for r in used]) if used else S.UNKNOWN,
                     'cli_list_price_usd': total_or_unknown([r['record']['cli_list_price_usd'] for r in used]) if used else S.UNKNOWN,
                     'subscription_charge': S.UNKNOWN, 'charge_records': [
                         {'amount': r['record']['subscription_charge'], 'currency': r['record']['subscription_currency']} for r in used],
                     'M_investigation_worthy_count': S.UNKNOWN, 'primary_rate': S.UNKNOWN}
    return {'schema': 'SCOUT_PROMPT_EVAL_INVENTORY_V001', 'protocol_sha256': digest(protocol()),
            'slots': rows, 'arms': arms, 'reserved_attempts': 18, 'intended_card_slots': 36,
            'all_attempt_outcomes_recorded': len(seen) == 18,
            'recorded_stop_conditions': stops, 'recorded_activity_after_stop': activity_after_stop,
            'complete_comparison': False, 'independent_human_review': 'NOT_SUPPLIED',
            'structural_novelty': 'NOT_JUDGED', 'economic_coherence': 'NOT_JUDGED',
            'winner': None, 'statistical_significance': 'NOT_CLAIMED', 'authorises': []}


def duplicate_flags(ideas):
    """Reuse existing internal proximity warnings; no external novelty verdict."""
    state = E.State(); warnings = []
    for i, idea in enumerate(ideas, 1):
        S.validate(S.IDEA, idea)
        card = {'id': f'ANALYSIS-ROW-{i}', 'version': 1, 'idea': copy.deepcopy(idea)}
        warnings.extend({'row': i, **r} for r in E.proximity(state, card))
        state.cards[card['id']] = [card]
    return {'warnings': warnings, 'economic_identity_established': False, 'external_novelty': 'NOT_CHECKED',
            'human_cluster_review_required': True, 'M_or_H_certified': False}
