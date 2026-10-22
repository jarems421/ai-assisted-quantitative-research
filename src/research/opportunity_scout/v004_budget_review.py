"""Offline combined-token accounting for the unapproved V004 R2 proposal.

Consumes CLI terminal usage, whose input_tokens is ordinary (uncached) input,
not Scout's older provenance usage where input_tokens is already aggregated.
No execution, provider call, billing inference or V003 record mutation occurs.
"""
from . import schema as S

COMBINED_ALLOWANCE = 60000
OUTPUT_PLANNING_GUIDE = 20000
COMPONENTS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')


def valid_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def assess_reported_budget(terminal_usage):
    """Post-hoc arithmetic only; neither consumption prevention nor authority.

    Unknown/invalid components never become zero. Thinking is an optional
    subcount of output; nested cache durations are optional subdetails of cache
    creation. Neither is added again. Conflicting thinking makes status UNKNOWN.
    """
    usage = terminal_usage if isinstance(terminal_usage, dict) else {}
    parts = {k: usage.get(k, S.UNKNOWN) if valid_count(usage.get(k)) else S.UNKNOWN for k in COMPONENTS}
    issues = [k + '_MISSING_OR_INVALID' for k in COMPONENTS if parts[k] == S.UNKNOWN]
    details = usage.get('output_tokens_details')
    thinking = details.get('thinking_tokens', S.UNKNOWN) if isinstance(details, dict) else S.UNKNOWN
    if thinking != S.UNKNOWN and not valid_count(thinking):
        issues.append('THINKING_SUBCOUNT_INVALID'); thinking = S.UNKNOWN
    if thinking != S.UNKNOWN and parts['output_tokens'] != S.UNKNOWN and thinking > parts['output_tokens']:
        issues.append('THINKING_SUBCOUNT_EXCEEDS_OUTPUT')
    total_input = (sum(parts[k] for k in COMPONENTS[:3])
                   if all(parts[k] != S.UNKNOWN for k in COMPONENTS[:3]) else S.UNKNOWN)
    combined = sum(parts.values()) if not issues else S.UNKNOWN
    return {'schema': 'SCOUT_V004_COMBINED_BUDGET_REVIEW_R2',
            'reported_components': parts, 'reported_input_total': total_input,
            'reported_output_total': parts['output_tokens'], 'reported_thinking_subcount': thinking,
            'reported_combined_total': combined, 'combined_allowance_tokens': COMBINED_ALLOWANCE,
            'budget_status': ('UNKNOWN' if combined == S.UNKNOWN else
                              'OVER_ALLOWANCE' if combined > COMBINED_ALLOWANCE else 'WITHIN_ALLOWANCE'),
            'excess_tokens': max(0, combined - COMBINED_ALLOWANCE) if combined != S.UNKNOWN else S.UNKNOWN,
            'output_planning_guideline_tokens': OUTPUT_PLANNING_GUIDE,
            'output_above_planning_guideline': (parts['output_tokens'] > OUTPUT_PLANNING_GUIDE
                                               if parts['output_tokens'] != S.UNKNOWN else S.UNKNOWN),
            'output_guideline_is_compliance_cap': False, 'issues': issues,
            'provider_usage_completeness': S.UNKNOWN, 'actual_subscription_charge': S.UNKNOWN,
            'actual_subscription_charge_currency': S.UNKNOWN, 'consumption_prevention_verified': False,
            'real_generation_authorised': False}
