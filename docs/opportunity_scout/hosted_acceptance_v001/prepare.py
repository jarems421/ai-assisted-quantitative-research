"""Read-only fictional approval-review validator, never a CLI/model runner.

Run from repository root:
  python -m docs.opportunity_scout.hosted_acceptance_v001.prepare --check
--check is the only action; there is no generation or write interface.
Actual runtime, account, capture binding and approval deliberately remain UNBOUND.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from src.research.spec import canonical
from src.research.opportunity_scout import engine as E, fixtures as F, prompts, schema as S
from src.research.opportunity_scout import v004_package as legacy
from src.research.opportunity_scout.v004_r3 import package as P, policy, runtime

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = ROOT / 'docs/opportunity_scout/v004_hosted_readiness_v001.md'
MOMENT = '2026-10-20T00:00:00+00:00'
TEXTS = (
    'WHOLLY FICTIONAL INTERFACE FIXTURE. No real issuer or research source. '
    'The invented Alder Basin workshop summary lists 12 inspection shifts each week across three independent customer groups. '
    'Its fictional weekly demand entries are 8, 9, 8, 10, 14, 15, 13, 9 shifts. '
    'The fifth week includes an announced maintenance shutdown in one customer group. '
    'The summary describes a separate invoice-delay register, but supplies no register rows, customer assignments, prices or contracts. '
    'No observation identifies who receives scarce shifts, who bears delay costs, or when a real publication would have occurred. '
    'These invented numbers are source-description data only, not verified fields or evidence of an actual consequence.',
    'WHOLLY FICTIONAL INTERFACE FIXTURE. No real issuer or research source. '
    'The invented Merehaven reusable-container pool summary describes 10000 containers and a refundable deposit change from 4 to 7 fictional currency units per container. '
    'It lists eight weekly return counts: 900, 1100, 950, 1000, 920, 1080, 990, 1010. '
    'It mentions a separately maintained borrowing-invoice register but supplies no balances or lender terms. '
    'Ownership, named customer inventories, refunds, funding costs, allocation and publication clocks are unknown. '
    'A deposit balance is not an expense or a demonstrated borrowing change. All quantities and places in this summary are invented.'
)


def request():
    """Existing full-schema PLAIN instructions, wholly fictional eligible pool."""
    state = E.State()
    state.batch = {'knowledge_cutoff': MOMENT, 'fixture': 'SYNTHETIC', 'max_output_tokens': 6000,
                   'memory': {'recorded_at': MOMENT, 'investigations': {
                       'HIST-FICTIONAL-N1': {'id': 'HIST-FICTIONAL-N1',
                           'title': 'FICTIONAL closed machine-rental allocation question',
                           'requirements': ['REQ_DOCUMENTED_ALLOCATION'], 'findings': [],
                           'verdict': 'FICTIONAL_MEASUREMENT_NOT_ESTABLISHED', 'closed_source_routes': []}}}}
    for index, text in enumerate(TEXTS, 1):
        seed = F.seed()
        seed.update(id=f'SEED-FICTIONAL-N1-{index}', publisher=f'Fictional Interface Records Office {index}',
                    locator=f'synthetic://scout-hosted-interface-v001/source-{index}', text=text, sha256=S.hash_text(text),
                    limitations=['Entirely fictional descriptive summary; no original field, economic bearer, allocation, consequence or public clock is verified.'])
        S.validate_seed(seed); state.seeds[seed['id']] = seed
    made = prompts.make_prompt(state, 'PLAIN', 2, 'PROMPT-FICTIONAL-N1')
    # The inherited batch cap is audit-only in this legacy constructor. Exactly
    # the accepted projection drops it; no 6000 ceiling is sent or activated.
    return {k: copy.deepcopy(made[k]) for k in legacy.PROMPT_FIELDS}


def runtime_template():
    candidate = runtime.description('claude-opus-99-1', '0' * 64, 'UNBOUND-NOT-A-CLI-VERSION')
    for key in ('model', 'binary_sha256', 'cli_version'): candidate[key] = S.UNKNOWN
    return {'schema': 'SCOUT_NATIVE_VALIDATION_RUNTIME_TEMPLATE_V001',
            'status': 'UNBOUND_NOT_EXECUTABLE', 'candidate': candidate,
            'actual_python_dependencies': S.UNKNOWN, 'actual_binary_path': S.UNKNOWN,
            'research_config_path': S.UNKNOWN, 'observed_account_source': S.UNKNOWN,
            'session_uuid': S.UNKNOWN, 'sterile_directory': S.UNKNOWN,
            'approved_capture_path_and_reservation': S.UNKNOWN,
            'reviewed_collector_sha256': S.UNKNOWN, 'hosted_authorised': False}


def sha(data): return hashlib.sha256(data).hexdigest()


def documents():
    """Reconstruct expected artifacts in memory for read-only comparison."""
    protocol = S.json_loads((HERE / 'protocol.json').read_text(encoding='utf-8'))
    files = {'request.json': canonical(request()),
             'system-prompt.txt': runtime.SYSTEM_PROMPT.encode('utf-8'),
             'runtime-template.json': canonical(runtime_template())}
    inventory = {name: {'sha256': sha(data), 'representation': 'EXACT_UTF8_BYTES_NO_TRAILING_NEWLINE'} for name,data in files.items()}
    inventory['protocol.json'] = {'sha256': sha(canonical(protocol)), 'representation': 'CANONICAL_JSON_UTF8'}
    # Portable proposal source fingerprint, not a certificate for an installed
    # binary/runtime. A final bound launch package still requires raw file pins.
    paths = set(P.implementation()) | {Path(__file__).relative_to(ROOT).as_posix(), REPORT.relative_to(ROOT).as_posix()}
    sources = {name: sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) if (ROOT / name).exists()
               else 'ABSENT_NAMESPACE_PACKAGE' for name in sorted(paths)}
    manifest = {'schema': 'SCOUT_NATIVE_VALIDATION_REVIEW_MANIFEST_V001',
                'status': 'UNAPPROVED_UNBOUND_PROPOSAL', 'base_main': protocol['base_main'],
                'files': inventory, 'source_normalisation': 'CRLF_TO_LF', 'sources': sources,
                'resource_policy_sha256': policy.policy_hash(),
                'full_two_card_schema_sha256': sha(canonical(request()['response_schema'])),
                'stdin_sha256': sha(files['request.json']), 'stdin_bytes': len(files['request.json']),
                'byte_size_is_token_bound': False, 'collector_implemented': False,
                'execution_bindings_complete': False, 'hosted_authorised': False,
                'scientific_dispatch_authorised': False, 'authorises': []}
    files['manifest.json'] = canonical(manifest)
    return files


def check():
    for name, expected in documents().items():
        if (HERE / name).read_bytes() != expected:
            raise S.ScoutError('proposal differs; never refresh an approved package in place: ' + name)
    return {'status': 'PROPOSAL_BYTES_CHECKED_NOT_EXECUTABLE', 'hosted_authorised': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(check()))


if __name__ == '__main__': main()
