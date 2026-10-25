"""Opportunity Scout scan V001: one operator command around the merged research pipeline.

It plans a new archive (or loads an existing, unclaimed plan such as Pilot 002), runs the same non-dispatch
preflight that the run itself performs, prints one confirmation, and only after the owner confirms that exact plan
hash writes the owner authorisation from the plan's own template and calls the unchanged pipeline once.

Everything research-relevant is delegated: planning, prompts, archive, generation runner, critic preparation,
providers, spend reservations, policy and report stay in ``automation_v001`` / ``exploratory_v001``. This module adds
no retry, resume, substitution or approval of its own. API keys are only checked for presence in the named
environment variable; their values are never read, written or printed here.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import time

from src.research.spec import digest
from .. import claude_subscription as CS, schema as S
from ..automation_v001 import pipeline as P, providers as V
from ..exploratory_v001 import runner as X
from ..post_generation.review import ASSISTANT
from ..storage import Archive, ROOT, input_json

VERSION = 'SCOUT_SCAN_V001'
CONFIG_V = 'SCOUT_SCAN_CONFIG_V001'
SCOUT = ROOT / '.research' / 'opportunity_scout'
CONFIG = SCOUT / 'scan-config.json'
RECORDS = SCOUT / 'scan-v001'
# Pilot 001 (claude-opus-5-5, effort medium): 4,675 output tokens for two cards, 436 of them thinking.
OBSERVED_TOKENS_PER_CARD = 2120
TYPICAL_REQUEST_BYTES = 25000  # Pilot 001 frozen critic requests were 24.5-24.8 KB
DISCLOSURE = ('The frozen FORGE prompt goes to Anthropic (generation). Each generated card, blinded, with a summary of '
              'the other card in the batch and the frozen critic rubric, goes to OpenAI (Codex) and Google (Gemini). '
              'No seeds, memory, source passages, research originals, account files or API keys are included.')
ONE_SHOT = ('The attempt and every critic request are claimed before dispatch and never retried, resumed or '
            'substituted. Any failure after the claim (budget overrun, provider fault, crash) is recorded, not re-run.')


def owner_ok(name):
    return isinstance(name, str) and name.strip() and not ASSISTANT.search(name) and name.strip().upper() not in ('UNKNOWN', 'OWNER')


def load_config(path=CONFIG):
    return validate_config(input_json(Path(path)), path)


def validate_config(c, path=CONFIG):
    if c.get('schema') != CONFIG_V:raise S.ScoutError(f'scan configuration {path} is not {CONFIG_V}; run configure first')
    if not owner_ok(c.get('owner')):raise S.ScoutError('configuration owner must be a named human, not an assistant or model')
    subs = c.get('allowed_subscription_types')
    if not isinstance(subs, list) or not subs or any(s not in X.SUBSCRIPTIONS for s in subs):raise S.ScoutError(f'allowed subscriptions are from {X.SUBSCRIPTIONS}')
    if c.get('account_fingerprint_sha256') != 'NOT_PINNED':S.validate(S.HASH, c.get('account_fingerprint_sha256'), 'account fingerprint')
    for k in ('model', 'effort', 'max_output_tokens_per_request', 'timeout_seconds', 'executable'):
        if k not in c.get('generator', {}):raise S.ScoutError(f'configuration generator needs {k}')
    for k in ('scientific', 'economic', 'codex_home', 'critic_timeout_seconds', 'default_count', 'default_spend_cap_usd', 'quiet_seconds'):
        if k not in c:raise S.ScoutError(f'configuration needs {k}')
    date.fromisoformat(c['prices_valid_until'])
    return c


def configure(path, *, owner, from_plan, prices_valid_until, default_count=2, default_spend_cap_usd=1.0,
              allowed_subscription_types=('pro',), account_fingerprint_sha256='NOT_PINNED', quiet_seconds=20, replace=False):
    """One-time local settings, copied from an existing reviewed pipeline plan. Holds no secret: only the name of the
    environment variable that will carry the Gemini key."""
    p = P.load_plan(Archive(from_plan))
    gen = p['generation_authorisation_template']
    roles = {r: {k: v for k, v in p['roles'][r].items() if k != 'executable_sha256'} for r in P.ROLES}
    c = {'schema': CONFIG_V, 'owner': owner, 'allowed_subscription_types': list(allowed_subscription_types),
         'account_fingerprint_sha256': account_fingerprint_sha256,
         'generator': {k: gen[k] for k in ('model', 'effort', 'max_output_tokens_per_request', 'timeout_seconds', 'executable')},
         'scientific': roles['SCIENTIFIC'], 'economic': roles['ECONOMIC'], 'codex_home': p['codex_home'],
         'critic_timeout_seconds': p['critic_timeout_seconds'], 'default_count': default_count,
         'default_spend_cap_usd': default_spend_cap_usd, 'prices_valid_until': prices_valid_until, 'quiet_seconds': quiet_seconds,
         'copied_from_plan_sha256': p['plan_sha256']}
    validate_config(c, path)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w' if replace else 'x', encoding='utf-8', newline='\n') as f:f.write(json.dumps(c, indent=2, ensure_ascii=False) + '\n')
    return c


def prepare(cfg, *, count=None, spend_cap_usd=None, root=SCOUT, host=None, now=None):
    """A new plan-specific archive; an existing path is never reused or overwritten."""
    stamp = (now or (lambda: datetime.now(timezone.utc)))().strftime('%Y%m%dT%H%M%SZ')
    store = Path(root) / f'scout-scan-{stamp}'
    if store.exists() or P.workspace_path(store).exists():raise S.ScoutError(f'{store.name} already exists; plans are never overwritten')
    count = cfg['default_count'] if count is None else count
    P.plan(store, title=f'Opportunity Scout scan {stamp}', generator={**cfg['generator'], 'count': count},
           scientific=dict(cfg['scientific']), economic=dict(cfg['economic']),
           spend_cap_usd=cfg['default_spend_cap_usd'] if spend_cap_usd is None else spend_cap_usd,
           codex_home=cfg['codex_home'], critic_timeout_seconds=cfg['critic_timeout_seconds'], host=host or P.Host())
    return store


def check(store, cfg, *, host=None, sleep=time.sleep, today=None):
    """The run's own non-dispatch checks, before anything is claimed. Starts only the administrative commands the run
    itself starts (Claude --version/--help/auth status; Codex --version/login status/exec --help); never a model."""
    host = host or P.Host(); blockers, warnings = [], []
    archive = Archive(store); state = archive.load(); ex = archive.path / 'exports'
    p = P.load_plan(archive)
    claims = sorted(x.name for x in ex.glob('*claim*'))
    if claims or P.status(store)['claimed']:blockers.append('ALREADY_CLAIMED: this one-shot plan was started; it is never re-run')
    try:g, prompt = X.load_plan(archive, state)
    except S.ScoutError as error:return {'ready': False, 'blockers': blockers + [f'GENERATION_PLAN: {error}'], 'warnings': [], 'summary': None}
    count = prompt['count']
    generator = {'model': g['model'], 'effort': g['effort'], 'cards': count, 'binary_sha256': g['binary_sha256']}
    if CS.file_hash(Path(g['executable'])) != g['binary_sha256']:blockers.append('CLAUDE_EXECUTABLE_CHANGED since planning')
    else:
        try:
            facts = X.preflight(host.generation, g, {'allowed_subscription_types': cfg['allowed_subscription_types'],
                                                     'account_fingerprint_sha256': cfg['account_fingerprint_sha256']},
                                CS.discover(g['executable']), X.environment(host.generation, g['effort'], g['max_output_tokens_per_request']))
            generator.update(cli_version=facts['cli_version'], account={k: v for k, v in facts['account'].items() if k != 'configDirectory'})
        except S.ScoutError as error:blockers.append(f'CLAUDE_PREFLIGHT: {error}')
    critics = {}
    for name, role in p['roles'].items():
        c = {'provider': role['provider'], 'model': role['model']}
        if role['provider'] == V.CODEX:
            c.update(effort=role['effort'], identity='REQUESTED_ONLY (accepted in the plan)' if role['accept_requested_identity'] else 'must be observed',
                     executable_sha256=role['executable_sha256'])
            tally = {'launches': 0, 'started': 0}; admin = P.codex_admin(host, tally)
            try:
                env = V.codex_environment(host.environ, p['codex_home'])
                c.update(V.codex_preflight(lambda a: admin(role['executable'], env, a), role['executable_sha256'], CS.file_hash(Path(role['executable']))))
            except (S.ScoutError, OSError) as error:blockers.append(f'{name}_CODEX_PREFLIGHT: {error}')
        elif role['provider'] == V.GEMINI:
            present = bool(host.environ.get(role['api_key_env']))  # presence only; the value is never read here
            c.update(thinking_level=role.get('thinking_level'), max_output_tokens=role['max_output_tokens'],
                     prices=role['prices'], prices_valid_until=cfg['prices_valid_until'], key_variable=role['api_key_env'], key_present=present)
            if not present:blockers.append(f'{name}_KEY_ABSENT: set {role["api_key_env"]} (the scout.ps1 shortcut loads it from the encrypted store)')
            if (today or date.today()) > date.fromisoformat(cfg['prices_valid_until']):blockers.append('GEMINI_PRICES_EXPIRED: re-check prices and plan again')
            per = P.reservation_micro_usd(TYPICAL_REQUEST_BYTES, role['max_output_tokens'], role['prices'])
            c['worst_case_reservation_usd_per_request'] = per / 1e6
            if per * count > int(p['spend_cap_usd'] * 10 ** 6):blockers.append(f'SPEND_CAP_TOO_LOW: {count} requests need about USD {per * count / 1e6:.2f} of reservation')
        else:blockers.append(f'{name}_PROVIDER_UNAVAILABLE: {role["provider"]}')
        critics[name] = c
    if count * OBSERVED_TOKENS_PER_CARD > state.batch['max_output_tokens'] * 0.9:
        warnings.append(f'GENERATION_BUDGET_RISK: {count} cards at about {OBSERVED_TOKENS_PER_CARD} tokens each (Pilot 001) '
                        f'approach or exceed the frozen {state.batch["max_output_tokens"]}-token batch budget; an overrun is ERROR with no cards')
    # The generation runner stops the run if these development-account files change during generation
    # (DEVELOPMENT_ACCOUNT_METADATA_CHANGED). Observe them for a short window instead of requiring every session closed.
    before = X.account_files(host.generation); sleep(cfg['quiet_seconds']); after = X.account_files(host.generation)
    changed = sorted(n for n in before if before[n] != after[n])
    if changed:blockers.append('DEVELOPMENT_ACCOUNT_FILES_CHANGING: ' + ', '.join(changed) + ' changed during the quiet check; '
                               'a Claude Code session is writing them and the runner would stop the run. Pause it and check again.')
    gemini = [r for r in p['roles'].values() if r['provider'] == V.GEMINI]
    summary = {'scan': VERSION, 'archive': str(archive.path), 'batch': state.batch['id'], 'plan_sha256': p['plan_sha256'],
               'generation_plan_sha256': g['plan_sha256'], 'prompt': {'version': prompt['prompt_version'], 'lane': prompt['lane'],
               'sha256': prompt['sha256'], 'seeds': len(prompt['context']['seeds']), 'memory': len(prompt['context']['memory'])},
               'generator': generator, 'critics': critics,
               'requests': {'generation_cli_processes': 1, 'critic_requests_maximum': p['critic_requests_maximum'],
                            'gemini_requests_maximum': count * len(gemini), 'attempts_per_request': 1, 'adversarial': 'never dispatched'},
               'spend': {'gemini_reservation_cap_usd': p['spend_cap_usd'], 'note': 'a software reservation limit at documented prices, '
                         'never a charge or a provider limit; billing can lag; Claude and Codex use subscriptions (charges UNKNOWN)'},
               'disclosure': DISCLOSURE, 'one_shot': ONE_SHOT}
    return {'ready': not blockers, 'blockers': blockers, 'warnings': warnings, 'summary': summary}


def authorisation(store, cfg, now):
    """The owner authorisation, built from the plan's own template with the configured owner and the actual time,
    then validated by the pipeline's and runner's own checks before it is written."""
    archive = Archive(store); state = archive.load()
    p = P.load_plan(archive); g, _ = X.load_plan(archive, state)
    t = input_json(archive.path / 'exports' / 'pipeline-authorisation-TEMPLATE.json')
    moment = now().isoformat(timespec='seconds')
    owner = cfg['owner'].strip()
    gen = {**t['generation'], 'owner': owner, 'approved_at': moment, 'hosted_transmission_approved': True,
           'allowed_subscription_types': list(cfg['allowed_subscription_types']), 'account_fingerprint_sha256': cfg['account_fingerprint_sha256']}
    value = {**t, 'generation': gen, 'owner': owner, 'approved_at': moment, 'hosted_transmission_approved': True,
             'gemini_prepaid_auto_reload_disabled': any(r['provider'] == V.GEMINI for r in p['roles'].values())}
    P.check_authorisation(value, p); X.check_authorisation(gen, g)
    return value


def run(store, cfg, confirm, *, channel, host=None, records=RECORDS, now=None, sleep=time.sleep, today=None):
    """After the owner confirms this exact plan hash: re-check, write the authorisation and confirmation records outside
    the archive (create-only), then call the unchanged pipeline once. Nothing here retries or starts another run."""
    now = now or (lambda: datetime.now().astimezone())
    result = check(store, cfg, host=host, sleep=sleep, today=today)
    if result['blockers']:raise S.ScoutError('NOT STARTED, preflight blocked: ' + ' | '.join(result['blockers']))
    summary = result['summary']
    if confirm != summary['plan_sha256']:raise S.ScoutError('NOT STARTED: the confirmation does not name this exact plan hash')
    value = authorisation(store, cfg, now)
    folder = Path(records) / Path(store).name; folder.mkdir(parents=True, exist_ok=True)
    def create(name, data):
        path = folder / name
        with path.open('x', encoding='utf-8', newline='\n') as f:json.dump(data, f, indent=2, ensure_ascii=False); f.write('\n')
        return path
    try:path = create('authorisation.json', value)
    except FileExistsError:raise S.ScoutError('NOT STARTED: an authorisation for this plan already exists; a plan is run once') from None
    create('confirmation.json', {'schema': VERSION + '_CONFIRMATION', 'plan_sha256': summary['plan_sha256'], 'archive': summary['archive'],
                                 'owner': value['owner'], 'confirmed_at': value['approved_at'], 'channel': channel,
                                 'attested': ['hosted transmission of the frozen prompt and generated cards to the listed providers',
                                              'requested-only Codex identity where the plan accepts it', 'one-shot risk and the generation budget',
                                              'Gemini prepaid auto-reload disabled and balance covering the reservation cap'],
                                 'summary_sha256': digest(summary), 'authorisation_sha256': digest(value)})
    outcome, error = None, None
    try:outcome = P.run(store, path, host=host or P.Host())
    except BaseException as caught:  # recorded truthfully, never retried; status below reads the recorded files
        error = type(caught).__name__ + (f': {caught}' if isinstance(caught, S.ScoutError) else '')
        if not isinstance(caught, (S.ScoutError, OSError, ValueError, KeyError, TypeError)):raise
    finally:
        st = P.status(store)
        create('result.json', {'schema': VERSION + '_RESULT', 'plan_sha256': summary['plan_sha256'], 'recorded_at': now().isoformat(timespec='seconds'),
                               'pipeline_outcome': (outcome or {}).get('outcome', st['outcome']), 'error': error, 'claimed': st['claimed'],
                               'finished': st['finished'], 'stages': st['stages'], 'accounting': st['accounting']['totals']})
    return {'outcome': (outcome or {}).get('outcome', st['outcome']), 'error': error, 'records': str(folder)}
