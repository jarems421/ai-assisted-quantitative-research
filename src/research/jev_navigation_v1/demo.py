"""Three executable offline examples. Real memory provenance; all classifications scripted."""
from pathlib import Path
from src.research.spec import canonical
from src.research.graph.catalogue import CATALOGUE_PATH
from src.research.graph.fixtures import campaign_a
from src.research.discovery.demo import Clock
from . import contracts as K, navigation as N, workspace as W
from .evaluation import at_budget

FIXTURES = N.ROOT / 'docs/jev_navigation_v001/fixtures'


def subject(**overrides):
    result = {'id': 'SYNTHETIC_F1', 'version': 1,
              'question': 'Does a binding reduction in terminal loading capacity precede lower independent shipments?',
              'predictor': 'F1 permitted daily loading limit', 'outcome': 'F1 next-quarter independently reported shipments',
              'unresolved_m': ['distinctive_predictor', 'separate_outcome', 'meaning_and_units', 'valid_join'],
              'concept_terms': ['terminal loading capacity shipments'], 'entity_ids': [], 'document_sha256': [], 'requirement_ids': []}
    result.update(overrides)
    return result


def evidence_input(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    cases = K.loads((FIXTURES / 'evidence_cases.json').read_bytes())
    records = []
    for case in cases['documents']:
        file = folder / (case['id'] + '.txt')
        W.write(file, case['text'].encode('utf-8'), raw=True)
        records.append({'id': case['id'], 'version': 'SYNTHETIC_V001', 'title': case['title'], 'source_id': 'SYN_' + case['id'],
                        'citation': {'artifact': {'base': 'INPUT', 'path': file.name, 'sha256': N.sha(file.read_bytes())},
                                     'location': case['id'] + ': full supplied passage', 'quote': case['text']},
                        'availability': case['availability'], 'original_sha256': 'UNKNOWN', 'limitations': ['Fictional source-content fixture, not an authentic original.']})
    data = {'schema': K.INPUT, 'task': K.TASKS[0], 'data_classification': 'SYNTHETIC', 'subject': subject(), 'documents': records}
    path = folder / 'input.json'
    W.write(path, data)
    return path


def memory_input(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=False)
    data = {'schema': K.INPUT, 'task': K.TASKS[1], 'data_classification': 'PUBLIC_REPOSITORY',
            'subject': subject(id='OFFLINE_OFFSHORE_QUESTION', question='Which earlier offshore decommissioning liability investigation lacked lease-level net obligation schedules?',
                               predictor='A proposed change in offshore decommissioning liability', outcome='Separately realised retained net payments',
                               concept_terms=['offshore liability decommissioning'], requirement_ids=['REQ_DOCUMENTED_ALLOCATION', 'REQ_RETAINED_NET_ECONOMICS']),
            'catalogue': N.ref(CATALOGUE_PATH.relative_to(N.ROOT))}
    path = folder / 'input.json'; W.write(path, data)
    return path


def workflow_input(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=False)
    ledger = campaign_a(folder / 'synthetic-campaign.jsonl', Clock())
    data = {'schema': K.INPUT, 'task': K.TASKS[2], 'data_classification': 'SYNTHETIC', 'subject': subject(),
            'context': {'ledger': {'base': 'INPUT', 'path': ledger.path.name, 'sha256': N.sha(ledger.path.read_bytes())},
                        'candidate_id': 'CAND-GA-1', 'candidate_version': 1, 'experiment_id': None, 'stops': [], 'context_files': []}}
    path = folder / 'input.json'; W.write(path, data)
    return path


def synthetic_response(bundle, script):
    answers = {}
    for key, member in bundle['request']['question_membership'].items():
        choice = script.get(member['record_id'], {}).get(member['category'], 'no')
        p = {c: .1 for c in K.CHOICES}; p[choice] = .8
        answers[key] = {'type': 'choice', 'choice': choice, 'probabilities': p, 'confidence': .7}
    return {'schema': K.SAVED, 'fixture': 'SYNTHETIC_NOT_MODEL_OUTPUT', 'request_sha256': bundle['request_sha256'],
            'response': {'model': 'SYNTHETIC_SCRIPTED_NOT_JEV', 'answers': answers, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}


def run(out):
    root = W.new_directory(out); root.mkdir(parents=True, exist_ok=False)
    scripts = K.loads((FIXTURES / 'scripted_choices.json').read_bytes())
    reports = {}
    for name, factory in (('evidence', evidence_input), ('memory', memory_input), ('workflow', workflow_input)):
        path = factory(root / name)
        workspace = path.parent / 'bundle'
        W.prepare(path, workspace)
        _, bundle = W.load(workspace)
        response = path.parent / 'synthetic-response.json'
        W.write(response, synthetic_response(bundle, scripts[name]))
        W.import_response(workspace, response)
        reports[name] = W.report(workspace)
        W.write(path.parent / 'navigation-report.json', reports[name])
    labels = K.loads((FIXTURES / 'evidence_labels.json').read_bytes())
    evaluation = at_budget(reports['evidence'], labels['labels'], 3)
    W.write(root / 'inspection-evaluation.json', evaluation)
    return {'schema': 'JEV_NAVIGATION_OFFLINE_DEMO_V001', 'fixture': 'SCRIPTED_NOT_JEV_PERFORMANCE',
            'out': str(root), 'evidence_order': [r['id'] for r in reports['evidence']['inspection_queue']],
            'memory_order': [r['id'] for r in reports['memory']['inspection_queue']],
            'workflow': {k: reports['workflow'][k] for k in ('effective_bottleneck', 'next_question', 'unsupported_model_bottlenecks')},
            'evaluation': evaluation, 'provider_activated': False, 'authorises': []}
