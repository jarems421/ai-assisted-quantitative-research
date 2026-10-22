"""Versioned reported-resource decisions; no provider, cancellation or billing IO."""
from src.research.spec import digest
from .. import schema as S

VERSION = 'SCOUT_V004_RESOURCE_POLICY_R3'
PLANNING_REFERENCE = 60000
ELEVATED_FLAG = 120000
EMERGENCY_TRIGGER = 200000
COMPONENTS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')
MODEL_COMPONENTS = ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens')
_ABSENT = object()


def description():
    return {'schema': VERSION, 'combined_planning_reference_tokens': PLANNING_REFERENCE,
            'planning_reference_is_ceiling': False, 'output_planning_guideline_tokens': 20000,
            'output_guideline_is_cap_or_target': False, 'candidate_per_response_output_tokens': 32768,
            'elevated_usage_flag_at_tokens': ELEVATED_FLAG, 'emergency_trigger_at_tokens': EMERGENCY_TRIGGER,
            'trigger_comparator': '>=', 'formula': list(COMPONENTS),
            'thinking_is_output_subcount': True, 'max_parent_invocations': 1,
            'max_visible_generations': 2, 'max_append_only_continuations': 1,
            'implemented_offline': True, 'owner_protocol_adopted': False,
            'hosted_authorised': False, 'guaranteed_token_or_financial_limit': False,
            'underlying_provider_requests': S.UNKNOWN}


def policy_hash(): return digest(description())


def count(value): return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def classification(total):
    if not count(total): return 'MEASUREMENT_INTEGRITY_STOP'
    if total >= EMERGENCY_TRIGGER: return 'RESOURCE_EMERGENCY_STOP'
    if total >= ELEVATED_FLAG: return 'ELEVATED_USAGE_RECORDED'
    return 'ORDINARY_USAGE_VARIATION'


def assess_final_usage(usage, model_usage=_ABSENT, *, has_output=False):
    """CLI terminal ordinary input is uncached input; all four parts count once.

    Model totals are corroboration, never additional consumption. Nested cache
    details and thinking are subcounts. Invalid/conflicting evidence stays known
    in parts/issues but does not become a compliant aggregate or a zero charge.
    """
    usage = usage if isinstance(usage, dict) else {}
    parts = {k: usage[k] if count(usage.get(k)) else S.UNKNOWN for k in COMPONENTS}
    issues = [k + '_MISSING_OR_INVALID' for k in COMPONENTS if parts[k] == S.UNKNOWN]
    details = usage.get('output_tokens_details')
    thinking = details.get('thinking_tokens', S.UNKNOWN) if isinstance(details, dict) else S.UNKNOWN
    if thinking != S.UNKNOWN and not count(thinking): issues.append('THINKING_SUBCOUNT_INVALID')
    if count(thinking) and count(parts['output_tokens']) and thinking > parts['output_tokens']:
        issues.append('THINKING_SUBCOUNT_EXCEEDS_OUTPUT')
    if has_output and parts['output_tokens'] == 0: issues.append('OUTPUT_ZERO_CONFLICTS_WITH_TEXT')
    if model_usage is not _ABSENT:
        if not isinstance(model_usage, dict): issues.append('MODEL_USAGE_INVALID')
        elif any(k in model_usage for k in MODEL_COMPONENTS):
            if any(not count(model_usage.get(m)) or model_usage[m] != parts[c]
                   for c, m in zip(COMPONENTS, MODEL_COMPONENTS)):
                issues.append('TERMINAL_MODEL_USAGE_CONFLICT')
    component_total = sum(parts.values()) if all(count(v) for v in parts.values()) else S.UNKNOWN
    total = component_total if not issues else S.UNKNOWN
    return {'schema': VERSION, 'policy_sha256': policy_hash(), 'reported_components': parts,
            'reported_input_total': sum(parts[k] for k in COMPONENTS[:3]) if all(count(parts[k]) for k in COMPONENTS[:3]) else S.UNKNOWN,
            'reported_output_total': parts['output_tokens'], 'reported_thinking_subcount': thinking,
            'reported_known_component_subtotal': sum(v for v in parts.values() if count(v)),
            'unreconciled_reported_component_total': component_total,
            'reported_combined_total': total, 'classification': classification(total), 'issues': issues,
            'difference_from_planning_reference': total - PLANNING_REFERENCE if count(total) else S.UNKNOWN,
            'planning_reference_tokens': PLANNING_REFERENCE, 'planning_reference_is_ceiling': False,
            'elevated_usage_flag': count(total) and total >= ELEVATED_FLAG,
            # Preserve a simultaneous reported emergency even when another
            # measurement contradicts it; the reconciled aggregate stays UNKNOWN.
            'emergency_detected': count(component_total) and component_total >= EMERGENCY_TRIGGER,
            'provider_usage_completeness': S.UNKNOWN, 'actual_subscription_charge': S.UNKNOWN,
            'actual_subscription_charge_currency': S.UNKNOWN, 'guaranteed_limit': False,
            'hosted_authorised': False}


def review_live_samples(samples, session_id):
    """Fictional cumulative-counter contract, not certified native CLI telemetry.

    No callback or process is available to cancel. Emit a decision only. Empty
    telemetry is normal until final usage arrives. Repeated snapshots are never
    summed; malformed/unverified supplied counters cannot trigger cancellation.
    """
    issues, seen, last, duplicates, first_emergency = [], {}, None, 0, None
    if not isinstance(samples, (list, tuple)):
        samples = []; issues.append('INVALID_LIVE_SAMPLE_CONTAINER')
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != {'source', 'session_id', 'sequence', 'usage'}:
            issues.append('UNVERIFIED_LIVE_SAMPLE'); break
        if (sample['source'] != 'FICTIONAL_CUMULATIVE_ATTEMPT_USAGE_V1' or sample['session_id'] != session_id
                or not count(sample['sequence']) or sample['sequence'] < 1):
            issues.append('UNVERIFIED_LIVE_SAMPLE'); break
        if sample['sequence'] in seen:
            if sample != seen[sample['sequence']]: issues.append('CONFLICTING_LIVE_REPLAY'); break
            duplicates += 1; continue
        usage = sample['usage']
        if not isinstance(usage, dict) or set(usage) != set(COMPONENTS) or not all(count(v) for v in usage.values()):
            issues.append('INVALID_LIVE_COMPONENTS'); break
        if last is not None and (sample['sequence'] <= last['sequence'] or
                                any(usage[k] < last['usage'][k] for k in COMPONENTS)):
            issues.append('NONMONOTONIC_LIVE_COUNTER'); break
        seen[sample['sequence']] = sample; last = sample
        if sum(usage.values()) >= EMERGENCY_TRIGGER and first_emergency is None: first_emergency = sample['sequence']
    trusted = bool(last) and not issues
    total = sum(last['usage'].values()) if trusted else S.UNKNOWN
    emergency = first_emergency is not None
    return {'source_scope': 'FICTIONAL_RECORDED_COUNTER_ONLY', 'native_cli_support': S.UNKNOWN,
            'sample_count': len(samples), 'deduplicated_repeats': duplicates, 'issues': issues,
            'trustworthy_in_fictional_contract': trusted, 'last_components': last['usage'] if trusted else S.UNKNOWN,
            'reported_cumulative_lower_bound': total, 'emergency_detected': emergency,
            'first_emergency_sample_sequence': first_emergency,
            'cancellation_signal': 'CANCEL_IF_SUPPORTED' if emergency else 'NONE',
            'cancellation_performed': False, 'guaranteed_limit': False}


def reconcile(resource, live):
    """Retain every final/live conflict and simultaneous emergency observation."""
    if live['issues']: resource['issues'].extend(live['issues'])
    if live['trustworthy_in_fictional_contract']:
        for k, lower in live['last_components'].items():
            final = resource['reported_components'][k]
            if count(final) and lower > final:
                resource['issues'].append('FINAL_BELOW_OBSERVED_LIVE_' + k.upper())
    if resource['issues']:
        resource['classification'] = 'MEASUREMENT_INTEGRITY_STOP'
        resource['reported_combined_total'] = S.UNKNOWN
        resource['difference_from_planning_reference'] = S.UNKNOWN
    resource['emergency_detected'] = resource['emergency_detected'] or live['emergency_detected']
    resource['live_telemetry'] = live
    reasons = []
    if resource['classification'] == 'MEASUREMENT_INTEGRITY_STOP': reasons.append('MEASUREMENT_INTEGRITY_STOP')
    if resource['emergency_detected']: reasons.append('RESOURCE_EMERGENCY_STOP')
    resource['stop_reasons'] = reasons
    return resource
