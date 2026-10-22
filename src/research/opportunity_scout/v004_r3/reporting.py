"""R3 descriptive resource outcomes and fixed slots, never human judgments."""
from .. import schema as S
from ..v004_package import CONDITIONS
from . import policy

VERSION = 'SCOUT_V004_RESOURCE_REPORT_R3'


def totals(receipts, interrupted_count=0):
    result = {'recorded_attempts': len(receipts), 'known_combined_subtotal': 0,
              'unrecorded_consumed_attempts': interrupted_count,
              'unknown_combined_entries': interrupted_count, 'component_known_subtotals': {k: 0 for k in policy.COMPONENTS},
              'component_unknown_entries': {k: interrupted_count for k in policy.COMPONENTS},
              'elevated_annotations': 0, 'emergency_events': 0, 'measurement_stops': 0,
              'content_valid': 0, 'content_invalid': 0, 'content_undetermined': 0}
    for receipt in receipts:
        resource = receipt['resource']; total = resource['reported_combined_total']
        if policy.count(total): result['known_combined_subtotal'] += total
        else: result['unknown_combined_entries'] += 1
        for key, count in resource['reported_components'].items():
            if policy.count(count): result['component_known_subtotals'][key] += count
            else: result['component_unknown_entries'][key] += 1
        result['elevated_annotations'] += bool(resource['elevated_usage_flag'])
        result['emergency_events'] += bool(resource['emergency_detected'])
        result['measurement_stops'] += resource['classification'] == 'MEASUREMENT_INTEGRITY_STOP'
        result['content_' + receipt['content_status'].lower()] += 1
    result['reported_combined_total'] = (S.UNKNOWN if result['unknown_combined_entries'] else result['known_combined_subtotal'])
    result['actual_subscription_charge'] = S.UNKNOWN
    result['thinking_is_not_added_twice'] = True
    return result


def summarize(manifest, consumed, receipts, pending, stopped):
    order = manifest['order']; consumed_slots = {c['slot'] for c in consumed}
    rows, prefixes, interrupted_prefix = [], [], 0
    for slot in order:
        r = receipts.get(slot['slot'])
        if r: prefixes.append(r)
        elif slot['slot'] in consumed_slots: interrupted_prefix += 1
        rows.append({**slot, 'status': r['outcome'] if r else
                     'CONSUMED_INTERRUPTED' if slot['slot'] in consumed_slots else 'NOT_RUN',
                     'intended_card_slots': 2, 'content_status': r['content_status'] if r else 'NOT_OBSERVED',
                     'resource': r['resource'] if r else None,
                     'integrity_faults': r['integrity_faults'] if r else [],
                     'format_faults': r['format_faults'] if r else [],
                     'cumulative_attempt_usage': totals(prefixes, interrupted_prefix),
                     'parsed_card_count': (len(r['value']['ideas']) if r and isinstance(r['value'], dict)
                                           and isinstance(r['value'].get('ideas'), list) else S.UNKNOWN),
                     'visible_generations': r['visible_generations'] if r else S.UNKNOWN,
                     'visible_request_ids': r['visible_request_ids'] if r else S.UNKNOWN,
                     'append_only_continuations': r['continuations'] if r else S.UNKNOWN,
                     'reported_agentic_turns': r['reported_agentic_turns'] if r else S.UNKNOWN,
                     'underlying_provider_requests': S.UNKNOWN,
                     'cli_list_price_estimate_usd': r['cli_list_price_estimate_usd'] if r else S.UNKNOWN,
                     'actual_subscription_charge': S.UNKNOWN,
                     'wall_seconds': r['wall_seconds'] if r else S.UNKNOWN,
                     'review_required_even_if_invalid': True})
    per_condition = {c: totals([r for s,r in receipts.items() if s.startswith(c+'-')],
                              sum(s.startswith(c+'-') and s not in receipts for s in consumed_slots))
                     for c in CONDITIONS}
    blocks = []
    for end in (4,8,12):
        selected=[receipts[r['slot']] for r in order[:end] if r['slot'] in receipts]
        blocks.append({'after_position': end, 'checkpoint_reached': all(r['slot'] in receipts for r in order[:end]),
                       'usage': totals(selected, sum(r['slot'] in consumed_slots and r['slot'] not in receipts for r in order[:end]))})
    events = [{'slot':s, 'resource_stop_reasons':r['resource']['stop_reasons'], 'faults':r['faults']}
              for s,r in receipts.items() if r['outcome']=='RUN_STOP']
    all_recorded = len(receipts)==12
    return {'schema': VERSION, 'fictional': True, 'resource_policy': policy.description(),
            'resource_policy_sha256': policy.policy_hash(), 'slots': rows,
            'consumed_attempts': len(consumed), 'recorded_attempts':len(receipts),
            'undispatched':12-len(consumed), 'stopped':stopped or pending is not None,
            'pending_requires_owner_review':pending is not None,
            'all_scheduled_slots_recorded':all_recorded,
            'workflow_complete':all_recorded and not stopped and pending is None,
            'data_complete_with_governance_event':all_recorded and stopped,
            'complete_scientific_comparison':False, 'independent_human_reviews':S.UNKNOWN,
            'human_effort':S.UNKNOWN, 'intended_attempt_denominator':12, 'intended_card_denominator':24,
            'actual_usage_outcome':totals(list(receipts.values()), len(consumed_slots-set(receipts))), 'per_condition_usage':per_condition,
            'block_checkpoints':blocks, 'run_events':events, 'underlying_provider_requests':S.UNKNOWN,
            'actual_cancellation_performed':False, 'hosted_authorised':False, 'authorises':[]}
