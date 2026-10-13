"""Versioned final House source gate, public regeneration and private replay."""
from collections import Counter
import argparse,hashlib,json
from src.research.spec import ROOT,digest
from src.research.phase3c.sources import put
from src.research.congress_sprint_source import DOCS,RAW as PRIOR
from src.research.congress_originals import select_original_row,normalized
from src.research.house_source_validation import parse_ocr_rows,compare,evaluate_gate,FIELDS,associate_ocr_row

RAW=ROOT/'data/raw/exp007_house_v002'
CONTRACT=DOCS/'exp007_design_candidate_v002.json'
CERT=DOCS/'exp007_house_source_certificate_v002.json'
REPORT=DOCS/'exp007_house_repair_report.md'


def verify_projection(projection,folder):
    if projection['evidence_tier']!='DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL' or not projection['network_disabled']:raise ValueError('OCR provenance invalid')
    for page in projection['pages']:
        if not re_full_render_name(page['render_path']):raise ValueError('Render path escape')
        if hashlib.sha256((folder/page['render_path']).read_bytes()).hexdigest()!=page['render_sha256']:raise ValueError('Render changed')
        if hashlib.sha256(page['text'].encode()).hexdigest()!=page['text_sha256']:raise ValueError('OCR text changed')
    return True


def re_full_render_name(name):
    import re
    return bool(re.fullmatch(r'page_\d{3,}\.png',name))


def review():
    sample=json.loads((DOCS/'exp007_original_validation_sample.json').read_bytes())
    contract=json.loads(CONTRACT.read_bytes());house=[r for r in sample['records'] if r['trade_key'][0]=='house']
    if digest(house)!=contract['house_sample_sha256']:raise ValueError('Frozen sample changed')
    old=json.loads((PRIOR/'original_field_validation_v002.json').read_bytes());oldmap={tuple(r['trade_key']):r for r in old['records']}
    acq={r['source_url']:r for r in json.loads((PRIOR/'original_acquisition_result.json').read_bytes())['records']}
    from src.research.congress_sprint_review import corpus
    trades={tuple((r['chamber'],r['doc_id'],r['row_index'])):r for r in corpus(range(2014,2022))['political_trades'] if r['chamber']=='house'}
    cache={};records=[]
    for r in house:
        prior=oldmap[tuple(r['trade_key'])];record=dict(prior,year=r['available_at'][:4],printed_present=bool(r['printed_ticker']),amendment=r['amended_version_source'])
        record['actual_action']=r['action'] if prior['fields']['transaction_type']=='AGREE' else None
        record['projection_type']='PRIOR_TEXT'
        if prior['fields']['transaction_type']=='UNKNOWN':
            source=acq[r['source_url']];ref=source['receipt']['body'];source_path=ROOT/source['source_root']/ref['path']
            if hashlib.sha256(source_path.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Original changed')
            folder=RAW/'ocr'/ref['sha256'];projection=json.loads((folder/'projection.json').read_bytes());verify_projection(projection,folder)
            if projection['source_sha256']!=ref['sha256']:raise ValueError('OCR source lineage mismatch')
            if ref['sha256'] not in cache:
                images={}
                def render_loader(page,tokens):
                    from PIL import Image
                    # The parser's normalized coordinates reveal the same
                    # dominant-axis rotation used by orient_tokens.
                    from src.research.house_source_validation import orient_tokens
                    original=page['tokens'];vertical=sum(len(t['text'])>=4 and max(b[1] for b in t['box'])-min(b[1] for b in t['box'])>max(b[0] for b in t['box'])-min(b[0] for b in t['box']) for t in original)
                    horizontal=sum(len(t['text'])>=4 for t in original)-vertical
                    if page['page'] not in images:
                        im=Image.open(folder/page['render_path'])
                        images[page['page']]=im.rotate(90,expand=True) if vertical>horizontal else im.copy()
                        im.close()
                    return images[page['page']]
                cache[ref['sha256']]=(projection,parse_ocr_rows(projection,render_loader))
                for image in images.values():image.close()
            projection,rows=cache[ref['sha256']];actual=associate_ocr_row(r,rows)
            fields=compare(r,actual)
            # Retain uncertain OCR values, but do not certify low-confidence text.
            if actual and actual['minimum_confidence']<0.8:fields={k:'UNKNOWN' for k in FIELDS}
            full=' '.join(p['text'] for p in projection['pages']);trade=trades[tuple(r['trade_key'])]
            if r['trade_key'][1] in full:fields['document_identity']='AGREE'
            first=normalized(trade.get('filer_first') or '');last=normalized(trade.get('filer_last') or '')
            if first and last and first in normalized(full) and last in normalized(full):fields['member_identity']='AGREE'
            record.update(fields=fields,actual_action=actual['action'] if actual and actual['minimum_confidence']>=.8 else None,
                projection_type='LOCAL_OCR',source_locator=actual['source_locator'] if actual else None,
                OCR_projection_sha256=digest(projection),reason='SOURCE_BLIND_TABLE_OCR_AND_ASSET_ASSOCIATION; UNCERTAIN_VALUES_UNKNOWN',
                actual_source_row=actual)
        records.append(record)
    gate=evaluate_gate(records,contract)
    value={'version':'EXP007_house_original_validation_v002','contract_sha256':digest(contract),'records':records,
        'records_sha256':digest(records),'gate':gate,'prior_text_decisive':27,'OCR_observations':34,'OCR_documents':len(cache),
        'field_results':{f:dict(Counter(r['fields'][f] for r in records)) for f in FIELDS},'performance_evaluations':0,'confirmation_outcome_accesses':0}
    put(RAW/'source_review_v002.json',value)
    return value


def certify():
    value=review();scope=json.loads((DOCS/'exp007_house_ocr_scope.json').read_bytes())
    docs=[]
    for sha in scope['source_hashes']:
        folder=RAW/'ocr'/sha;p=json.loads((folder/'projection.json').read_bytes());verify_projection(p,folder)
        docs.append({'source_sha256':sha,'projection_sha256':digest(p),'pages':len(p['pages']),
                     'renders':[{'page':x['page'],'render_sha256':x['render_sha256'],'text_sha256':x['text_sha256']} for x in p['pages']]})
    output={k:value[k] for k in ('version','contract_sha256','gate','prior_text_decisive','OCR_observations','OCR_documents','field_results','performance_evaluations','confirmation_outcome_accesses')}
    output.update(private_review_sha256=digest(value),documents=docs,total_OCR_pages=sum(d['pages'] for d in docs),
        code_hashes={n:hashlib.sha256((ROOT/'src/research'/n).read_bytes()).hexdigest() for n in ('house_ocr.py','house_source_validation.py','house_repair_report.py')},
        dependency_inventory_sha256=hashlib.sha256((DOCS/'exp007_house_ocr_inventory.json').read_bytes()).hexdigest(),
        scientific_source_requests=0,senate_requests=0,market_provider_requests=0,registered=False,frozen=False,
        remaining_gates='NOT_RUN_UPSTREAM_SOURCE_STOP' if value['gate']['verdict']=='ABANDON_EXP007_SOURCE_FEASIBILITY' else 'CONTINUATION_REQUIRED',
        model_hashes=json.loads((RAW/'ocr'/scope['source_hashes'][0]/'projection.json').read_bytes())['model_hashes'])
    put(CERT,output);return output


def report(check=False):
    c=json.loads(CERT.read_bytes());g=c['gate'];vpath=DOCS/'exp007_house_validation.json';v=json.loads(vpath.read_bytes()) if vpath.exists() else {}
    if g['verdict']!='ABANDON_EXP007_SOURCE_FEASIBILITY':raise ValueError('Source passed mechanically; cluster review and authorized continuation required, no false stop report')
    fields='\n'.join(f"| {f.replace('_',' ')} | {c['field_results'][f].get('AGREE',0)} | {c['field_results'][f].get('DISAGREE',0)} | {sum(n for k,n in c['field_results'][f].items() if k not in ('AGREE','DISAGREE'))} |" for f in FIELDS)
    clusters='\n'.join(f"| {name} | {label} | {x['total']} | {x['unresolved']} |" for name,part in g['unresolved_clusters'].items() for label,x in part.items())
    text=f'''# EXP007 final House-only original-source repair

**{g['verdict']}. House source gate fails; economic hypothesis untested.** Starting HEAD `7451373705b09f152107a88af69aec4ee2199cf5`, as of 2026-10-13. [Owner instruction](owner_exp007_house_repair_2026-10-13.md) authorized one final pre-performance House-only revision, with mandatory abandonment if the frozen source criteria failed. No experiment was registered or frozen.

## Fixed source revision and bounded repair

[Design v002](exp007_design_candidate_v002.json) restricts the estimand to source-resolved House common-equity purchase disclosures versus SPY over 20 sessions. This source-access revision precedes all market outcomes; it does not select members, parties, amounts, sectors or returns. The earlier [House/Senate report](exp007_source_validation_report.md), 96-row sample, schema/snapshot receipts, original PDFs/projections and Senate 403 remain unchanged. Senate observations are outside v002, not House failures. No Senate request or access workaround occurred.

All **61 existing House observations** remain, with no replacements. **27** had decisive text-source validation before repair. OCR attempted the other **34 observations across {c['OCR_documents']} cached official PDFs**, processing {c['total_OCR_pages']} pages. Full transaction documents were projected because the archived image-only PDFs supply no reliable text page index; source geometry alone drives row extraction. No expected asset, ticker, action or date is supplied to the OCR worker. A general parser extracts rows first; association uses source asset/printed-symbol evidence, then independently compares action/date. Ambiguous associations and low-confidence OCR remain UNKNOWN.

The isolated pipeline uses RapidOCR 3.4.0, ONNX Runtime 1.23.2, pypdfium2 4.30.0 and packaged local models. Four local processes partition the fixed documents; each uses one CPU inference thread and identical settings. Render hashes, page numbers, token boxes/confidences, source hashes, model/configuration and projection hashes are retained privately. OCR is **DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL**, not a new primary source. [Wheel lock](exp007_house_ocr_requirements.lock), [licence/notice inventory](exp007_house_ocr_inventory.json) and [canonical certificate](exp007_house_source_certificate_v002.json) preserve reproduction evidence. Canonical research requirements are unchanged. Rendering follows the [pypdfium2 API](https://pypdfium2.readthedocs.io/en/v4/python_api.html); engine provenance is [RapidOCR](https://github.com/RapidAI/RapidOCR).

The first offline setup caught the library's automatic visualization-font fetch at the socket guard; no projection completed. It was corrected to use a local Windows Arial font, which does not influence recognition. The failed setup log and initial render remain retained. No cloud OCR, LLM transcription or external OCR request occurred. Local dependency downloads and official software-documentation review are separate from scientific source calls.

## Frozen source gate

The criteria were committed and pushed in `deae95a` before OCR: at least **55/61** decisive type/date/asset rows; zero confirmed purchase/non-purchase disagreements; decisive date/type agreement at least 98% and normalized asset agreement at least 95%; no undermining systematic unresolved cluster. No threshold was relaxed.

**Final decisive rows: {g['decisive']}/61; unresolved core validation: {g['unknown']}/61.** Confirmed purchase/non-purchase disagreements: {g['purchase_nonpurchase_disagreements']}. The decisive minimum {'passes' if g['checks']['decisive_minimum'] else 'fails'}. Field-specific unknowns remain explicit:

| Field | Agree | Disagree | Unknown |
| --- | ---: | ---: | ---: |
{fields}

Printed ticker is compared only when original evidence supports it; a resolver-corrected symbol is never required to appear in a filing. Member/document identity are reported separately from the three mandatory transaction fields. An UNKNOWN is not a source disagreement, a non-purchase or zero activity. This result does not prove upstream purchases are materially misclassified or that every original is unreadable.

| Unresolved cluster dimension | Group | Frozen observations | Core unresolved |
| --- | --- | ---: | ---: |
{clusters}

These retained clusters describe extraction missingness, not market outcomes. The mechanical source gate fails independently of a favorable interpretation of cluster patterns; no downstream source-resolved trading population is certified.

## Final stop and verification

**Abandon EXP007 as a source-feasibility candidate.** No third source repair, fresh sample, reduced thresholds, modern-year restriction, Senate retry, alternate original route or new OCR provider follows. The predictive economic hypothesis remains untested. Provider/class/path certification, actual event aggregation, market sessions/prices, inference calibration, synthetic power, Proof, spec, freeze and Development are **NOT_RUN**. There is no effect, interval, p-value or materiality verdict. The 8-evaluation ceiling remains untouched; performance evaluations and confirmation outcome accesses are **0**.

Scientific source starts: **0**; Senate **0**; provider/identity/Nexus/Aurora **0**. Only cached originals were used; no purchase or upgrade. Account-wide debit is UNKNOWN. Source geometry keeps Development 2014–2021 and owner-held confirmation 2022–2025 as prior planning boundaries; no stage was opened or shortened to improve coverage. Modeled EOD and second-later-session entry remain proposed contracts; exact public availability remains UNKNOWN, no trading eligibility view was activated.

Validation: **{v.get('local_tests_passed','pending')} local tests, {v.get('public_tests_passed','pending')} public tests, {v.get('tests_skipped','pending')} skipped**. [Receipt](exp007_house_validation.json). Public report regeneration reads tracked receipts; private audit verifies immutable PDFs, render/text hashes, blind extraction replay and the frozen 61-row frame. Public CI needs no OCR binary, private filing or network.

```sh
python -m src.research.house_repair_report --check
python -m src.research.house_repair_report --audit --check
python -m src.research.public_checks
python -m unittest discover -s tests -v
python -m src.presentation.exp001 --check
```

Recreate the isolated helper on CPython 3.13/Windows x86-64 with `python -m venv .research/exp007_house/ocr-env`, then its interpreter's `pip install --require-hashes -r docs/acceleration/exp007_house_ocr_requirements.lock`. Private OCR replay additionally needs the archived exact dispatch, original PDFs and local Arial font; no source acquisition command is included. Source hashes, parser code and model hashes identify this reconstruction, not contemporaneous ingestion or legal disclosure exhaustiveness.

EXP002–EXP006 remain closed to new research; EXP004 stays paused and EXP005/EXP006 abandoned/absent. Previous reports, raw bodies, frozen experiments, processed metrics and dependency pins are preserved. No paid provider, Phase 4B, optimizer or paper/live operation occurred. **Stopped under owner sections 8/25; no automatic next phase.** Commit/push and hosted CI are delivery receipts reported separately.
'''
    if check:
        if REPORT.read_bytes()!=text.encode():raise ValueError('House report differs')
    else:REPORT.write_bytes(text.encode())
    return g['verdict']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.build:print(certify()['gate'])
    if a.audit:
        c=json.loads(CERT.read_bytes());r=review()
        if digest(r)!=c['private_review_sha256']:raise ValueError('Source replay differs')
        print('Private source/render/row replay PASS')
    print(report(a.check))
