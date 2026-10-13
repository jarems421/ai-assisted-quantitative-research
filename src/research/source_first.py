"""SourceResearchabilityContract and bounded probes; no hypothesis/performance runner."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from src.research.procurement_pilot import PilotHTTP,contract as shared_contract
from src.research.phase3c.sources import SourceHTTP,put
from src.research.sec_pilot.acquisition import ROOT,identity,now
from src.research.spec import canonical,digest

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/source_first_v001'
STATUSES=('PROVEN_FROM_EXISTING_EVIDENCE','PASS_BOUNDED_PROBE','PARTIAL','UNKNOWN','BLOCKED','NOT_APPLICABLE')
DIMENSIONS=('SOURCE_ACCESS','DENOMINATOR','HISTORICAL_DEPTH','POINT_IN_TIME','TIMING','REVISION_LINEAGE',
 'ENTITY_IDENTIFIERS','RELATIONSHIPS','RECORD_FREQUENCY','DEPENDENCE_GEOMETRY','TERMINAL_LIFECYCLE_BURDEN',
 'ACCESS_COST','REPRODUCIBILITY','GRAPH_REUSE')
HARD_GATES=('SOURCE_ACCESS','DENOMINATOR','POINT_IN_TIME','HISTORICAL_DEPTH','REPRODUCIBILITY','RECORD_FREQUENCY')


def candidates():
    return [
     {'id':'SEC','name':'SEC EDGAR filing/accession universe','reason':'Existing original-byte accession archive, offline parser and metadata lineage; form enumeration separates source from eventual financial outcomes',
      'primary':'https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/0000320193-19-000119-index.htm',
      'probes':[{'id':'SEC_ACCESS','kind':'existing_fixture_index','url':'https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/0000320193-19-000119-index.htm','rule':'First fixed Phase2 fixture in its original manifest order; no new issuer or outcome selection'},
       {'id':'SEC_DOC','kind':'documentation','url':'https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data','rule':'Official EDGAR filing-index/archive scope documentation'}]},
     {'id':'FR','name':'Federal Register document/publication register','reason':'Official date/document/agency register with mechanically defined publication-day denominator, independently of corporate success',
      'primary':'https://www.federalregister.gov/api/v1/documents.json?per_page=2&order=oldest&conditions%5Bpublication_date%5D%5Bis%5D=2019-01-02',
      'probes':[{'id':'FR_ACCESS','kind':'neutral_json_sample','url':'https://www.federalregister.gov/api/v1/documents.json?per_page=2&order=oldest&conditions%5Bpublication_date%5D%5Bis%5D=2019-01-02','rule':'First page, at most2 records, fixed2019-01-02 publication-day slice; no company/outcome/agency filter'},
       {'id':'FR_DOC','kind':'documentation','url':'https://www.federalregister.gov/developers/documentation/api/v1','rule':'Official schema/history/publication semantics'}]},
     {'id':'CT','name':'ClinicalTrials.gov study register','reason':'Official stable study IDs, sponsor/status/date fields and broad registered-study panel; current-version versus historical-posting distinction is testable',
      'primary':'https://clinicaltrials.gov/api/v2/studies?pageSize=2&sort=LastUpdatePostDate%3Aasc&format=json&countTotal=true',
      'probes':[{'id':'CT_ACCESS','kind':'neutral_json_sample','url':'https://clinicaltrials.gov/api/v2/studies?pageSize=2&sort=LastUpdatePostDate%3Aasc&format=json&countTotal=true','rule':'First page at most2 current registry studies in source LastUpdatePostDate ascending order; no status/sponsor/therapeutic/outcome filter'},
       {'id':'CT_DOC','kind':'documentation','url':'https://clinicaltrials.gov/data-api/api','rule':'Official API/schema/update/history semantics'}]}]


def contract():
    return {'version':'source_first_v001','mode':'SOURCE_FIRST_RESEARCHABILITY_MAPPING','surfaces':candidates(),
     'surface_ceiling':6,'request_ceiling':36,'retry':shared_contract()['retry'],
     'pacing':{'workers':1,'minimum_global_seconds':0.6},'sample_ceiling':2,'score_before_access':False,
     'dimensions':list(DIMENSIONS),'status_scale':list(STATUSES),'hard_gates':list(HARD_GATES),
     'stops':'Per-surface denial/redirect/uncertainty stops that frozen surface; independent other predeclared surfaces remain permitted. Total36, paid/evasive/corpus/performance/expanded-list stops entire pass.',
     'archive':'Shared PilotHTTP/Archive; per-surface immutable original bytes/stops; global reservations for quota/pacing; no blind resubmission',
     'SEC_identity':'Owner local EDGAR_IDENTITY only in transport header; never logged or tracked. Receipt header label describes redaction, not exact private header.',
     'existing_evidence':['phase2_summary.json','phase2_validation.json','phase3a_evidence.json','phase3_final_report.md',
      'phase4a_procurement_pilot_summary.json','phase4a_fda_pilot_summary.json','phase4a_merger_pilot_summary.json'],
     'surface_expansion':False,'new_timing_policy_approved':False,'performance_authorized':False,'family_pilot_candidate4':False,
     'Phase4B_4C_authorized':False,'hypothesis_selection_authorized':False,'maximum_mechanism_directions_per_source':3,
     'forbidden':['prices','returns','event study','commercial data','full corpus','Orbis','Nexus','Aurora','experiment registration','graph','causal lab','paper/live']}


def validate(m):
    if len(m.get('surfaces',[]))>6 or canonical(m)!=canonical(contract()):raise ValueError('Source-first exact scope/route/rule/ceiling changed')
    return digest(m)


def frozen():
    m=json.loads((DOCS/'phase4a_source_probe_manifest.json').read_bytes());receipt=json.loads((DOCS/'phase4a_source_probe_freeze.json').read_bytes())
    if validate(m)!=receipt['manifest_sha256']:raise ValueError('Source-first freeze mismatch')
    return m


class ProbeHTTP(PilotHTTP):
    def __init__(self,m,surface,*,root=RAW,transport=None,**kwargs):
        validate(m)
        if surface not in m['surfaces']:raise ValueError('Surface outside frozen set')
        self.global_root=Path(root)
        def identified(url,headers,payload):
            if urlsplit(url).hostname=='www.sec.gov':headers=dict(headers,**{'User-Agent':identity()})
            return SourceHTTP._transport(url,headers,payload)
        super().__init__(shared_contract(),root=self.global_root/surface['id'],transport=transport or identified,**kwargs)
        self.m=m;self.allowed={p['url'] for p in surface['probes']}
    def starts(self):return sorted(self.global_root.glob('*/reservations/*.json'))


def acquire():
    m=frozen();saved=RAW/'acquisition.json'
    if saved.exists():return json.loads(saved.read_bytes())
    outcomes=[]
    for surface in m['surfaces']:
        http=ProbeHTTP(m,surface);rows=[];status='PROBES_COMPLETED_REVIEW_REQUIRED'
        for probe in surface['probes']:
            try:receipt,body=http.fetch(probe['url'],purpose=probe['id'])
            except ValueError:status='SURFACE_BOUNDARY_OR_TRANSPORT_STOP';break
            rows.append({'probe_id':probe['id'],'receipt':receipt})
            if receipt['status']!=200:status='SURFACE_ROUTE_UNAVAILABLE';break
        outcomes.append({'surface':surface['id'],'sources':rows,'acquisition_status':status})
        if len(http.starts())>=36:break
    result={'manifest_sha256':digest(m),'surfaces':outcomes,'starts':len(list(RAW.glob('*/reservations/*.json'))),
     'scientific_review':'REQUIRED','finished_at_utc':now(),'performance_inputs':0}
    put(saved,result);return result


def dimension(status,reason,evidence):
    if status not in STATUSES or not reason or not evidence:raise ValueError('Status requires reason and provenance')
    return {'status':status,'reason':reason,'evidence':evidence}


def assess(row):
    if set(row['dimensions'])!=set(DIMENSIONS):raise ValueError('Researchability dimensions incomplete')
    for cell in row['dimensions'].values():dimension(cell['status'],cell['reason'],cell['evidence'])
    if not row.get('access_attempted') and row['dimensions']['SOURCE_ACCESS']['status']!='PROVEN_FROM_EXISTING_EVIDENCE':raise ValueError('No scientific assessment before access proof')
    # Partial counts only when the reviewer gives an explicit, evidenced plausibility basis.
    return all(row['dimensions'][k]['status'] in ('PASS_BOUNDED_PROBE','PROVEN_FROM_EXISTING_EVIDENCE')
     or (row['dimensions'][k]['status']=='PARTIAL' and k in row.get('plausible_hard_gates',[])) for k in HARD_GATES)


def neutral_sample(body,surface):
    obj=json.loads(body)
    records=obj['results'] if surface=='FR' else obj['studies'] if surface=='CT' else []
    if len(records)>2:raise ValueError('Tiny sample ceiling exceeded; no larger sample interpreted')
    return records


def timing(kind):
    if kind not in ('OBSERVED_PUBLIC_TIMESTAMP','OBSERVED_DATE_ONLY','MODELED_BOUND_PLAUSIBLE','PRESENT_DAY_DATABASE_ONLY','CONTRADICTORY','UNKNOWN'):raise ValueError('Unknown clock semantics')
    return {'capability':kind,'policy_approved':False,'trading_eligibility_activated':False}


def mechanism_allowed(row,estimand):
    if estimand not in ('PREDICTIVE','CAUSAL_CANDIDATE'):raise ValueError('Declare predictive/causal estimand')
    if not assess(row):raise ValueError('No mechanisms before plausible hard gates')
    return {'estimand_type':estimand,'experiment_authorized':False,'causal_identification_certified':False}


def denominator_gate(*,success_selected,current_state_only):
    return 'BLOCKED_OUTCOME_SELECTION' if success_selected else 'BLOCKED_HISTORICAL_PIT' if current_state_only else 'REQUIRES_COVERAGE_REVIEW'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('manifest','acquire'));p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.command=='manifest':print('Source-first manifest:',digest(frozen()))
    else:
        if not a.execute:p.error('Probe acquisition requires --execute')
        print('Source-first requests:',acquire()['starts'])
