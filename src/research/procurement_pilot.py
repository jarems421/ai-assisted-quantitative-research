"""Bounded publication-channel pilot; no price, strategy or performance interface."""
import argparse,json,re,time,uuid
from datetime import date
from pathlib import Path
from src.research.spec import digest,canonical
from src.research.phase3c.sources import SourceHTTP,put
from src.research.sec_pilot.acquisition import Archive,ROOT,now

DOCS=ROOT/'docs/acceleration';RAW=ROOT/'data/raw/procurement_pilot_v001'
MONTHS=[f'{y}-{m:02}' for y in (2019,2020) for m in (1,3,5,7,9,11)]
ALTERNATIVE='https://raw.githubusercontent.com/fedspendingtransparency/usaspending-api/master/usaspending_api/api_contracts/contracts/v2/transactions.md'


def contract():
    return {'version':'procurement_source_pilot_v001','research_cutoff':'2020-11-30','owner_authority':'FAMILY_APPROVED_FOR_SOURCE_FEASIBILITY',
     'slots':[{'slot':m,'discovery_url':f'https://www.defense.gov/News/Contracts/Year/{m[:4]}/Month/{int(m[5:])}/'} for m in MONTHS],
     'announcement_source_family':'Official defense contract announcement pages; no rotated hosts or mirrors',
     'selection':{'announcement':'Earliest official dated announcement in the fixed month from an exhaustive monthly index; ascending date then original URL tie-break',
                  'award':'First listed award in source document order; no easiest/public/amount selection','filters':{},'month_replacement':False},
     'fallback':None,'discovery':'Exact official monthly URLs only; incomplete enumeration fails closed; no search or dynamic endpoint guess',
     'alternative_channel_check':{'url':ALTERNATIVE,'purpose':'Official USAspending transaction documentation: evaluate whether it can substitute for an announcement; no event data query'},
     'USAspending_route':{'url':'https://api.usaspending.gov/api/v2/search/spending_by_award/','method':'POST','selection':'Exact selected printed contract identifier; no recipient/amount/current-public filters; freeze payload before dispatch'},
     'SEC_route':'Exact sec.gov/Archives/edgar/data identity document URLs evidenced by selected-source lineage; no companyfacts/latest/ticker lookup; freeze dispatch receipt',
     'OpenFIGI_route':{'url':'https://api.openfigi.com/v3/mapping','role':'Identifier corroboration only; never historical span or parent proof; freeze payload before dispatch'},
     'request_ceiling':60,'indicative_allocation':{'Announcement_Documentation':12,'USAspending':12,'SEC':24,'OpenFIGI':12},
     'allocation_policy':'Total ceiling authoritative including listing discovery/retries; indicative allocation not additive permission; no unrelated-source expansion',
     'pacing':{'workers':1,'global_minimum_seconds':0.6,'OpenFIGI_minimum_seconds':3},
     'retry':{'maximum_attempts_per_request':3,'transient_statuses':[500,502,503,504],'backoff_seconds':[1,2],
              'no_retry_statuses':[403,429],'transport_unknown_submission':'Count reservation and stop; never blind resubmit'},
     'storage':{'archive':'Existing Archive original-byte store','root':'data/raw/procurement_pilot_v001','receipts':'Exclusive canonical JSON; original bodies never reserialized',
                'hash':'SHA256 original bytes; content-addressed versions; reserve request before transport; contact headers private/redacted'},
     'status_taxonomy':['OFFICIAL_PAGE_UNAVAILABLE','DEFERRED_SOURCE_CHANNEL_STOP','SOURCE_ENUMERATION_UNCERTIFIED','AWARD_SELECTED',
                        'PRIVATE_RECIPIENT','RECIPIENT_PARENT_AMBIGUOUS','PUBLIC_RECIPIENT_PLAUSIBLE','UNAVAILABLE','UNKNOWN','NOT_APPLICABLE','DATE_ONLY','OBSERVED_TIMESTAMP_SUPPORTED','CONTRADICTORY'],
     'stop_conditions':['403/429/access denial','Redirect/encoding/source contradiction','Incomplete monthly enumeration','60 starts','Paid/evasive access','Performance information','Unapproved scope'],
     'forbidden':['Tiingo','FMP','Orbis','Nexus','Aurora','price data','returns','event studies','threshold/holding-period optimization','graph','causal claim','experiment creation/freeze','paper/live'],
     'output_questions':['accessibility','lineage','action semantics','public timing','historical identity','clustering','controls','variation','dependence','advance redesign or reject'],
     'performance_authorized':False}


def validate_manifest(m):
    # Exact structure comparison also rejects newly nested discretionary filters.
    if canonical(m)!=canonical(contract()):raise ValueError('Frozen scope/filter/slot/route changed')
    if len(m['slots'])!=12 or len({s['slot'] for s in m['slots']})!=12:raise ValueError('Denominator changed')
    return digest(m)


def check_frozen():
    m=json.loads((DOCS/'phase4a_procurement_pilot_manifest.json').read_bytes());h=validate_manifest(m)
    f=json.loads((DOCS/'phase4a_procurement_pilot_freeze.json').read_bytes())
    if f['manifest_sha256']!=h:raise ValueError('Manifest freeze mismatch')
    return m


def select_announcement(rows,month,*,complete):
    if not complete:raise ValueError('Incomplete enumeration cannot certify earliest')
    eligible=[]
    for r in rows:
        date.fromisoformat(r['page_date'])
        if not re.fullmatch(r'https://www\.defense\.gov/News/Contracts/Contract/Article/\d+/[a-z0-9-]+/?',r['url']):raise ValueError('Nonofficial announcement')
        if r['page_date'].startswith(month+'-'):eligible.append(r)
    if not eligible:return None
    return min(eligible,key=lambda r:(r['page_date'],r['url']))


def event_record(slot,receipt=None):
    return {'slot':slot,'status':'OFFICIAL_PAGE_UNAVAILABLE' if receipt else 'DEFERRED_SOURCE_CHANNEL_STOP',
            'receipt_sha256':digest(receipt) if receipt else None,'announcement_id':None,'award':None,
            'recipient':None,'recipient_status':'UNAVAILABLE','public_private_status':'UNKNOWN','parent_issuer':None,
            'identity_status':'UNAVAILABLE','USAspending_status':'NOT_TESTED_NO_SELECTED_EVENT',
            'economic_date':None,'signature_date':None,'action_date':None,'announcement_date':None,
            'observed_public_at':None,'retrieved_at_utc':receipt.get('retrieved_at_utc') if receipt else None,
            'timing_status':'UNAVAILABLE','modeled_policy_approved':False,'trading_eligible':False}


def timing(page_date,observed=None):
    if observed is not None:raise ValueError('Timestamp requires separately reviewed publication evidence, not a parsed attribute')
    if page_date:date.fromisoformat(page_date)
    return {'page_date':page_date,'public_available_at_utc':None,'status':'DATE_ONLY' if page_date else 'UNAVAILABLE','modeled_policy_approved':False}


def lineage(printed_id,returned_ids):
    matches=[x for x in returned_ids if x==printed_id]
    return 'UNMATCHED' if not matches else 'USASPENDING_MATCHED_IDENTIFIER_ONLY' if len(matches)==1 else 'USASPENDING_AMBIGUOUS'


class PilotHTTP:
    def __init__(self,m,*,root=RAW,transport=None,sleep=time.sleep,clock=time.monotonic):
        validate_manifest(m);self.m=m;self.root=Path(root);self.archive=Archive(root)
        self.transport=transport or SourceHTTP._transport;self.sleep=sleep;self.clock=clock;self.last=None
        self.allowed={s['discovery_url'] for s in m['slots']}|{ALTERNATIVE}

    def starts(self):return sorted((self.root/'reservations').glob('*.json'))

    def fetch(self,url,*,slot=None,purpose='publication_channel'):
        if url not in self.allowed:raise ValueError('URL outside frozen dispatch allowlist')
        cache=self.root/'completed'/(digest({'url':url})+'.json')
        if cache.exists():
            receipt=json.loads(cache.read_bytes());return receipt,self.archive.read(receipt['body'])
        stop=self.root/'publication_stop.json'
        if stop.exists() and url!=ALTERNATIVE:raise ValueError('Persisted publication stop; no automatic retry')
        for attempt in range(1,4):
            if len(self.starts())>=self.m['request_ceiling']:raise ValueError('Total starts ceiling reached')
            # Persisted UTC pacing remains enforceable across process restarts.
            from datetime import datetime,timezone
            previous=[json.loads(p.read_bytes())['request_started_at_utc'] for p in self.starts()]
            if previous:
                gap=(datetime.now(timezone.utc)-datetime.fromisoformat(max(previous))).total_seconds()
                self.sleep(max(0,.6-gap))
            if self.last is not None:self.sleep(max(0,.6-(self.clock()-self.last)))
            self.last=self.clock()
            reserve={'url':url,'slot':slot,'purpose':purpose,'attempt':attempt,'request_started_at_utc':now(),'manifest_sha256':digest(self.m)}
            token=uuid.uuid4().hex;put(self.root/'reservations'/(token+'.json'),reserve)
            try:
                status,headers,body,final=self.transport(url,{'User-Agent':'ResearchOS-SourceFeasibility/1.0','Accept-Encoding':'identity'},None)
                # Archive before parsing status, URL or headers, including denial bytes.
                saved=self.archive.body('0000000000-00-000000',body)
                receipt=dict(reserve,status=status,retrieved_at_utc=now(),final_url=final,body=saved,
                    content_type=next((v for k,v in headers.items() if k.lower()=='content-type'),None),
                    response_headers={k.lower():v for k,v in headers.items() if k.lower() in ('content-type','content-length','content-encoding','date','last-modified','retry-after')},
                    request_headers='IDENTIFIED_GENERIC_UA_NO_CONTACT_OR_CREDENTIAL',decoding='Original response bytes; no text interpretation yet')
                put(self.root/'receipts'/(token+'.json'),receipt)
                if final!=url or status in (301,302,303,307,308):raise ValueError('Redirect prohibited')
                if receipt['response_headers'].get('content-encoding','identity').lower()!='identity':raise ValueError('Unexpected encoding retained, not interpreted')
                length=receipt['response_headers'].get('content-length')
                if length is not None and int(length)!=len(body):raise ValueError('Incomplete original response')
                if status in (403,429):
                    reason={'reason':'SOURCE_CHANNEL_BLOCKED','receipt_sha256':digest(receipt),'status':status}
                    put(self.root/'stops'/(digest(reason)+'.json'),reason)
                    if not stop.exists():put(stop,reason)
                    put(cache,receipt);return receipt,body
                if status in self.m['retry']['transient_statuses'] and attempt<3:
                    self.sleep(2**(attempt-1));continue
                if status!=200 and url!=ALTERNATIVE and not stop.exists():
                    put(stop,{'reason':'SOURCE_UNAVAILABLE','receipt_sha256':digest(receipt),'status':status})
                put(cache,receipt);return receipt,body
            except Exception as error:
                failure=dict(reserve,error_type=type(error).__name__,status='TRANSPORT_OR_BOUNDARY_FAILURE')
                if hasattr(error,'partial_body'):failure['partial_body']=self.archive.body('0000000000-00-000000',error.partial_body)
                put(self.root/'errors'/(token+'.json'),failure)
                if not stop.exists():put(stop,{'reason':'UNCERTAIN_TRANSPORT_OR_BOUNDARY','failure_sha256':digest(failure)})
                raise ValueError('Source stopped; reservation/error bytes retained') from None
        raise ValueError('Bounded source attempts exhausted')


def acquire():
    m=check_frozen();http=PilotHTTP(m)
    existing=RAW/'result.json'
    if existing.exists():return json.loads(existing.read_bytes())
    primary=m['slots'][0];receipt,body=http.fetch(primary['discovery_url'],slot=primary['slot'])
    if receipt['status']==200:
        raise ValueError('Channel accessible: inspect archived monthly enumeration before any derived dispatch; no earliest event asserted yet')
    # The only independently permitted alternative is official transaction documentation.
    alternate,doc=http.fetch(ALTERNATIVE,purpose='alternative_documentation')
    rows=[event_record(s['slot'],receipt if i==0 else None) for i,s in enumerate(m['slots'])]
    result={'version':'procurement_access_gate_v001','manifest_sha256':digest(m),'status':'SOURCE_CHANNEL_BLOCKED',
            'primary_receipt':receipt,'alternative_documentation_receipt':alternate,
            'alternative_status':'OFFICIAL_TRANSACTION_DOC_NOT_ANNOUNCEMENT_CHANNEL' if alternate['status']==200 else 'ALTERNATIVE_DOCUMENTATION_UNAVAILABLE',
            'alternative_semantic_check':{'action_date_documented':b'action_date' in doc,'modification_number_documented':b'modification_number' in doc,
                                        'exact_historical_first_public_proven':False},'slots':rows,'requests':len(http.starts()),
            'verdict':'PROCUREMENT_FAMILY_REJECT','verdict_scope':'Frozen historical publication-channel/frame failed cheaply; not proof that all official procurement channels are impossible',
            'stop_authority':'Owner sections6/28; no adequate accessible historical announcement channel established within frozen routes',
            'performance_inputs':0}
    put(existing,result);return result


def report(check=False):
    m=check_frozen();r=json.loads((RAW/'result.json').read_bytes());http=PilotHTTP(m)
    requests=[]
    for p in sorted((RAW/'receipts').glob('*.json')):
        row=json.loads(p.read_bytes());http.archive.read(row['body'])
        requests.append({k:row[k] for k in ('url','slot','purpose','attempt','request_started_at_utc','status','retrieved_at_utc','body','content_type')})
    if len(requests)!=len(http.starts()) or len(requests)>60:raise ValueError('Unreconciled reservations/receipts')
    pub={'manifest_sha256':digest(m),'denominator':12,'verdict':r['verdict'],'source_channel':'SOURCE_CHANNEL_BLOCKED','requests':len(requests),
         'official_pages_retrieved':0,'selected_awards':0,'USAspending_matches':0,'USAspending_match_status':'NOT_TESTED',
         'mapped_public_issuers':0,'mapping_status':'NOT_TESTED','first_public_supported':0,'timing':'UNAVAILABLE',
         'unique_awards':None,'unique_recipients':None,'effective_sample_size':None,'controls':'NOT_ASSESSED_NO_EVENTS',
         'dominant_dependence':'Not measured; potential repeated recipient/agency/contract/page/date/programme/budget clustering remains a design concern',
         'verdict_scope':r['verdict_scope'],'EXP004':'PAUSED','EXP005':'ABANDONED_ABSENT','next_experiment':'NOT_REGISTERED_NOT_FROZEN',
         'performance_authorized':False,'policy_activated':False,'stop_authority':r['stop_authority']}
    outputs={'phase4a_procurement_pilot_summary.json':pub,
      'phase4a_procurement_source_registry.json':{'request_ceiling':60,'total_starts':len(http.starts()),'requests':requests,
       'counts':{'Official_announcements':sum(x['purpose']=='publication_channel' for x in requests),'USAspending_documentation':sum(x['purpose']=='alternative_documentation' for x in requests),
                 'USAspending_data':0,'SEC':0,'OpenFIGI':0,'Tiingo':0,'FMP':0,'Orbis':0,'Nexus':0,'Aurora':0,'browser_search':0},
       'cost':'No purchase or source upgrade; account-wide debit unknown','original_bytes':'Ignored Archive bodies; public hashes/lengths, no source payload'},
      'phase4a_procurement_events.json':{'denominator':12,'events':r['slots'],'selected_awards':0,'economic_fields_unavailable_not_zero':True},
      'phase4a_procurement_timing_review.json':{'denominator':12,'cases':[{'slot':x['slot'],**timing(None)} for x in r['slots']],'approved_event_timing_policy':None,'v002_v003_reused':False},
      'phase4a_procurement_identity_review.json':{'denominator':12,'cases':[{'slot':x['slot'],'recipient_status':'UNAVAILABLE_NO_ANNOUNCEMENT','public_private_status':'UNKNOWN','issuer':None,'security':None,'parent_relation':'NOT_TESTED'} for x in r['slots']]},
      'phase4a_procurement_cluster_geometry.json':{'raw_slots':12,'pages_found':0,'award_lines':None,'unique_awards':None,'unique_action_chains':None,'unique_recipients':None,'plausible_public_issuers':None,'recipient_repeats':None,'agency_repeats':None,'same_day_clusters':None,'modification_clusters':None,'effective_sample_size':None,'status':'NO_GEOMETRY_ESTIMATED_ACCESS_STOP'}}
    validation=DOCS/'phase4a_procurement_validation.json';v=json.loads(validation.read_bytes()) if validation.exists() else {}
    md=f'''# Procurement pilot: publication channel stop

**{r['verdict']}. SOURCE_CHANNEL_BLOCKED.** Frozen manifest hash `{digest(m)}`. The owner-approved source-only pilot stopped at its first scientific gate; no experiment, prices, strategy or performance was created.

The first fixed slot, January2019, requested the exact official monthly discovery URL. It returned HTTP{receipt_status(r)}. Its original response bytes and request/retrieval/hash receipt are archived. No proxy, redirect following, host rotation, scraping workaround or retry of the denied channel occurred. Previous browser denial remains separate historical evidence. This is a failure of ordinary access to the frozen route, not proof that all government publication channels are impossible.

The independent official USAspending transaction-documentation request returned HTTP{r['alternative_documentation_receipt']['status']}. Its schema describes action/modification lineage but does not establish the earliest historical public announcement or first-public timestamp. It cannot replace a missing announcement under the approved rule. No award/transaction API data, SEC or OpenFIGI request followed. Search snippets and filing-policy v003 were not used to fill the gap.

| Denominator outcome | Count |
| --- | ---: |
| Fixed historical slots | 12 |
| Directly attempted publication slot | 1 |
| Unvisited slots retained after stop | 11 |
| Selected announcements / first awards | 0 / 0 |
| Public-company mappings / timing certificates | 0 / 0; not tested |

All twelve slots remain explicit in [events](phase4a_procurement_events.json). Eleven deferred slots are not eleven observed404s, zero-award months or private recipients. Award/action/amount, recipient, parent, class and time fields are unavailable; no absence or zero value is manufactured. [Identity](phase4a_procurement_identity_review.json), [timing](phase4a_procurement_timing_review.json) and [geometry](phase4a_procurement_cluster_geometry.json) preserve that distinction.

## Ten pilot questions

| Question | Answer |
| --- | --- |
| Q1 authoritative historical access | Failed for the frozen ordinary publication route; no reliable accessible channel established |
| Q2 award/action lineage | Not tested: no selected award; documentation only shows potential transaction structure |
| Q3 new work versus modification/ceiling | Not tested on original announcements; equivalence never assumed |
| Q4 public timing | Unavailable; no observed instant or modeled bound approved |
| Q5 historical listed-recipient mapping | Not tested; no public/private cases dropped |
| Q6 clustering | Not measured; page/recipient/agency/contract/calendar clusters remain potential concerns |
| Q7 controls | Not selected or certified; peers, competitors, observable losing bidders or within-recipient comparisons would need dated evidence and confounding/anticipation review |
| Q8 larger-census justification | No: source gate failed before event variation could be measured |
| Q9 dominant dependence | Empirically unknown; repeat recipients, modifications, programme/budget cycles and agency/date shocks require later review |
| Q10 full design/population phase | Reject expansion under this channel/frame; no larger campaign authorized |

Anticipation remains unassessed on actual cases. A future differently authorized source framing would need solicitation/pre-award/schedule/competition and modification history; this pilot acquired none. No causal claim or independent sample-size certificate follows from potential controls or documentation.

[Source registry](phase4a_procurement_source_registry.json) accounts for {len(requests)} starts including retries, below60: publication1; USAspending documentation1; every other source/data/search0. No successful announcement match is claimed from the documentation response. All HTTP bodies, including errors, remain ignored and immutable. Retrieval today is historical reconstruction, not contemporaneous ingestion. A persisted publication stop prevents automatic resubmission.

Validation: {v.get('local_tests_passed','pending')} local tests; {v.get('public_tests_passed','pending')} public tests; {v.get('tests_skipped','pending')} skipped. [Receipt](phase4a_procurement_validation.json). Reconcile archived bodies/report with `python -m src.research.procurement_pilot report --check`; it performs no network request. Acquisition is a separate `acquire --execute` mutation and is not routine reproduction.

EXP004 remains paused; EXP005 abandoned and absent. Phase3, FDA/merger evidence, approved policies and frozen experiments remain unchanged. No EXP006, price/performance, graph, causal lab, paper/live or Phase4B/4C operation occurred.

**Stopped under owner sections6/28.** No owner decision is required to record this negative pilot. Do not expand procurement acquisition. Any attempt with a genuinely different official historical announcement channel requires a separately reviewed exact route/frame and new authorization; no alternate host or mirrored route is proposed as an evasion.
'''.replace('January2019','January 2019').replace('HTTP','HTTP ').replace('observed404s','observed 404s').replace('below60','below 60').replace('publication1','publication 1').replace('documentation1','documentation 1').replace('data/search0','data/search 0').replace('Phase3','Phase 3').replace('Phase4B/4C','Phase 4B/4C').replace('sections6/28','sections 6/28')
    texts={k:json.dumps(x,sort_keys=True,indent=2)+'\n' for k,x in outputs.items()};texts['phase4a_procurement_pilot_report.md']=md
    for name,text in texts.items():
        p=DOCS/name
        if check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:raise ValueError('Pilot report mismatch: '+name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    return pub


def receipt_status(r):return r['primary_receipt']['status']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['manifest','acquire','report']);p.add_argument('--execute',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.command=='manifest':print('Frozen manifest:',digest(check_frozen()))
    elif a.command=='acquire':
        if not a.execute:p.error('Acquisition requires explicit --execute')
        print('Pilot acquisition:',acquire()['status'])
    else:print('Pilot report:',report(a.check)['verdict'])
