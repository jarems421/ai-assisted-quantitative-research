"""Source-only general title-variant review; preserve first-parser unknowns."""
import hashlib
import json
import re

from src.research.item202_date_bound import FilingText, confusion
from src.research.item202_date_repair import DOCS, RAW, write_public
from src.research.sec_pilot.acquisition import Archive
from src.research.spec import digest

TITLE_RULE = (r'\bItem\s*2\s*\.\s*02[\s.\-:\u2014\u2013]*'
              r'(?:Disclosure\s+of\s+)?Results\s+of\s+Operations?\s+and\s+Financial\s+Condition\b')


def inspect(body):
    parser = FilingText()
    parser.feed(body.decode('utf-8', errors='strict'))
    text = re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()
    heading = re.search(TITLE_RULE, text, re.I)
    if heading:
        return {'present': True, 'heading': heading.group(),
                'normalized_text_locator': [heading.start(), heading.end()],
                'normalized_text_sha256': hashlib.sha256(text.encode()).hexdigest()}
    if re.search(r'\bItem\s*2\s*\.\s*02\b', text, re.I):
        return {'present': None, 'reason': 'Reference without supported heading'}
    if re.search(r'\bItem\s*[1-9]\s*\.\s*\d{2}\b', text, re.I):
        return {'present': False, 'reason': 'Recognizable other items; no Item2.02 reference',
                'normalized_text_sha256': hashlib.sha256(text.encode()).hexdigest()}
    return {'present': None, 'reason': 'No recognizable item structure'}


def review():
    first = json.loads((DOCS/'exp006_primary_validation_v003.json').read_bytes())
    rows=[]
    for row in first['records']:
        r = dict(row)
        if r.get('receipt', {}).get('status') == 200:
            body = Archive(RAW/'primary').read(r['receipt']['body'])
            observation = inspect(body)
            r.update(primary_observation=observation, primary_present=observation['present'],
                     first_parser_status=row['status'])
            r['status'] = 'SOURCE_HEADING_CONFIRMED' if observation['present'] is not None else 'UNKNOWN_PRIMARY'
            if observation['present'] is not None and observation['present'] != r['header_present']:
                r.update(status='HEADER_PRIMARY_DISAGREEMENT', primary_present=None)
        rows.append(r)
    counts=confusion(rows)
    passed=counts['sample_size']==96 and counts['FP']==counts['FN']==counts['UNKNOWN']==0
    result={'version':'EXP006_primary_title_variant_review_v001',
            'status':'SCOPED_ITEM202_CLASSIFICATION_PASS' if passed else 'ITEM202_CLASSIFICATION_BLOCKED',
            'first_parser_evidence_sha256':digest(first), 'first_parser_result_retained':True,
            'rule':TITLE_RULE,'implementation_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
            'review_basis':'Five original source headings differ only by Disclosure of prefix, Operation singular, or Unicode dash. General rule reruns every frozen source; no accession-specific override, sample replacement, feature change or market outcome.',
            'source_selected_not_blind_holdout':True,'sample_certifies':'Current label/header/primary concordance in 96 fixed records; not full-population historical version/deletion completeness or independent classifier generalization.',
            **counts,'records':rows,'performance_evaluations':0,'confirmation_accesses':0}
    write_public('exp006_primary_title_review_v003.json',result)
    return {k:result[k] for k in ('status','TP','TN','FP','FN','UNKNOWN','coverage')}


if __name__ == '__main__': print(review())
