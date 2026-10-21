"""Actual generation records, including failures and missingness, without a quality score."""
from . import schema as S


def generation(state):
    rows = []
    for aid, attempt in state.attempts.items():
        provider = attempt.get('result', {}).get('provider', {})
        effort = next((r for r in reversed(state.efforts) if r.get('attempt_id') == aid), None)
        rows.append({'attempt_id': aid, 'status': attempt.get('result', {}).get('status', 'PENDING'),
            'requested_cards': state.prompts[attempt['prompt_id']]['count'],
            'imported_cards': sum(v[0]['provenance']['attempt_id'] == aid for v in state.cards.values()),
            'invocation_status': effort['invocation_status'] if effort else S.UNKNOWN,
            'model': provider.get('model', S.UNKNOWN), 'provider': provider.get('provider', S.UNKNOWN),
            'parameters': provider.get('parameters', S.UNKNOWN),
            'input_tokens': provider.get('usage', {}).get('input_tokens', S.UNKNOWN),
            'output_tokens': provider.get('usage', {}).get('output_tokens', S.UNKNOWN),
            'human_minutes': effort['human_minutes'] if effort else S.UNKNOWN,
            'wall_seconds': effort['wall_seconds'] if effort else S.UNKNOWN,
            'effort_recorded': effort is not None, 'context_id': effort['context_id'] if effort else S.UNKNOWN,
            'fresh_context': effort['fresh_context'] if effort else S.UNKNOWN,
            'no_prior_generated_cards': effort['no_prior_generated_cards'] if effort else S.UNKNOWN})
    totals = {}
    for field in ('input_tokens', 'output_tokens', 'human_minutes', 'wall_seconds'):
        values = [r[field] for r in rows]
        totals[field] = {'known_total': sum(v for v in values if v != S.UNKNOWN),
                         'unknown_entries': sum(v == S.UNKNOWN for v in values),
                         'total': sum(values) if values and S.UNKNOWN not in values else S.UNKNOWN}
    return {'attempts': rows, 'totals': totals, 'reserved': len(rows), 'cards': len(state.cards),
            'invoked_reported': sum(r['invocation_status'] == 'INVOKED' for r in rows),
            'invocation_unknown': sum(r['invocation_status'] == S.UNKNOWN for r in rows),
            'completed': sum(r['status'] != 'PENDING' for r in rows),
            'unbound_generation_effort_records': sum(r['kind'] == 'GENERATION' for r in state.efforts)}


def fairness(states, config):
    from src.research.spec import digest
    conditions, deviations, missing, contexts, identities = {}, [], [], [], []
    if set(states) != {'PLAIN', 'EVIDENCE_ONLY', 'MECHANISM_ONLY', 'HYBRID'}:
        deviations.append('all four conditions are required')
    for label, values in (('seed pool', [digest(s.seeds) for s in states.values()]),
                          ('memory pool', [digest(s.batch['memory']) for s in states.values()]),
                          ('knowledge cutoff', [s.batch['knowledge_cutoff'] for s in states.values()])):
        if len(set(values)) != 1: deviations.append(label + ' differs across conditions')
    for name, state in states.items():
        data = generation(state); conditions[name] = data
        if any(state.batch[k] != config[c] for k, c in (('max_cards', 'raw_cards'),
               ('max_attempts', 'generation_attempts'), ('max_output_tokens', 'max_output_tokens_per_attempt'))):
            deviations.append(name + ': configured ceilings differ from protocol')
        if len(state.cards) != config['raw_cards']: missing.append(name + ': raw card collection incomplete')
        if data['reserved'] != config['generation_attempts'] or data['completed'] != config['generation_attempts']:
            deviations.append(name + ': actual attempt count/completion differs from protocol')
        for row in data['attempts']:
            prefix = name + '/' + row['attempt_id']
            if row['status'] != 'VALID': deviations.append(prefix + ': ' + row['status'])
            if 'cards_per_attempt' in config and (row['requested_cards'] != config['cards_per_attempt']
                    or row['imported_cards'] != config['cards_per_attempt']):
                deviations.append(prefix + ': actual/requested card allocation differs from protocol')
            if row['invocation_status'] == S.UNKNOWN: missing.append(prefix + ': actual invocation UNKNOWN')
            if row['invocation_status'] == 'NOT_INVOKED': deviations.append(prefix + ': reserved attempt was not invoked')
            for field, cap in (('output_tokens', config['max_output_tokens_per_attempt']),
                               ('input_tokens', config.get('max_input_tokens_per_attempt', 30000))):
                if row[field] == S.UNKNOWN: missing.append(prefix + ': ' + field + ' UNKNOWN')
                elif row[field] > cap: deviations.append(prefix + ': ' + field + ' exceeds cap')
            if not row['effort_recorded']: missing.append(prefix + ': attempt effort missing')
            for field in ('human_minutes', 'wall_seconds', 'fresh_context', 'no_prior_generated_cards', 'context_id'):
                if row[field] == S.UNKNOWN: missing.append(prefix + ': ' + field + ' UNKNOWN')
            if row['fresh_context'] == 'NO' or row['no_prior_generated_cards'] == 'NO':
                deviations.append(prefix + ': context independence failed')
            if row['context_id'] != S.UNKNOWN: contexts.append(row['context_id'])
            if row['model'] == S.UNKNOWN or row['parameters'] == S.UNKNOWN: missing.append(prefix + ': model/settings UNKNOWN')
            else: identities.append(digest([row['model'], row['provider'], row['parameters']]))
        for field, cap in (('human_minutes', config.get('generation_human_minutes', 30)),
                           ('wall_seconds', config.get('generation_wall_seconds', 1800))):
            if data['totals'][field]['known_total'] > cap: deviations.append(name + ': ' + field + ' exceeds condition cap')
        if data['unbound_generation_effort_records']:
            missing.append(name + ': unbound generation effort cannot establish per-attempt compliance')
    if len(contexts) != len(set(contexts)): deviations.append('context identifiers reused across requests')
    if len(set(identities)) > 1: deviations.append('actual model/provider/settings differ')
    return {'conditions': conditions, 'deviations': deviations, 'incomplete_records': missing,
            'reserved_attempt_counts_equal': len({x['reserved'] for x in conditions.values()}) == 1,
            'completed_attempt_counts_equal': len({x['completed'] for x in conditions.values()}) == 1,
            'actual_attempt_counts_equal': (S.UNKNOWN if any(x['invocation_unknown'] for x in conditions.values())
                                            else len({x['invoked_reported'] for x in conditions.values()}) == 1),
            'actual_effort_equal': {f: (S.UNKNOWN if any(x['totals'][f]['total'] == S.UNKNOWN for x in conditions.values())
                                      else len({x['totals'][f]['total'] for x in conditions.values()}) == 1)
                                    for f in ('human_minutes', 'wall_seconds', 'input_tokens', 'output_tokens')},
            'comparative_eligible': bool(states) and not deviations and not missing,
            'independence': 'OPERATOR_ATTESTATION_NOT_PROVEN_BY_SOFTWARE', 'authorises': []}
