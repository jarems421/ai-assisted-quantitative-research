import copy,hashlib,io,json,re,socket,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from src.research.discovery import records as R
from src.research.discovery import demo as D
from src.research.discovery.cli import main,prompt
from src.research.discovery.ledger import Ledger,LedgerError,core
from src.research.discovery.report import compare,summary,metrics
from src.research.discovery.review import checklist,source_next
from src.research.spec import canonical,digest

ROOT=Path(__file__).resolve().parents[1]
U=R.UNKNOWN
COMPANY=D.entity('LISTED_COMPANY','SYN_LISTED:ALPHA','Alpha Synthetic Holdings (fictional)')
FACILITY=D.entity('FACILITY','SYN_FACILITY:F-001','Synthetic Terminal North')


def live_ev(locator,depth='VERIFIED_ORIGINAL_FIELD',kind='ORIGINAL_DOCUMENT'):
    return {'locator':'https://example.invalid/'+locator,'kind':kind,'depth':depth,'passage':'Test passage.',
            'sha256':hashlib.sha256(locator.encode()).hexdigest() if depth in R.ORIGINAL else None,'archive':None,'synthetic':False,'reused_from':None}


def campaign(method='OBSERVATION_FIRST',fixture='SYNTHETIC',**extra):
    c=D.rec('campaign',id='DLC-T-'+method[:3],title='Test campaign',method=method,fixture=fixture,question='Test question?',
            authority='docs/strategy/owner_discovery_lab_2026-10-21.md',budget=dict(D.BUDGET),notes=[])
    c.update(extra);return c


def observation(oid='OBS-T-1',kind='STATE_CHANGE',**extra):
    o=D.rec('observation',id=oid,source_id='SRC-T',kind=kind,statement='Ceiling reduced.',value={'from':10,'to':6},units='tonnes/day',
            denominator='single facility',entity=FACILITY,depth='VERIFIED_ORIGINAL_FIELD',evidence=[D.syn('obs/'+oid)],
            clocks=D.clocks('2000-03-01','2000-03-02','2000-04-01T00:00:00+00:00'),as_of_status='VERIFIED_ONLY_RETROSPECTIVELY',
            why_informative='State change.',outcome_independent=True)
    o.update(extra);return o


def relationship(rid='REL-T-1',**extra):
    r=D.rec('relationship',id=rid,source_entity=FACILITY,target_entity=COMPANY,type='OPERATION',direction='Operator.',
            period={'start':'1990-01-01','end':'OPEN'},basis='DOCUMENTED',status='VERIFIED',evidence=[D.syn('rel/'+rid,'VERIFIED_ORIGINAL_RECORD')],
            quantity_transfer={'status':'NOT_APPLICABLE','method':'NONE','evidence':[],'note':'No allocation.'})
    r.update(extra);return r


def candidate(method='OBSERVATION_FIRST',entry='OBS-T-1',**extra):
    c=D.rec('candidate',id='CAND-T-1',method=method,entry_record=entry,population='Facility F-001 and operator.',
            predictor={'observation_ids':['OBS-T-1'],'quantity':'Change in ceiling','units':'tonnes/day','transformation':'NONE'},
            exposure={'company':COMPANY,'relationship_ids':['REL-T-1'],'claim_basis':'GROSS','allocation_required':False,
                      'gross':{'value':40,'units':'USD million/year'},'net':U,'materiality':'Synthetic material share.'},
            mechanism='Ceiling lowers shipments.',
            outcome={'quantity':'Reported shipments','units':'tonnes/quarter','route':'Quarterly report','source_id':'SRC-T','status':'OBSERVED_VALUE',
                     'value':61,'derived_from_observations':['OBS-T-OUT'],'evidence':[D.syn('out')],'independence':'Issuer-measured.'},
            joins=D.joins(legal_entity='VERIFIED',period='VERIFIED'),
            information_event={'description':'Register posting','decision_time':'2000-03-02','basis':'Version date.'},
            public_time_route='Archived register versions.',horizon='Quarterly outcome revisable within weeks.',
            closest_substitute=D.substitute(True,'Issuer release.','issuer/release'),increment='Quantified ceiling.',
            falsification='Show the report lacks facility shipments.',selection=D.selection(),
            propositions=D.propositions('Effect.','Lead.','Residual.'),recommendation={'action':'REQUEST_M_REVIEW','reason':'Test.'})
    c.update(extra);return c


def world(tmp,method='OBSERVATION_FIRST'):
    led=Ledger.create(Path(tmp)/'t.jsonl',campaign(method),D.Clock())
    led.append('source',D.passport('SRC-T','Test register',field='ceiling',units='tonnes/day'))
    led.append('observation',observation(kind='EVENT' if method=='EVENT_FIRST' else 'STATE_CHANGE'))
    led.append('observation',observation('OBS-T-OUT',kind='QUANTITY',value=61,units='tonnes/quarter',outcome_independent=False))
    led.append('relationship',relationship())
    return led


def m_review(rid='REV-T-M',judgment='EVIDENCED',reviewer='SYNTHETIC_FIXTURE',version=1,not_checked=('PUBLIC_TIME',)):
    return D.rec('review',id=rid,candidate_id='CAND-T-1',version=version,reviewer=D.reviewer(reviewer),
                 judgments={k:{'judgment':judgment,'reason':'Inspected.','evidence_refs':['OBS-T-1']} for k in R.M_REQUIREMENTS},
                 not_checked=D.not_checked(*not_checked),conclusion='Recorded judgment.')


def disposition(did='DSP-T-1',decision='HOLD',reason_type='UNRESOLVED',kind='SYNTHETIC_FIXTURE',version=1,**extra):
    d=D.rec('disposition',id=did,candidate_id='CAND-T-1',version=version,decision=decision,reason_type=reason_type,
            reason='Stated reason.',scope='CAND-T-1 v1',decided_by=D.reviewer(kind))
    d.update(extra);return d


class DiscoveryLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)

    def refused(self,action,pattern=None):
        with self.assertRaises(ValueError) as caught:action()
        if pattern:self.assertRegex(str(caught.exception),pattern)

    def test_original_observation_keeps_units_and_provenance(self):
        led=world(self.tmp.name);s=led.load();o=s.latest('observation','OBS-T-1')
        self.assertEqual((o['units'],o['depth']),('tonnes/day','VERIFIED_ORIGINAL_FIELD'))
        self.assertTrue(o['evidence'][0]['sha256'])
        bad=observation('OBS-T-2');bad['evidence'][0]['sha256']=None
        self.refused(lambda:led.append('observation',bad),'sha256 or archive')
        weak=observation('OBS-T-3',evidence=[D.syn('schema','SCHEMA_ONLY','SCHEMA')])
        self.refused(lambda:led.append('observation',weak),'original depth declared')
        missing=observation('OBS-T-4');del missing['units']
        self.refused(lambda:led.append('observation',missing),'use UNKNOWN rather than omitting')

    def test_observation_may_exist_without_a_hypothesis(self):
        led=world(self.tmp.name);s=led.load()
        self.assertEqual(s.versions['candidate'],{})
        self.assertIn('no (observation only)',summary(s))

    def test_relationship_cannot_be_inferred_from_coincident_names(self):
        led=world(self.tmp.name)
        self.refused(lambda:led.append('relationship',relationship('REL-T-2',basis='NAME_MATCH_ONLY')),'coincident names')
        names=relationship('REL-T-3',evidence=[D.syn('names','UNVERIFIED','NAME_MATCH')])
        self.refused(lambda:led.append('relationship',names),'original documentary evidence')
        unnamed=relationship('REL-T-4',target_entity=D.entity('LISTED_COMPANY','NAME:Alpha','Alpha'))
        self.refused(lambda:led.append('relationship',unnamed),'identified')
        led.append('relationship',relationship('REL-T-5',basis='NAME_MATCH_ONLY',status='UNVERIFIED'))

    def test_aggregate_to_cohort_allocation_stays_unverified(self):
        led=world(self.tmp.name)
        forced=relationship('REL-T-2',quantity_transfer={'status':'VERIFIED','method':'PROPORTIONAL_ASSUMPTION','evidence':[D.syn('split')],'note':'Pro rata.'})
        self.refused(lambda:led.append('relationship',forced),'assumed/proportional')
        led.append('relationship',relationship('REL-T-2',quantity_transfer={'status':'UNVERIFIED','method':'PROPORTIONAL_ASSUMPTION','evidence':[],'note':'Pro rata.'}))
        c=candidate();c['exposure'].update(relationship_ids=['REL-T-1','REL-T-2'],allocation_required=True)
        led.append('candidate',c)
        blockers=checklist(led.load(),'CAND-T-1')['requirements']['valid_join']['blockers']
        self.assertIn('ALLOCATION_UNVERIFIED:REL-T-2=PROPORTIONAL_ASSUMPTION',blockers)

    def test_missing_public_time_certificate_is_never_verified_as_of(self):
        led=world(self.tmp.name)
        for basis in ('WEB_CACHE','FILENAME','HTTP_HEADER','SEARCH_INDEX','DOCUMENT_DATE','DATASET_VERSION'):
            o=observation('OBS-T-9');o['clocks']['first_public']=D.clk('2000-03-02',basis,[D.syn('c','VERIFIED_ORIGINAL_RECORD','PUBLICATION_RECORD')])
            self.refused(lambda:led.append('observation',o),'cannot be inferred')
        o=observation('OBS-T-9');o['clocks']['first_public']=D.clk('2000-03-02','PUBLICATION_RECORD',[D.syn('c','VERIFIED_ORIGINAL_RECORD')])
        self.refused(lambda:led.append('observation',o),'publication-record certificate')
        self.refused(lambda:led.append('observation',observation('OBS-T-9',as_of_status='VERIFIED_AS_OF')),'certified first-public')
        late=observation('OBS-T-9');late['clocks']['first_public']=D.clk('2000-05-02','PUBLICATION_RECORD',[D.syn('c','VERIFIED_ORIGINAL_RECORD','PUBLICATION_RECORD')])
        self.refused(lambda:led.append('observation',late),'cannot follow our retrieval')
        undated=observation('OBS-T-9');undated['clocks']['first_public']=D.clk('2000-03-02',U)
        self.refused(lambda:led.append('observation',undated),'basis must be UNKNOWN')
        ok=observation('OBS-T-9',as_of_status='VERIFIED_AS_OF');ok['clocks']['first_public']=D.clk('2000-03-02','PUBLICATION_RECORD',[D.syn('c','VERIFIED_ORIGINAL_RECORD','PUBLICATION_RECORD')])
        led.append('observation',ok)

    def test_frozen_claim_cannot_change_silently(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        self.refused(lambda:led.append('candidate',candidate(mechanism='Different.')),'never overwritten')
        self.refused(lambda:led.freeze('CAND-T-1'),'already frozen')
        no_reason=candidate(version=2,supersedes=1,mechanism='Different.')
        self.refused(lambda:led.append('candidate',no_reason),'state why')
        lines=led.path.read_bytes().splitlines()
        i=next(n for n,l in enumerate(lines) if b'"type":"candidate"' in l)
        lines[i]=lines[i].replace(b'Ceiling lowers shipments.',b'Ceiling raises shipments.')
        led.path.write_bytes(b'\n'.join(lines)+b'\n')
        self.refused(led.load,'hash chain broken')

    def test_replay_rejects_rule_bypass_even_with_a_valid_chain(self):
        led=world(self.tmp.name);s=led.load()
        bad=disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE');bad['candidate_id']='CAND-NONE'
        event={'seq':len(s.events),'type':'disposition','recorded_at_utc':'2000-02-01T00:00:00+00:00','record':bad,'derived':{},'prev':s.events[-1]['hash']}
        event['hash']=digest(event)
        with led.path.open('ab') as f:f.write(canonical(event)+b'\n')
        self.refused(led.load,'fails current rules')

    def test_material_change_creates_new_version_and_keeps_old(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        clar=candidate(version=2,supersedes=1,revision_reason='Clarify falsification wording.',falsification='Clearer wording.')
        self.assertEqual(led.append('candidate',clar)['derived']['revision_kind'],'CLARIFICATION');led.freeze('CAND-T-1')
        changed=candidate(version=3,supersedes=2,revision_reason='Outcome changed after seeing data.',after_outcome_seen=True)
        changed['outcome'].update(quantity='Segment revenue',units='USD million')
        d=led.append('candidate',changed)['derived']
        self.assertEqual((d['revision_kind'],d['claim_class'],d['post_outcome']),('MATERIAL_REVISION','REFORMULATION',True))
        s=led.load();self.assertEqual(len(s.versions['candidate']['CAND-T-1']),3)
        self.assertEqual(s.version('candidate','CAND-T-1',1)['outcome']['quantity'],'Reported shipments')
        self.assertNotEqual(digest(core(s.version('candidate','CAND-T-1',1))),digest(core(changed)))

    def test_outcome_cannot_be_copied_from_predictor(self):
        led=world(self.tmp.name);c=candidate();c['outcome']['derived_from_observations']=['OBS-T-1']
        self.refused(lambda:led.append('candidate',c),'not independent')
        c=candidate();c['outcome']['quantity']='change in CEILING'
        self.refused(lambda:led.append('candidate',c),'repeats the predictor')

    def test_incomplete_card_is_never_certified(self):
        led=world(self.tmp.name);c=candidate();c['outcome'].update(status='ROUTE_ONLY',value=U,evidence=[],derived_from_observations=[])
        c['closest_substitute']=D.substitute(False,'Not checked.');led.append('candidate',c);led.freeze('CAND-T-1')
        ck=checklist(led.load(),'CAND-T-1');self.assertFalse(ck['software_certifies_M'])
        self.assertNotIn('PASS',json.dumps(ck['requirements']))
        self.refused(lambda:led.append('review',m_review(not_checked=('PUBLIC_TIME','COMPETITOR','OUTCOME'))),'mechanical blockers')
        self.refused(lambda:led.append('disposition',disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE')),'mechanical blockers')

    def test_complete_fields_still_need_a_human_judgment(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        ck=checklist(led.load(),'CAND-T-1')
        self.assertTrue(all(r['mechanical']=='NO_MECHANICAL_BLOCKER_HUMAN_JUDGMENT_REQUIRED' for r in ck['requirements'].values()))
        self.assertEqual(ck['next']['blocker'],'HUMAN_M_REVIEW_REQUIRED')
        self.refused(lambda:led.append('disposition',disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE')),'human Measurement Gate M review')
        led.append('review',m_review('REV-T-A',reviewer='ASSISTANT'))
        self.refused(lambda:led.append('disposition',disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE')),'human Measurement Gate M review')
        led.append('review',m_review())
        led.append('disposition',disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE'))

    def test_reviewer_uncertainty_and_human_reasons_are_retained(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        led.append('review',m_review(judgment='UNCERTAIN'))
        led.append('review',D.rec('review',id='REV-T-H',candidate_id='CAND-T-1',version=1,kind='H',reviewer=D.reviewer(),
                                  judgments={'judgment':'UNCERTAIN','information_event':U,'expectation_mechanism':U,'reason':'Cannot judge yet.'},
                                  not_checked=D.not_checked('PUBLIC_TIME'),conclusion='No conclusion forced.'))
        led.append('disposition',disposition(reason='Reviewer uncertain; hold without source work.'))
        s=Ledger(led.path).load();ck=checklist(s,'CAND-T-1')
        self.assertEqual({r['human_judgment'] for r in ck['requirements'].values()},{'UNCERTAIN'})
        self.assertEqual(ck['h_human_judgment'],'UNCERTAIN')
        self.assertEqual(s.dispositions[-1]['reason'],'Reviewer uncertain; hold without source work.')
        self.assertEqual(s.dispositions[-1]['decided_by']['kind'],'SYNTHETIC_FIXTURE')

    def test_dispositions_are_human_decisions_that_authorise_nothing(self):
        led=world(self.tmp.name);led.append('candidate',candidate())
        self.refused(lambda:led.append('disposition',disposition(kind='ASSISTANT')),'human decisions')
        self.refused(lambda:led.append('disposition',disposition(decision='REJECT',reason_type='ACCESS')),'HOLD, not REJECT')
        self.refused(lambda:led.append('disposition',disposition(authorizes=['source acquisition'])),'authorises nothing')
        verify=disposition(decision='VERIFY',verify={'decisive_question':'Q?','proposed_check':'One file.','cost':{'analyst_hours':1,'source_starts':1,'bytes':U},'authority':'RUN_NOW'})
        self.refused(lambda:led.append('disposition',verify),'proposal')
        self.refused(lambda:led.append('disposition',disposition(decision='LEVEL_A_DESIGN_CANDIDATE',reason_type='EVIDENCE_COMPLETE')),'frozen')

    def test_level_a_needs_m_pass_and_separate_h(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1');led.append('review',m_review())
        level_a=lambda:led.append('disposition',disposition('DSP-T-A',decision='LEVEL_A_DESIGN_CANDIDATE',reason_type='EVIDENCE_COMPLETE'))
        self.refused(level_a,'M_PASSED for this version first')
        led.append('disposition',disposition(decision='M_PASSED',reason_type='EVIDENCE_COMPLETE'))
        self.refused(level_a,'separate human H')
        led.append('review',D.rec('review',id='REV-T-H',candidate_id='CAND-T-1',version=1,kind='H',reviewer=D.reviewer(),
                                  judgments={'judgment':'PLAUSIBLE','information_event':'Posting.','expectation_mechanism':'Quarterly revision.','reason':'Stated.'},
                                  not_checked=D.not_checked('PUBLIC_TIME'),conclusion='H assessed separately.'))
        self.assertTrue(level_a()['derived']['requires_separate_owner_approval'])

    def test_all_methods_apply_identical_measurement_rules(self):
        results=[]
        for method,entry in (('OBSERVATION_FIRST','OBS-T-1'),('RELATIONSHIP_FIRST','REL-T-1'),('EVENT_FIRST','OBS-T-1'),('HYPOTHESIS_FIRST',None)):
            with tempfile.TemporaryDirectory() as tmp:
                led=world(tmp,method);c=candidate(method,entry);c['outcome']['status']='ROUTE_ONLY';c['outcome'].update(value=U,evidence=[],derived_from_observations=[])
                led.append('candidate',c);led.freeze('CAND-T-1');ck=checklist(led.load(),'CAND-T-1')
                results.append((ck['requirements'],ck['h_gaps'],ck['next']['blocker']))
        self.assertTrue(all(r==results[0] for r in results))

    def test_method_entry_rules(self):
        led=world(self.tmp.name)
        self.refused(lambda:led.append('candidate',candidate(entry=None)),'must start from a recorded observation')
        self.refused(lambda:led.append('candidate',candidate(method='HYPOTHESIS_FIRST')),'campaign method')
        with tempfile.TemporaryDirectory() as tmp:
            hyp=world(tmp,'HYPOTHESIS_FIRST')
            self.refused(lambda:hyp.append('candidate',candidate('HYPOTHESIS_FIRST','OBS-T-1')),'entry_record must be null')
        with tempfile.TemporaryDirectory() as tmp:
            evt=world(tmp,'EVENT_FIRST');evt.append('observation',observation('OBS-T-Q',kind='QUANTITY'))
            c=candidate('EVENT_FIRST','OBS-T-Q');c['predictor']['observation_ids']=['OBS-T-Q']
            self.refused(lambda:evt.append('candidate',c),'EVENT observation')

    def test_dated_relationship_must_cover_the_observation(self):
        led=world(self.tmp.name);led.append('relationship',relationship('REL-T-NOW',period={'start':'2020-01-01','end':'OPEN'}))
        c=candidate();c['exposure']['relationship_ids']=['REL-T-NOW'];led.append('candidate',c)
        self.assertIn('RELATIONSHIP_PERIOD_UNCOVERED:REL-T-NOW@OBS-T-1',checklist(led.load(),'CAND-T-1')['requirements']['valid_join']['blockers'])

    def test_reference_revised_after_freeze_is_flagged(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        led.append('observation',observation(version=2,supersedes=1,revision_reason='Corrected value.',value={'from':10,'to':7}))
        self.assertIn('REFERENCE_REVISED_AFTER_FREEZE:OBS-T-1 v1->v2',checklist(led.load(),'CAND-T-1')['requirements']['distinctive_predictor']['blockers'])

    def test_entity_identifiers_must_be_consistent(self):
        led=world(self.tmp.name);clash=relationship('REL-T-2',target_entity=D.entity('LEGAL_ENTITY','SYN_LISTED:ALPHA','Alpha'))
        self.refused(lambda:led.append('relationship',clash),'already recorded as LISTED_COMPANY')

    def test_review_must_acknowledge_what_was_not_checked(self):
        led=world(self.tmp.name);c=candidate();c['closest_substitute']=D.substitute(False,'Not checked.');led.append('candidate',c)
        sceptic=D.rec('review',id='REV-T-S',candidate_id='CAND-T-1',version=1,kind='SCEPTIC',role='information',reviewer=D.reviewer('ASSISTANT'),
                      judgments={'challenges':['Issuer may have explained it.'],'verdict':'CHALLENGE_UNRESOLVED','reason':'Unchecked.'},
                      not_checked=D.not_checked('PUBLIC_TIME'),conclusion='Open.')
        self.refused(lambda:led.append('review',sceptic),"COMPETITOR")
        sceptic['not_checked']=D.not_checked('PUBLIC_TIME','COMPETITOR');led.append('review',sceptic)

    def test_unsupported_novelty_and_return_inspection_are_refused(self):
        led=world(self.tmp.name)
        for phrase in ('Nobody else tracks this register.','Institutions overlook this.','This is unknown to the market.'):
            self.refused(lambda:led.append('candidate',candidate(increment=phrase)),'unsupported novelty')
        sel=D.selection(returns_inspected=True)
        self.refused(lambda:led.append('candidate',candidate(selection=sel)),'never inspects security returns')

    def test_renamed_claim_must_declare_its_predecessor(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        renamed=candidate(id='CAND-T-2',mechanism='Same data, new story.')
        self.refused(lambda:led.append('candidate',renamed),'prior_related_claims')
        renamed['selection']['prior_related_claims']=['CAND-T-1'];led.append('candidate',renamed)

    def test_review_references_must_exist(self):
        led=world(self.tmp.name);led.append('candidate',candidate());led.freeze('CAND-T-1')
        review=m_review(judgment='UNCERTAIN');review['judgments']['valid_join']['evidence_refs']=['REL-T-MISSING']
        self.refused(lambda:led.append('review',review),'unknown relationship REL-T-MISSING')

    def test_live_campaign_needs_recorded_authority_and_novelty_lint_covers_observations(self):
        self.refused(lambda:Ledger.create(Path(self.tmp.name)/'x.jsonl',campaign(fixture='LIVE',authority='docs/strategy/missing_authority.md')),'existing repository authority')
        led=world(self.tmp.name)
        self.refused(lambda:led.append('observation',observation('OBS-T-N',why_informative='No one else tracks this field.')),'unsupported novelty')

    def test_acquisition_needs_authority_and_respects_budget(self):
        self.refused(lambda:R.validate('campaign',campaign(budget={'analyst_hours':1,'source_starts':3,'external_bytes':0}),None),'cannot authorise acquisition')
        self.refused(lambda:R.validate('campaign',campaign(fixture='LIVE',budget={'analyst_hours':1,'source_starts':3,'external_bytes':0}),None),'acquisition_authorized')
        led=world(self.tmp.name)
        start=D.rec('effort',id='EFF-T-1',kind='SOURCE_START',description='GET',source_starts=1,bytes=100,receipt='receipt.json',outcome='SUCCESS')
        self.refused(lambda:led.append('effort',start),'no acquisition authority')
        led.append('effort',D.rec('effort',id='EFF-T-2',description='Reading.',analyst_minutes=100,outcome='NOT_APPLICABLE'))
        self.refused(lambda:led.append('effort',D.rec('effort',id='EFF-T-3',description='More reading.',analyst_minutes=30,outcome='NOT_APPLICABLE')),'exceed the campaign budget')

    def test_unknown_costs_remain_unknown(self):
        led=world(self.tmp.name);s=led.load()
        self.assertIn('UNKNOWN (no effort recorded)',summary(s))
        led.append('effort',D.rec('effort',id='EFF-T-1',kind='SEARCH',description='Search.',analyst_minutes=U,bytes=U,outcome='NOT_FOUND'))
        m=metrics(led.load())
        self.assertEqual(m['analyst minutes'],{'known':0,'unknown_entries':1,'entries':1})
        self.assertIn('0 + 1 UNKNOWN',summary(led.load()))

    def test_synthetic_and_live_evidence_are_segregated(self):
        with tempfile.TemporaryDirectory() as tmp:
            live=Ledger.create(Path(tmp)/'live.jsonl',campaign(fixture='LIVE'))
            self.refused(lambda:live.append('source',D.passport('SRC-T','Synthetic',field='f',units='u')),'forbidden outside synthetic')
        led=world(self.tmp.name);o=observation('OBS-T-L',evidence=[live_ev('x')])
        self.refused(lambda:led.append('observation',o),'only synthetic evidence')
        led.append('candidate',candidate());led.freeze('CAND-T-1')
        self.refused(lambda:led.append('review',m_review(reviewer='HUMAN')),'never real human decisions')

    def test_every_record_field_is_required(self):
        valid={'observation':observation(),'relationship':relationship(),'candidate':candidate()}
        for kind,record in valid.items():
            R.validate(kind,record,'SYNTHETIC')
            for key in record:
                broken=copy.deepcopy(record);del broken[key]
                with self.assertRaises(ValueError,msg=f'{kind}.{key}'):R.validate(kind,broken,'SYNTHETIC')

    def test_comparison_reports_counts_without_ranking(self):
        text=D.generate();section=text.split('## 8. Method comparison',1)[1]
        self.assertIn('No composite score, ranking or statistical inference',section)
        for word in ('better','superior','outperform','winner','best method','significant','alpha','%'):
            self.assertNotIn(word,section.lower())
        self.assertIn('undefined (0 original M passes)',section)

    def test_offline_demo_makes_no_external_requests_and_preserves_records(self):
        protected=sorted((ROOT/'docs').rglob('*.json'))+sorted((ROOT/'docs/strategy').glob('*.md'))
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        attempts=[]
        def connect(sock,address):attempts.append(address);raise ValueError('network blocked by test')
        with patch.object(socket.socket,'connect',connect):text=D.generate()
        self.assertEqual(attempts,[])
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected})
        self.assertEqual(D.check()['walkthrough'],'PASS')
        self.assertIn('Refused as intended:** loading a copy whose frozen candidate units were edited',text)
        source=' '.join(p.read_text(encoding='utf-8') for p in (ROOT/'src/research/discovery').glob('*.py'))
        for forbidden in ('import urllib','import requests','import socket','Store(','from src.research.store','nexus','http.client'):
            self.assertNotIn(forbidden,source)

    def test_source_passport_next_evidence_is_qualitative(self):
        schema=D.passport('SRC-A','A',field='f',units='u',depth='SCHEMA_ONLY',revision='UNVERIFIED',publication='UNVERIFIED')
        self.assertEqual(source_next(schema)[0],'OBTAIN_ONE_ORIGINAL_RECORD')
        blocked=D.passport('SRC-B','B',field='f',units='u');blocked['access']['status']='PAID'
        self.assertEqual(source_next(blocked)[0],'STOP_ROUTE')
        self.assertEqual(source_next(D.passport('SRC-C','C',field='f',units='u',publication='VERIFIED_ORIGINAL_RECORD'))[0],'READY_FOR_OBSERVATIONS')

    def test_cli_round_trip_and_prompts(self):
        tmp=Path(self.tmp.name);files={'campaign':campaign(),'source':D.passport('SRC-T','Test',field='ceiling',units='tonnes/day'),
                                       'observation':observation(),'relationship':relationship()}
        for name,record in files.items():(tmp/f'{name}.json').write_text(json.dumps(record),encoding='utf-8')
        out=io.StringIO()
        with redirect_stdout(out):
            main(['init',str(tmp/'c.jsonl'),str(tmp/'campaign.json')])
            for name in ('source','observation','relationship'):main(['add',str(tmp/'c.jsonl'),name,str(tmp/f'{name}.json')])
            main(['validate',str(tmp/'c.jsonl')]);main(['summary',str(tmp/'c.jsonl')])
        self.assertIn('chain_and_rules',out.getvalue())
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):main(['add',str(tmp/'c.jsonl'),'observation',str(tmp/'observation.json')])
        for kind in R.KEYS:self.assertEqual(list(R.template(kind)),list(R.KEYS[kind]))
        stages=re.findall(r'^## `([a-z-]+)`',(ROOT/'docs/strategy/discovery_lab_prompts.md').read_text(encoding='utf-8'),re.M)
        for stage in ('observation-first','relationship-first','event-first','hypothesis-first','sceptic-measurement','sceptic-information','next-evidence'):
            self.assertIn(stage,stages);self.assertTrue(prompt(stage))


if __name__=='__main__':unittest.main()
