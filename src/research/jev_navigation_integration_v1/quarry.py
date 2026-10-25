"""Compose explicitly supplied validated exports; no source discovery or new evidence claims."""
from copy import deepcopy
from src.research.spec import digest
from src.research.jev_navigation_v1 import contracts as K, navigation as N
from src.research.quarry_v1 import evidence as Q, io

COLLECTION = 'QUARRY_JEV_COLLECTION_MANIFEST_V001'


def combined(exports):
    inputs = [io.json_file(e['input']) for e in exports]
    first = inputs[0]
    K.need(all(i['subject'] == first['subject'] and i['data_classification'] == first['data_classification'] for i in inputs),
           'collection requires the same exact question and data classification')
    documents = []
    for index, value in enumerate(inputs):
        for original in value['documents']:
            document = deepcopy(original)
            ref = document['citation']['artifact']
            K.need(ref['base'] == 'INPUT', 'Quarry collection requires portable INPUT citations')
            ref['path'] = f'packages/P{index:02d}/' + ref['path']
            documents.append(document)
    K.need(len({d['id'] for d in documents}) == len(documents), 'collection excerpt IDs must be distinct; re-export with explicit distinct IDs')
    data = {**first, 'documents': documents}
    K.validate(K.input_schema('EVIDENCE_PROSPECTOR'), data)
    return data


def compose(export_paths, out):
    K.need(1 <= len(export_paths) <= 32, 'explicit bounded list of Quarry exports required')
    exports = [Q.validate_export(p) for p in export_paths]
    data = combined(exports)
    # Enforce existing request bounds before making the final collection usable.
    root = io.new_directory(out, prefix='jev-provider-v1-')
    io.write(root / 'claim.json', {'schema': 'QUARRY_JEV_COLLECTION_CLAIM_V001', 'authorises': []})
    (root / 'packages').mkdir()
    files, entries = ['claim.json', 'collection.json', 'input.json'], []
    for index, (source, checked) in enumerate(zip(export_paths, exports)):
        directory = f'packages/P{index:02d}'
        target = root / directory; target.mkdir()
        for name in [*checked['manifest']['files'], 'manifest.json']:
            dest = io.child(target, name); dest.parent.mkdir(parents=True, exist_ok=True)
            io.write(dest, io.read(io.child(source, name)), raw=True)
            files.append(directory + '/' + name)
        entries.append({'directory': directory, 'manifest_sha256': digest(checked['manifest'])})
    io.write(root / 'collection.json', {'schema': 'QUARRY_JEV_COLLECTION_V001', 'exports': entries, 'authorises': []})
    io.write(root / 'input.json', data)
    N.derive(root / 'input.json')
    io.seal(root, files, COLLECTION)
    return validate(root)


def validate(root):
    root = io.safe_path(root)
    manifest = io.json_file(root / 'manifest.json')
    if manifest.get('schema') != COLLECTION:
        return Q.validate_export(root)
    manifest = io.verify_seal(root, COLLECTION)
    metadata = io.json_file(root / 'collection.json')
    K.need(set(metadata) == {'schema', 'exports', 'authorises'} and metadata['schema'] == 'QUARRY_JEV_COLLECTION_V001'
           and metadata['authorises'] == [] and 1 <= len(metadata['exports']) <= 32, 'invalid collection')
    exports, expected_files = [], {'claim.json', 'collection.json', 'input.json'}
    for index, entry in enumerate(metadata['exports']):
        directory = f'packages/P{index:02d}'
        K.need(set(entry) == {'directory', 'manifest_sha256'} and entry['directory'] == directory, 'collection namespace changed')
        checked = Q.validate_export(io.child(root, directory))
        K.need(entry['manifest_sha256'] == digest(checked['manifest']), 'collection source version changed')
        exports.append(checked)
        expected_files.update(directory + '/' + name for name in [*checked['manifest']['files'], 'manifest.json'])
    K.need(set(manifest['files']) == expected_files and io.json_file(root / 'input.json') == combined(exports), 'collection universe, citations or restrictions changed')
    K.need(io.json_file(root / 'claim.json') == {'schema': 'QUARRY_JEV_COLLECTION_CLAIM_V001', 'authorises': []}, 'collection claim changed')
    return {'manifest': manifest, 'input': root / 'input.json', 'bundle': N.derive(root / 'input.json'), 'authorises': []}
