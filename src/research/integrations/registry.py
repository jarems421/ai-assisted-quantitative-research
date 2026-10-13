"""Validated external audit registry; scientific evidence never comes from a library."""
import re
STATUSES={'ADOPTED_RUNTIME','ADOPTED_SEMANTICS','ADOPTED_INTERFACE_PATTERN','EXISTING_DEPENDENCY','OPTIONAL_ADAPTER','DEFERRED_PHASE5','REFERENCE_ONLY','REJECTED'}
def validate_registry(rows):
    if len(rows)!=9 or len({r['name'] for r in rows})!=9:raise ValueError('Exact nine-repository audit required')
    for r in rows:
        if not re.fullmatch('[0-9a-f]{40}',r['pinned_audit_commit']) or r['integration_status'] not in STATUSES:raise ValueError('Unpinned or unknown integration')
        if not all(r.get(k) for k in ('repo','license','role','allowed_usage','forbidden_usage','reason','files_inspected')):raise ValueError('Audit provenance incomplete')
        if r['name'] in ('FinRL','OpenBB','scikit-learn','pandas') and r['runtime_dependency']:raise ValueError('Unused dependency not authorized')
        if r['canonical_evidence_role']!='NONE_LIBRARY_IS_NOT_PRIMARY_EVIDENCE':raise ValueError('Library promoted to evidence')
    return rows
