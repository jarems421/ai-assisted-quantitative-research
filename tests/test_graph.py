import builtins,contextlib,copy,hashlib,io,json,os,shutil,socket,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from src.research.discovery import records as R
from src.research.discovery.demo import Clock,clk,entity,passport,rec,syn,observation_first
from src.research.discovery.ledger import Ledger
from src.research.graph import catalogue as C,cli as GCLI,demo as D,evaluate as E,implementation as I,model as M,operators as O,pilot as P,pilot_dryrun as DR,render as RN
from src.research.graph import pilot_r4_dryrun as R4
from src.research.graph.fixtures import AUTHORITY,ECHO,T7,build_all,campaign,obs
from src.research.graph.project import GraphError,build
from src.research.graph.rules import View,find_paths,verified_assertion

ROOT=Path(__file__).resolve().parents[1]
K_ECONOMIC='ECONOMIC_CONNECTION_CANDIDATE'
V=View()


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name);self.paths=build_all(self.dir,Clock())
        self.abc=[self.paths['A'],self.paths['B'],self.paths['C']]

    def syn_graph(self,ledgers=None,**kw):
        return build(ledgers or self.abc,mode='synthetic',with_memory=False,**kw)

    def extra(self,cid,records,fixture='SYNTHETIC',method='OBSERVATION_FIRST'):
        """A small extra ledger: campaign plus passport plus the given (kind, record) pairs."""
        c=campaign(cid,'Extra test campaign',method,'Test question?');c['fixture']=fixture
        if fixture!='SYNTHETIC':c['authority']='docs/strategy/owner_graph_v1_2026-10-21.md'
        led=Ledger.create(self.dir/f'{cid}.jsonl',c,Clock())
        from src.research.discovery.demo import passport
        p=passport('SRC-X','Extra source',field='f',units='u')
        if fixture!='SYNTHETIC':
            for q in p['quantities']+p['identifiers']:
                for ev in q['evidence']:ev.update(synthetic=False,reused_from='docs/strategy/x.md' if fixture=='RETROSPECTIVE_INSPECTED' else None)
            for key in ('history','revision_policy','publication_clock'):
                for ev in p[key]['evidence']:ev.update(synthetic=False,reused_from='docs/strategy/x.md' if fixture=='RETROSPECTIVE_INSPECTED' else None)
        led.append('source',p)
        for kind,r in records:
            if kind=='freeze':led.freeze(r)
            else:led.append(kind,r)
        return led.path

    # 1-3 integrity and identity of inputs
    def test_tampered_ledger_refuses_build(self):
        lines=self.paths['A'].read_bytes().splitlines();i=next(k for k,l in enumerate(lines) if b'2.0 Mt/year' in l)
        lines[i]=lines[i].replace(b'2.0 Mt/year',b'9.0 Mt/year')
        self.paths['A'].write_bytes(b'\n'.join(lines)+b'\n')
        with self.assertRaisesRegex(GraphError,'failed replay'):self.syn_graph()

    def test_duplicate_campaign_ids_refused(self):
        copy_=self.dir/'copy.jsonl';shutil.copy(self.paths['A'],copy_)
        with self.assertRaisesRegex(GraphError,'duplicate campaign id'):self.syn_graph([self.paths['A'],copy_])

    def test_namespaced_identities_are_stable_and_distinct(self):
        other=self.extra('DLC-GSYN-X',[('observation',obs('OBS-GA-1','SRC-X','Same local id, other campaign.',1,'u',
                                                          entity('FACILITY','SYN_FACILITY:Z-1','Zed'),'2000-01-01','2000-01-02','2000-02-01T00:00:00+00:00','x'))])
        g1=self.syn_graph(self.abc+[other]);g2=self.syn_graph(self.abc+[other])
        self.assertIn('observation:DLC-GSYN-A/OBS-GA-1@1',g1.nodes);self.assertIn('observation:DLC-GSYN-X/OBS-GA-1@1',g1.nodes)
        self.assertEqual(sorted(g1.nodes),sorted(g2.nodes))

    # 4-6 entity identity
    def test_similar_names_and_name_only_entities_never_merge(self):
        g=self.syn_graph()
        self.assertIn('entity:SYN_FACILITY:T-7',g.nodes);self.assertIn('entity:SYN_FACILITY:T-7B',g.nodes)
        pairs=[set(i['entities']) for i in g.issues if i['code']=='IDENTITY_QUESTION']
        self.assertIn({'entity:SYN_FACILITY:T-7','entity:SYN_FACILITY:T-7B'},pairs)
        other=self.extra('DLC-GSYN-Y',[('observation',obs('OBS-Y-1','SRC-X','Named company again.','x','status',
                                                         entity('LISTED_COMPANY','NAME:Echo Logistics','Echo Logistics'),'2000-07-05','2000-07-05','2000-08-02T00:00:00+00:00','x',kind='EVENT'))])
        g=self.syn_graph(self.abc+[other])
        self.assertIn('entity:NAME:DLC-GSYN-C/Echo Logistics',g.nodes);self.assertIn('entity:NAME:DLC-GSYN-Y/Echo Logistics',g.nodes)

    def test_ticker_is_not_a_legal_entity_identity(self):
        g=self.syn_graph();n=g.nodes['entity:TICKER:ECHO']
        self.assertEqual(n['attrs']['identity_status'],'TICKER_ONLY');self.assertNotEqual('entity:TICKER:ECHO','entity:SYN_LISTED:ECHO')
        self.assertTrue(any('ticker' in r.lower() for r in n['restrictions']))
        self.assertEqual(O.complements(g,'OBS-GC-4',V)['abstentions'][0]['code'],'NO_VERIFIED_IDENTITY')

    def test_cross_ledger_entity_type_conflict_is_exposed(self):
        other=self.extra('DLC-GSYN-T',[('observation',obs('OBS-T-1','SRC-X','Terminal Seven recorded as an asset.',1,'u',
                                                         entity('ASSET','SYN_FACILITY:T-7','Synthetic Terminal Seven'),'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x'))])
        g=self.syn_graph(self.abc+[other])
        self.assertTrue(any(i['code']=='ENTITY_TYPE_CONFLICT' and i['node']=='entity:SYN_FACILITY:T-7' for i in g.issues))
        leaps={p['first_unsupported_leap']['code'] for p in O.explain(g,'OBS-GB-1','SYN_LISTED:ECHO',V)['results']}
        self.assertIn('ENTITY_TYPE_CONFLICT',leaps)

    # 7-11 assertion-level verification
    def test_relationship_and_allocation_are_separate_assertions(self):
        rel=rec('relationship',id='REL-U-1',source_entity=ECHO,target_entity=T7,type='SUPPLIER_CUSTOMER',direction='Documented supply.',
                period={'start':'1990-01-01','end':'OPEN'},basis='DOCUMENTED',status='VERIFIED',evidence=[syn('u/rel','VERIFIED_ORIGINAL_RECORD')],
                quantity_transfer={'status':'UNVERIFIED','method':'PROPORTIONAL_ASSUMPTION','evidence':[],'note':'Share unknown.'})
        g=self.syn_graph(self.abc+[self.extra('DLC-GSYN-U',[('relationship',rel)])])
        n=g.nodes['relationship:DLC-GSYN-U/REL-U-1@1']
        self.assertEqual((n['status'],n['attrs']['allocation_status']),(M.DOCUMENTED_RELATIONSHIP,'ALLOCATION_UNVERIFIED'))
        self.assertEqual(g.nodes['relationship:DLC-GSYN-A/REL-GA-1@1']['attrs']['allocation_status'],'VERIFIED_ALLOCATION')

    def test_verified_path_does_not_certify_exposure(self):
        res=O.explain(self.syn_graph(),'OBS-GB-1','SYN_LISTED:ECHO',V)
        self.assertTrue(res['results'])
        for p in res['results']:
            self.assertTrue(p['connectivity_only']);self.assertFalse(p['exposure_certified']);self.assertFalse(p['causal_claim'])
        best=res['results'][0]
        self.assertEqual(best['first_unsupported_leap']['code'],'FINANCIAL_TRANSMISSION_UNVERIFIED')

    def test_document_reference_and_schema_do_not_verify_a_quantity(self):
        record=obs('OBS-R-1','SRC-X','Document seen, field not.',5,'u',T7,'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x',depth='VERIFIED_ORIGINAL_RECORD')
        schema=obs('OBS-R-2','SRC-X','Schema only.',R.UNKNOWN,'u',T7,'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x',depth='SCHEMA_ONLY')
        schema['evidence']=[syn('dict','SCHEMA_ONLY','SCHEMA')];schema['as_of_status']='UNVERIFIED'
        g=self.syn_graph(self.abc+[self.extra('DLC-GSYN-R',[('observation',record),('observation',schema)])])
        a,b=g.nodes['observation:DLC-GSYN-R/OBS-R-1@1'],g.nodes['observation:DLC-GSYN-R/OBS-R-2@1']
        self.assertEqual((a['status'],a['reasons']),(M.ORIGINAL_DOCUMENT_REFERENCED,['DOCUMENT_SEEN_FIELD_NOT_VERIFIED']))
        self.assertEqual((b['status'],b['reasons']),(M.RECORDED_UNVERIFIED,['SCHEMA_ONLY']))
        self.assertFalse(verified_assertion(a) or verified_assertion(b))
        lead=[r for r in O.revisit(g,'OBS-R-2',V)['results'] if r['match'].startswith('claim:DLC-GSYN-A')][0]
        self.assertFalse(lead['field_visible'])

    def test_retrospective_description_stays_unverified(self):
        o=obs('OBS-Q-1','SRC-X','Later account of an earlier state.','described','status',T7,'2000-06-30',R.UNKNOWN,R.UNKNOWN,'x',depth='RETROSPECTIVE_DESCRIPTION')
        o['evidence']=[{**syn('later','RETROSPECTIVE_DESCRIPTION','RETROSPECTIVE_ACCOUNT'),'synthetic':False,'reused_from':'docs/strategy/x.md'}]
        o['clocks']['economic_occurrence']['evidence']=[{**e,'synthetic':False,'reused_from':'docs/strategy/x.md'} for e in o['clocks']['economic_occurrence']['evidence']]
        o['as_of_status']='UNVERIFIED'
        g=build([self.extra('DLC-RETRO-Q',[('observation',o)],fixture='RETROSPECTIVE_INSPECTED')],mode='memory')
        n=g.nodes['observation:DLC-RETRO-Q/OBS-Q-1@1']
        self.assertEqual((n['status'],n['reasons'],n['fixture']),(M.RECORDED_UNVERIFIED,['RETROSPECTIVE_ONLY'],'RETROSPECTIVE_INSPECTED'))
        self.assertFalse(any(x['kind']=='observation' and x['fixture']=='HISTORICAL_MEMORY' for x in g.nodes.values()))

    # 12-15 time
    def test_unknown_clocks_stay_unknown_and_first_public_is_never_derived(self):
        g=self.syn_graph();a=g.nodes['observation:DLC-GSYN-A/OBS-GA-1@1']['attrs']
        self.assertEqual(a['clocks']['first_public'],{'value':R.UNKNOWN,'basis':R.UNKNOWN});self.assertFalse(a['first_public_certified'])
        b=g.nodes['observation:DLC-GSYN-B/OBS-GB-1@1']['attrs'];self.assertEqual(b['clocks']['first_public']['value'],'2000-07-10')
        gc=O.revisit(g,'OBS-GC-1',V)
        for r in O.revisit(self.syn_graph(),'OBS-GA-1',V)['results']+gc['results']:
            self.assertEqual(r['time']['first_public'],R.UNKNOWN);self.assertIn('historical availability (first-public time UNKNOWN)',r['not_yet_verified'])

    def test_modern_relationship_is_not_applied_to_an_earlier_date(self):
        g=self.syn_graph()
        self.assertIn('PERIOD_INCOMPATIBLE',[x['code'] for x in O.complements(g,'OBS-GC-3',V)['rejected']])
        rel='relationship:DLC-GSYN-A/REL-GA-2@1'
        from src.research.graph.rules import visible
        self.assertEqual(visible(g,rel,View(as_of='2000-06-30')),(False,'PERIOD_INCOMPATIBLE'))
        self.assertTrue(visible(g,rel,View(as_of='2012-01-01'))[0])

    def test_transcription_time_is_not_backdated(self):
        g=build(ledgers=[]);cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        h=g.nodes['history:HIST-F01']
        self.assertEqual(h['origin']['catalogue_recorded_at_utc'],cat['recorded_at_utc'])
        self.assertEqual(h['attrs']['historical_closure']['date'],'2026-10-20')
        early=build(ledgers=[],known_at='2026-10-20')
        self.assertFalse(any(n['kind'].startswith('history') for n in early.nodes.values()))
        self.assertTrue(any('catalogue recorded after' in x['reason'] for x in early.excluded))
        g2=self.syn_graph(known_at='2000-01-01T00:08:00+00:00')
        self.assertEqual([x['campaign'] for x in g2.inputs],['DLC-GSYN-A'])

    # 16-17 independence
    def test_shared_document_is_one_document_and_never_independent_corroboration(self):
        same=syn('contracts/TOP-7','VERIFIED_ORIGINAL_RECORD')
        o=obs('OBS-S-1','SRC-X','Cites the same contract file.',1,'u',entity('FACILITY','SYN_FACILITY:S-1','Sea One'),'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x')
        o['evidence'].append(same)
        g=self.syn_graph(self.abc+[self.extra('DLC-GSYN-S2',[('observation',o)])])
        doc=f"document:sha256:{same['sha256']}"
        citers={x for e,x,d in g.neighbours(doc) if e['kind']=='CITES'}
        self.assertEqual(len([k for k in g.nodes if k==doc]),1);self.assertGreaterEqual(len(citers),2)
        res=O.shared(g,'OBS-S-1',V)['results'][0]
        self.assertEqual(res['classification'],'SAME_SOURCE_REUSE');self.assertIn('SOURCE_INDEPENDENCE_UNKNOWN',res['independence'])
        self.assertTrue(all(n['attrs']['independence']=='NOT_ASSESSED' for n in g.nodes.values() if n['kind']=='document'))

    # 18-21 versions
    def test_frozen_claim_keeps_its_version_references(self):
        led=Ledger(self.paths['A']);o=copy.deepcopy(led.load().latest('observation','OBS-GA-1'))
        o.update(version=2,supersedes=1,revision_reason='Corrected throughput.',value=1.8)
        led.append('observation',o)
        g=self.syn_graph()
        targets=[x for e,x,d in g.neighbours('claim:DLC-GSYN-A/CAND-GA-1@1') if e['kind']=='PREDICTS_WITH']
        self.assertEqual(targets,['observation:DLC-GSYN-A/OBS-GA-1@1'])
        self.assertTrue(any(r['code']=='REFERENCE_REVISED_AFTER_FREEZE' for r in O.changes(g)['results']))

    def test_reformulations_stay_distinct_from_originals(self):
        path=self.dir/'obs.jsonl';observation_first(type('W',(),{'lines':[],'h':lambda *a:None,'say':lambda *a:None,'ok':lambda s,l,e:e,
                                                                   'refuse':lambda s,l,a:None,'checklist':lambda *a:None})(),path,Clock())
        g=build([path],mode='synthetic',with_memory=False,)
        v1,v3=g.nodes['claim:DLC-SYN-OBS/CAND-SYN-OBS-1@1'],g.nodes['claim:DLC-SYN-OBS/CAND-SYN-OBS-1@3']
        self.assertEqual((v1['attrs']['claim_class'],v3['attrs']['claim_class']),('ORIGINAL','REFORMULATION'))
        self.assertTrue(v3['attrs']['post_outcome'])
        mem=build(ledgers=[])
        self.assertFalse(mem.nodes['history:HIST-EF06/claim-v2']['attrs']['counts_as_original'])

    def test_contradicted_and_superseded_records_remain_inspectable(self):
        rel=rec('relationship',id='REL-K-1',source_entity=ECHO,target_entity=T7,type='OPERATION',direction='Disputed.',
                period={'start':'1990-01-01','end':'OPEN'},basis='DOCUMENTED',status='CONTRADICTED',evidence=[syn('k','VERIFIED_ORIGINAL_RECORD')])
        o=obs('OBS-K-1','SRC-X','First version.',1,'u',T7,'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x')
        o2=dict(copy.deepcopy(o),version=2,supersedes=1,revision_reason='Correction.',value=2)
        g=self.syn_graph(self.abc+[self.extra('DLC-GSYN-K',[('relationship',rel),('observation',o),('observation',o2)])])
        from src.research.graph.rules import visible
        self.assertEqual(g.display_status('relationship:DLC-GSYN-K/REL-K-1@1'),M.CONTRADICTED)
        self.assertTrue(visible(g,'relationship:DLC-GSYN-K/REL-K-1@1',V)[0])
        old='observation:DLC-GSYN-K/OBS-K-1@1'
        self.assertEqual(visible(g,old,V),(False,'SUPERSEDED'));self.assertTrue(visible(g,old,View(history=True))[0])
        codes={(r['code'],r.get('node')) for r in O.changes(g)['results']}
        self.assertIn(('CONTRADICTED_RECORD','relationship:DLC-GSYN-K/REL-K-1@1'),codes);self.assertIn(('SUPERSEDED',old),codes)

    # 22-23 modes
    def test_synthetic_never_enters_memory_or_prospective_views(self):
        for mode in ('memory','prospective'):
            g=build(self.abc,mode=mode)
            self.assertFalse(any(n['fixture']=='SYNTHETIC' for n in g.nodes.values()))
            self.assertEqual(len(g.excluded) - (1 if mode=='prospective' else 0),3)
        self.assertFalse(any(n['kind'].startswith('history') for n in build(self.abc,mode='prospective').nodes.values()))

    def test_retrospective_and_historical_records_are_labelled(self):
        g=build(ledgers=[])
        for n in g.nodes.values():
            if n['kind'].startswith('history'):
                self.assertEqual(n['fixture'],'HISTORICAL_MEMORY');self.assertTrue(n['restrictions'])
        self.assertTrue(all(r['fixture']=='HISTORICAL_MEMORY' for r in O.search(g,'capacity',V)['results'] if r['kind'].startswith('history')))
        hidden=O.search(g,'capacity',View(exclude_retrospective=True))['results']
        self.assertFalse([r for r in hidden if r['kind'].startswith('history')])

    # 24-27 traversal
    def test_entity_nodes_do_not_block_verified_traversal(self):
        g=self.syn_graph();paths,_=find_paths(g,'observation:DLC-GSYN-B/OBS-GB-1@1','entity:SYN_LISTED:ECHO',V,semantic=1)
        via_rel=[p for p in paths if 'relationship:DLC-GSYN-A/REL-GA-1@1' in p['nodes']]
        self.assertTrue(via_rel);self.assertEqual((via_rel[0]['semantic_hops'],via_rel[0]['structural_edges']),(1,3))

    def test_structural_steps_do_not_reject_short_semantic_paths(self):
        g=self.syn_graph();paths,bounds=find_paths(g,'observation:DLC-GSYN-B/OBS-GB-1@1','entity:SYN_FACILITY:T-9',V,semantic=2)
        self.assertTrue(any(p['semantic_hops']==2 and p['structural_edges']==5 for p in paths))
        self.assertEqual(bounds['structural_limit'],8)

    def test_long_paths_are_capped_and_never_self_certify(self):
        res=O.explain(self.syn_graph(),'OBS-GB-1','SYN_FACILITY:T-9',V,semantic=10)
        self.assertEqual(res['bounds']['semantic_limit'],M.MAX_SEMANTIC_HOPS)
        self.assertTrue(all(p['connectivity_only'] and not p['exposure_certified'] for p in res['results']))
        self.assertLessEqual(len(res['results']),M.MAX_PATHS)

    def test_high_degree_hubs_do_not_bridge_results(self):
        g=build([self.paths['H']],mode='synthetic',with_memory=False)
        self.assertGreater(g.degree('entity:SYN_REGULATOR:R-1'),M.HUB_DEGREE)
        self.assertEqual(O.explain(g,'OBS-GH-00','OBS-GH-01',V)['abstentions'][0]['code'],'NO_PATH_WITHIN_BOUNDS')
        nb=O.neighbourhood(g,'OBS-GH-00',V)['results'][0]
        self.assertIn('entity:SYN_REGULATOR:R-1',[c['node'] for c in nb['collapsed']])
        self.assertLessEqual(len(nb['nodes']),M.MAX_NODES)
        self.assertIn('entity:SYN_REGULATOR:R-1',[r['node'] for r in O.search(g,'regulator one',V)['results']])

    # 28-31 suggestions
    def test_keywords_and_unknown_tags_create_no_links(self):
        g=self.syn_graph();res=O.revisit(g,'OBS-GC-1',V)
        self.assertFalse(res['results'])
        self.assertIn('ONLY_SHARED_KEYWORD',[x['code'] for x in res['rejected']]);self.assertIn('UNKNOWN_TAG',[x['code'] for x in res['rejected']])
        self.assertFalse([e for e in g.edges if e['src']=='observation:DLC-GSYN-C/OBS-GC-1@1' and e['kind']=='MAY_MEASURE'])
        self.assertTrue(any(i['code']=='UNKNOWN_TAG' for i in g.issues))

    def test_suggestions_never_become_verified_relationships(self):
        g=self.syn_graph();before=g.digest();relationships={k for k,n in g.nodes.items() if n['kind']=='relationship'}
        hashes={k:sha(p) for k,p in self.paths.items()}
        for op in (lambda:O.revisit(g,'DLC-GSYN-B',V),lambda:O.complements(g,'OBS-GB-1',V),lambda:O.shared(g,'DLC-GSYN-B',V),
                   lambda:O.next_questions(g,V),lambda:O.changes(g)):
            for r in op()['results']:
                if 'status' in r and r.get('suggestion_id'):self.assertEqual(r['status'],M.SUGGESTION_ONLY)
        self.assertEqual(g.digest(),before);self.assertEqual({k for k,n in g.nodes.items() if n['kind']=='relationship'},relationships)
        self.assertEqual(hashes,{k:sha(p) for k,p in self.paths.items()})

    def test_new_campaign_yields_an_explainable_cross_campaign_suggestion(self):
        res=O.revisit(self.syn_graph(),'DLC-GSYN-B',V)['results']
        self.assertEqual(res[0]['match'],'claim:DLC-GSYN-A/CAND-GA-1@1')
        self.assertEqual(res[0]['strength'],'EXACT_ENTITY_ID');self.assertIn('entity:SYN_FACILITY:T-7',res[0]['via'])
        self.assertTrue(res[0]['previous_status_stands']);self.assertEqual(res[0]['previous_status'],'HOLD')

    # 32-36 historical memory
    def test_historical_states_are_preserved_verbatim(self):
        g=build(ledgers=[]);cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        for inv in cat['investigations']:self.assertEqual(g.nodes[f"history:{inv['id']}"]['attrs']['verdict']['text'],inv['verdict']['text'])
        self.assertIn('STOP',g.nodes['history:HIST-SH09']['attrs']['verdict']['text'])
        self.assertEqual(g.nodes['history:HIST-F19']['attrs']['verdict']['status_class'],'HOLD')

    def test_f01_and_sh09_gain_no_fictional_economic_facts(self):
        g=build(ledgers=[])
        self.assertFalse([k for k,n in g.nodes.items() if n['kind'] in ('observation','relationship','claim')])
        res=O.explain(g,'HIST-SH09','CIK:0000093410',V)
        self.assertEqual(res['results'][0]['first_unsupported_leap']['code'],'NO_ECONOMIC_ASSERTION_ON_PATH')
        self.assertTrue(all(r['state']!='VERIFIED' for r in O.gaps(g,'history:HIST-SH09/claim-v1')['results']))
        self.assertTrue(all(r['kind'] in ('history','history_claim','history_finding','requirement','entity') for r in O.search(g,'treatment',V)['results']))

    def test_ef06_versions_are_separate_economic_objects(self):
        g=build(ledgers=[]);v1,v2=g.nodes['history:HIST-EF06/claim-v1'],g.nodes['history:HIST-EF06/claim-v2']
        self.assertEqual((v1['attrs']['financial_basis'],v2['attrs']['financial_basis']),('RETAINED_NET','GROSS'))
        self.assertIn(('REFORMULATES','history:HIST-EF06/claim-v2','history:HIST-EF06/claim-v1'),{(e['kind'],e['src'],e['dst']) for e in g.edges})
        self.assertTrue(v1['attrs']['counts_as_original']);self.assertFalse(v2['attrs']['counts_as_original'])

    def test_missing_and_changed_reports_are_flagged_not_filled(self):
        root=self.dir/'root';cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        for p in cat['report_hashes']:
            (root/p).parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/p,root/p)
        (root/'docs/strategy/discovery_bottleneck_report.md').unlink()
        sal=root/'docs/strategy/salmon_verification_final_report.md';sal.write_text(sal.read_text(encoding='utf-8').replace('spare capacity','free slots'),encoding='utf-8')
        cards=root/'docs/strategy/measurement_gate_campaign_cards.md';cards.write_text(cards.read_text(encoding='utf-8')+'\nappended\n',encoding='utf-8')
        loaded,issues=C.load(C.CATALOGUE_PATH,root)
        codes={i['code'] for i in issues}
        self.assertTrue({'MISSING_SOURCE_DOCUMENT','STALE_CITATION','CITATION_HASH_CHANGED'}<=codes)
        self.assertEqual(loaded['_citation_status']['HIST-F19'],'MISSING');self.assertEqual(loaded['_citation_status']['HIST-F01'],'STALE')

    def test_corrupted_catalogue_refuses_build(self):
        cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        for mutate in (lambda c:c['investigations'][0]['findings'][0].update(requirement='REQ_INVENTED'),
                       lambda c:c['investigations'][1]['documents'][0].update(sha256='0'*64),
                       lambda c:c['investigations'][0]['verdict']['citation'].update(path='data/raw/secret.json'),
                       lambda c:c['investigations'][2]['claims'][1].update(counts_as_original=True),
                       lambda c:c.update(status='AUTHORITATIVE')):
            bad=copy.deepcopy(cat);mutate(bad);path=self.dir/'bad.json';path.write_text(json.dumps(bad),encoding='utf-8')
            with self.assertRaises(GraphError):build(ledgers=[],catalogue_path=path)

    # 37-42 boundaries and determinism
    def test_reads_only_declared_inputs_and_never_private_archives(self):
        opened=[];real=builtins.open
        def spy(path,*a,**k):
            if not isinstance(path,int):opened.append(str(Path(path).resolve()))
            return real(path,*a,**k)
        real_read=Path.read_bytes;real_text=Path.read_text
        def rb(self_):opened.append(str(self_.resolve()));return real_read(self_)
        def rt(self_,*a,**k):opened.append(str(self_.resolve()));return real_text(self_,*a,**k)
        with patch.object(builtins,'open',spy),patch.object(Path,'read_bytes',rb),patch.object(Path,'read_text',rt):
            g=build(self.abc,mode='synthetic');RN.mermaid(g,O.neighbourhood(g,'OBS-GB-1',V))
        cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        allowed={str(p.resolve()) for p in self.abc}|{str(C.CATALOGUE_PATH.resolve()),str((ROOT/cat['supersedes']['path']).resolve())}
        allowed|={str((ROOT/p).resolve()) for p in cat['report_hashes']}
        self.assertTrue(set(opened)<=allowed,set(opened)-allowed)
        self.assertFalse(any('data' in Path(p).parts and 'raw' in Path(p).parts for p in opened))
        self.assertNotIn('PRIVATE_AUTH',C.CATALOGUE_PATH.read_text(encoding='utf-8'))

    def test_graph_operations_are_offline(self):
        def blocked(*a,**k):raise AssertionError('network attempted')
        with patch.object(socket.socket,'connect',blocked),patch.object(socket,'create_connection',blocked):
            g=build(self.abc,mode='synthetic',with_memory=True)
            for f in (lambda:O.search(g,'terminal',V),lambda:O.show(g,'OBS-GB-1',V),lambda:O.neighbourhood(g,'OBS-GB-1',V),
                      lambda:O.explain(g,'OBS-GB-1','SYN_LISTED:ECHO',V),lambda:O.trace(g,'CAND-GA-1',V),lambda:O.shared(g,'DLC-GSYN-B',V),
                      lambda:O.complements(g,'OBS-GB-1',V),lambda:O.same_gap(g,'REQ_REALISED_ACTIVITY',V),lambda:O.gaps(g,'CAND-GA-1',V),
                      lambda:O.revisit(g,'DLC-GSYN-B',V),lambda:O.changes(g),lambda:O.failures(g,V),lambda:O.orphans(g,V),lambda:O.next_questions(g,V)):
                self.assertEqual(f()['banner'],M.BANNER)

    def test_build_is_deterministic_across_locations(self):
        other=Path(self.tmp.name)/'second';other.mkdir();paths2=build_all(other,Clock())
        g1=self.syn_graph();g2=self.syn_graph([paths2['A'],paths2['B'],paths2['C']])
        self.assertEqual(g1.digest(),g2.digest());self.assertEqual(build(ledgers=[]).digest(),build(ledgers=[]).digest())

    def test_empty_and_unrelated_inputs_abstain(self):
        g=build(ledgers=[],catalogue_path=None)
        self.assertEqual(len(g.nodes),0)
        self.assertEqual(O.next_questions(g,V)['abstentions'][0]['code'],'NO_OPEN_CLAIMS')
        self.assertEqual(O.search(g,'anything',V)['abstentions'][0]['code'],'NO_USEFUL_SUGGESTION')
        with self.assertRaises(O.NotFound):O.show(g,'OBS-1',V)
        lone=self.extra('DLC-GSYN-L',[('observation',obs('OBS-L-1','SRC-X','Unrelated quarry output.',3,'t',entity('FACILITY','SYN_FACILITY:Q-1','Quarry'),
                                                         '2000-01-01','2000-01-02','2000-02-01T00:00:00+00:00','x'))])
        g=self.syn_graph(self.abc+[lone])
        self.assertEqual(O.revisit(g,'DLC-GSYN-L',V)['abstentions'][0]['code'],'NO_USEFUL_SUGGESTION')
        self.assertIn('observation:DLC-GSYN-L/OBS-L-1@1',[r['node'] for r in O.orphans(g,V)['results'] if r['state']=='STANDALONE_RETAINED'])

    # walkthrough, evaluation and pilot hooks
    def test_walkthrough_and_utility_check(self):
        self.assertEqual(D.check()['walkthrough'],'PASS')
        report=E.run(self.paths)
        graph=report['totals']['graph']
        self.assertEqual(graph.get('RECOVERED'),1);self.assertFalse(graph.get('FALSE_CONNECTION'));self.assertFalse(graph.get('PREMATURE_IDENTITY_JOIN'))
        self.assertNotIn('runtime_seconds',report)


class GraphReviewRegressionTests(unittest.TestCase):
    """Defects found in the pre-pilot review: catalogue mappings, archive-path identity, evaluation isolation, baseline fairness."""
    setUp=GraphTests.setUp;extra=GraphTests.extra;syn_graph=GraphTests.syn_graph

    def test_catalogue_v002_corrects_mappings_and_preserves_v001(self):
        v1_path=ROOT/'docs/strategy/graph/research_memory_catalogue.json'
        v1=json.loads(v1_path.read_text(encoding='utf-8'));v2=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        self.assertEqual(sha(v1_path),v2['supersedes']['sha256']);self.assertEqual(C.load(v1_path)[0]['version'],'GRAPH_MEMORY_CATALOGUE_V001')
        self.assertEqual({i['id']:i['verdict'] for i in v1['investigations']},{i['id']:i['verdict'] for i in v2['investigations']})
        f=lambda iid,fid:next(x for x in next(i for i in v2['investigations'] if i['id']==iid)['findings'] if x['id']==fid)
        req={r['id']:r for r in v2['requirements']}
        self.assertNotIn('qualified',req['REQ_REALISED_ACTIVITY']['definition'])
        self.assertEqual({f('HIST-F03','F1')['requirement'],f('HIST-F03','F2')['requirement']},{'REQ_QUALIFIED_COMMERCIAL_EXPOSURE'})
        for target in (('HIST-F19','F3'),('HIST-F03','F3')):
            self.assertEqual((f(*target)['kind'],f(*target)['requirement']),('ACQUISITION_LIMIT',None))
        self.assertFalse([x for i in v2['investigations'] for x in i['findings'] if x['kind']=='ACQUISITION_LIMIT' and x['requirement']])
        self.assertIn('recoverable-net',f('HIST-SH09','F4')['citation']['quote'])
        self.assertEqual(f('HIST-SH09','F10')['requirement'],'REQ_ENTITY_COHORT_JOIN')
        self.assertEqual(f('HIST-EF06','F2')['requirement'],'REQ_DOCUMENTED_ALLOCATION')
        self.assertTrue(all(c['reason'] for c in v2['mapping_corrections']))
        g=build(ledgers=[])
        self.assertNotIn('history:HIST-F03/claim-v1',{r['claim'] for r in O.same_gap(g,'REQ_REALISED_ACTIVITY',V)['results']})
        self.assertEqual({r['claim'] for r in O.same_gap(g,'REQ_HISTORICAL_SCHEDULE_OR_VERSION',V)['results']},{'history:HIST-SH09/claim-v1'})

    def test_archive_path_cik_is_not_a_corroborated_issuer_identity(self):
        g=build(ledgers=[]);n=g.nodes['entity:CIK:0000093410']
        self.assertEqual(n['attrs']['identity_status'],'ARCHIVE_PATH_IDENTIFIER')
        self.assertEqual((n['attrs']['types'],n['attrs']['memory_types']),([],['LISTED_COMPANY']))
        self.assertTrue(any('archive path' in r for r in n['restrictions']))
        self.assertNotIn('entity:NAME:HIST-F19/Voya Retirement Insurance and Annuity Company',{x for e,x,d in g.neighbours('entity:CIK:0001535929')})
        cat=json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))
        for e in [e for i in cat['investigations'] for e in i['entities'] if e['identity_basis'].startswith('SEC')]:
            self.assertIn(f"/edgar/data/{int(e['id'].split(':')[1])}/",e['name_citation']['quote'])
        bad=copy.deepcopy(cat);bad['investigations'][1]['entities'][0]['name_citation']={'path':'docs/strategy/sh09_verification_report.md','quote':'Chevron'}
        path=self.dir/'bad.json';path.write_text(json.dumps(bad),encoding='utf-8')
        with self.assertRaisesRegex(GraphError,'archive path'):build(ledgers=[],catalogue_path=path)

    def test_archive_path_join_carries_a_caveat_and_no_type_conflict(self):
        o=obs('OBS-V-1','SRC-X','Synthetic test observation about a registrant.',1,'u',entity('LEGAL_ENTITY','CIK:0000093410','Registrant'),
              '2023-12-20','2023-12-21','2024-01-05T00:00:00+00:00','x')
        g=build([self.extra('DLC-GSYN-V',[('observation',o)])],mode='synthetic',with_memory=True)
        self.assertFalse(any(i['code']=='ENTITY_TYPE_CONFLICT' for i in g.issues))
        self.assertEqual(g.nodes['entity:CIK:0000093410']['attrs']['identity_status'],'IDENTIFIED')
        leads=[r for r in O.revisit(g,'OBS-V-1',V)['results'] if r['match'].startswith('history:HIST-SH09')]
        self.assertTrue(leads);self.assertTrue(any('archive-path CIK' in x for x in leads[0]['not_yet_verified']))
        self.assertEqual(leads[0]['previous_status'],'STOP / M NOT PASSED / H NOT ESTABLISHED')

    def test_evaluation_reads_only_declared_inputs(self):
        def refuse(*a,**k):raise AssertionError('undeclared input read')
        with patch('src.research.graph.catalogue.load',refuse),patch('src.research.graph.project.discover_ledgers',refuse):
            report=E.run(self.paths)
        self.assertEqual(sorted(report['declared_inputs']['ledgers']),['A.jsonl','B.jsonl','C.jsonl'])
        self.assertIsNone(report['declared_inputs']['catalogue'])
        retro=self.extra('DLC-RETRO-Z',[],fixture='RETROSPECTIVE_INSPECTED')
        with self.assertRaisesRegex(ValueError,'isolation'):E.isolated_graph(self.abc+[retro])

    def test_structured_baseline_is_exact_temporal_and_identity_aware(self):
        from src.research.graph import baseline as B
        t7b=entity('FACILITY','SYN_FACILITY:T-7B','Synthetic Terminal Seven B')
        o=obs('OBS-D-1','SRC-X','Seven B throughput.',1,'Mt/quarter',t7b,'2000-06-30','2000-07-01','2000-08-01T00:00:00+00:00','x')
        cand=copy.deepcopy(Ledger(self.paths['A']).load().latest('candidate','CAND-GA-1'))
        cand.update(id='CAND-D-1',method='OBSERVATION_FIRST',entry_record='OBS-D-1',population='Terminal SYN_FACILITY:T-7B only.')
        cand['predictor']['observation_ids']=['OBS-D-1'];cand['exposure']['relationship_ids']=[];cand['missing_variables']=[]
        ledgers=self.abc+[self.extra('DLC-GSYN-D',[('observation',o),('candidate',cand)])]
        self.assertIn('DLC-GSYN-D/CAND-D-1',B.naive_text_search(ledgers,'DLC-GSYN-B','OBS-GB-1'))
        self.assertNotIn('DLC-GSYN-D/CAND-D-1',B.structured_search(ledgers,'DLC-GSYN-B','OBS-GB-1')['claims'])
        self.assertEqual(B.structured_search(self.abc,'DLC-GSYN-C','OBS-GC-3')['excluded_contexts'],
                         [{'record':'DLC-GSYN-A/REL-GA-2','reason':'PERIOD_INCOMPATIBLE'}])
        named=B.structured_search(self.abc,'DLC-GSYN-C','OBS-GC-2');self.assertTrue(named['identity_join_refused']);self.assertFalse(named['claims'])
        a_end=Ledger(self.paths['A']).load().events[-1]['recorded_at_utc']
        later={c['record'] for c in B.structured_search(self.abc,'DLC-GSYN-A','OBS-GA-1')['contexts']}
        earlier={c['record'] for c in B.structured_search(self.abc,'DLC-GSYN-A','OBS-GA-1',known_at=a_end)['contexts']}
        self.assertIn('DLC-GSYN-B/OBS-GB-1',later);self.assertNotIn('DLC-GSYN-B/OBS-GB-1',earlier)
        with self.assertRaisesRegex(ValueError,'not recorded'):B.structured_search(self.abc,'DLC-GSYN-B','OBS-GB-1',known_at=a_end)

    def test_pilot_export_gives_the_baseline_the_same_memory(self):
        g=build([self.paths['S']],mode='synthetic',with_memory=True);cat=C.load()[0]
        hist=[s for s in E.export_suggestions(g,'DLC-GSYN-S',[self.paths['S']],cat) if s['match'].startswith('history:')]
        self.assertTrue(hist);self.assertTrue(all(s['baseline_structured_discoverable'] for s in hist))
        without=E.export_suggestions(g,'DLC-GSYN-S',[self.paths['S']],None)
        self.assertFalse(any(s['baseline_structured_discoverable'] for s in without if s['match'].startswith('history:')))


class GraphPilotProtocolTests(unittest.TestCase):
    """Pilot protocol corrections: query-time visibility, equivalent inputs, isolation, blinding, accounting and decision rules."""

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=Path(self.tmp.name)
        self.clock=DR.Clock();self.d=self.dir/'P1'
        self.packet=Ledger.create(self.d/'packet.jsonl',DR.campaign('DLC-GPKT-1','packet'),self.clock)
        self.packet.append('source',passport('SRC-P-1','register',field='t',units='kt/month',publication='VERIFIED_ORIGINAL_RECORD'))
        self.packet.append('observation',DR.observation('OBS-P-1','Quay One throughput fell.',{'from':410,'to':265},'kt/month',
                                                        DR.doc('bundle/x',b'x'),'STATE_CHANGE',source='SRC-P-1'))
        self.packet.append('relationship',DR.relationship('REL-P-1'))
        self.bundle=self.dir/'bundle';self.bundle.mkdir();(self.bundle/'x.csv').write_bytes(b'x')
        self.clock.advance(1);frozen=self.clock.at();self.clock.advance(2)
        self.snap=self.d/'snapshot.json'
        P.make_snapshot(self.snap,'P1',self.d/'packet.jsonl',{'S':(self.d/'S.jsonl','DLC-GP1-S'),'G':(self.d/'G.jsonl','DLC-GP1-G')},self.bundle,frozen_at=frozen)

    def arm(self,arm):
        led=Ledger.create(self.d/f'{arm}.jsonl',DR.campaign(f'DLC-GP1-{arm}',arm),self.clock)
        led.append('source',passport('SRC-1','notices',field='b',units='berths',publication='VERIFIED_ORIGINAL_RECORD'))
        led.append('observation',DR.observation('OBS-1','Quay One berths closed.',3,'berths',DR.doc('arm/n',DR.NOTICE),'EVENT',
                                                '[MEASURES:REQ_REALISED_ACTIVITY] closure'))
        return led,self.clock.at()

    def refused(self,argv):
        err=io.StringIO()
        with contextlib.redirect_stderr(err),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as c:GCLI.main(argv)
        self.assertEqual(c.exception.code,2);return err.getvalue()

    def test_own_new_records_are_visible_and_later_records_are_not(self):
        led,t1=self.arm('G')
        g,view=P.arm_graph(self.snap,'G',t1)
        self.assertIn('observation:DLC-GP1-G/OBS-1@1',g.nodes)
        self.assertTrue(O.revisit(g,'OBS-1',V)['results']);self.assertTrue(O.complements(g,'OBS-1',V)['results'])
        self.assertTrue(E.export_suggestions(g,'DLC-GP1-G',view['ledgers'],C.load(view['catalogue'])[0],None,view['cuts']))
        start=led.load().events[0]['recorded_at_utc']
        old=build([self.d/'packet.jsonl',self.d/'G.jsonl'],mode='synthetic',known_at=start)
        self.assertNotIn('observation:DLC-GP1-G/OBS-1@1',old.nodes)  # the superseded single cutoff hides the current observation
        self.clock.advance(3);led.append('observation',DR.observation('OBS-2','later',1,'count',DR.doc('arm/l',b'l')))
        again,_=P.arm_graph(self.snap,'G',t1)
        self.assertEqual(again.digest(),g.digest());self.assertNotIn('observation:DLC-GP1-G/OBS-2@1',again.nodes)
        self.assertIn('observation:DLC-GP1-G/OBS-2@1',P.arm_graph(self.snap,'G',self.clock.at())[0].nodes)
        with self.assertRaisesRegex(P.PilotError,'future'):P.arm_view(self.snap,'G','2099-01-01T00:00:00+00:00')
        with self.assertRaisesRegex(P.PilotError,'precedes'):P.arm_view(self.snap,'G',DR.START.isoformat())

    def test_arms_share_identical_prior_inputs_and_never_see_each_other(self):
        from src.research.graph import baseline as B
        _,ts=self.arm('S');_,tg=self.arm('G')
        vs=P.arm_view(self.snap,'S',ts);gg,vg=P.arm_graph(self.snap,'G',tg)
        self.assertEqual(vs['receipt']['frozen_prior'],vg['receipt']['frozen_prior'])
        self.assertFalse([k for k in gg.nodes if 'DLC-GP1-S' in k])
        with self.assertRaisesRegex(ValueError,'not recorded'):B.structured_search(vg['ledgers'],'DLC-GP1-S','OBS-1',None,None,vg['cuts'])
        s_ctx=B.structured_search(vs['ledgers'],'DLC-GP1-S','OBS-1',C.load()[0],None,vs['cuts'])
        g_ctx=B.structured_search(vg['ledgers'],'DLC-GP1-G','OBS-1',C.load()[0],None,vg['cuts'])
        self.assertEqual([c['record'] for c in s_ctx['contexts']],[c['record'] for c in g_ctx['contexts']]);self.assertEqual(s_ctx['catalogue'],g_ctx['catalogue'])
        for arm in P.ARMS:shutil.copytree(self.bundle,self.dir/f'copy-{arm}')
        self.assertEqual(P.verify_summary(self.snap,self.dir/'copy-S'),P.verify_summary(self.snap,self.dir/'copy-G'))

    def test_snapshot_pins_packet_catalogue_bundle_and_arm_start(self):
        with self.assertRaisesRegex(P.PilotError,'already exists'):
            self.arm('S');P.make_snapshot(self.d/'again.json','P1',self.d/'packet.jsonl',{'S':(self.d/'S.jsonl','DLC-GP1-S'),'G':(self.d/'G2.jsonl','DLC-GP1-G')})
        shutil.copytree(self.bundle,self.dir/'tamper');(self.dir/'tamper/x.csv').write_bytes(b'y')
        with self.assertRaisesRegex(P.PilotError,'bundle differs'):P.load_snapshot(self.snap,self.dir/'tamper')
        s=json.loads(self.snap.read_text(encoding='utf-8'));s['prior']['catalogue']['sha256']='0'*64
        (self.d/'bad.json').write_text(json.dumps(s),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'catalogue differs'):P.load_snapshot(self.d/'bad.json')
        Ledger.create(self.d/'G.jsonl',DR.campaign('DLC-GP1-G','early'),lambda:'2026-10-21T12:31:00+00:00')
        with self.assertRaisesRegex(P.PilotError,'began before'):P.arm_view(self.snap,'G')
        self.packet.append('observation',DR.observation('OBS-P-2','late',1,'count',DR.doc('bundle/z',b'z'),source='SRC-P-1'))
        with self.assertRaisesRegex(P.PilotError,'changed after'):P.load_snapshot(self.snap)

    def test_cli_snapshot_mode_refuses_mixed_inputs_and_structured_graph_use(self):
        _,ts=self.arm('S');_,tg=self.arm('G');snap=['--snapshot',str(self.snap)]
        self.assertIn('uses no graph operator',self.refused(['revisit','OBS-1',*snap,'--arm','S','--query-at',ts]))
        self.assertIn('snapshot inputs are fixed',self.refused(['revisit','OBS-1',*snap,'--arm','G','--query-at',tg,'--ledgers',str(self.d/'S.jsonl')]))
        self.assertIn('snapshot inputs are fixed',self.refused(['revisit','OBS-1',*snap,'--arm','G','--known-at',tg]))
        self.assertIn('need --snapshot',self.refused(['revisit','OBS-1','--arm','G']))
        self.assertIn('needs --arm',self.refused(['revisit','OBS-1',*snap]))
        out=io.StringIO()
        with contextlib.redirect_stdout(out):GCLI.main(['baseline-search','DLC-GP1-S','OBS-1',*snap,'--arm','S','--query-at',ts])
        self.assertEqual(json.loads(out.getvalue())['visibility']['arm'],'S')

    def log(self,arm,**change):
        row={'connection_id':P.connection_id('a','b',['EXACT_ENTITY_ID']),'arm':arm,'kind':'CONNECTION','operator':'baseline-search',
             'found_via':'ANALYST_READING','source_record':f'DLC-GP1-{arm}/OBS-1','target_record':'DLC-GPKT-1/REL-P-1','basis':['EXACT_ENTITY_ID'],
             'arm_decision':'DECLINED','analyst_minutes':4,'discovery_lab_record':None,'recorded_at_utc':DR.START.isoformat(),'notes':''}
        return {**row,**change}

    def write_log(self,name,rows):
        path=self.d/name;path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8');return path

    def test_connection_logs_enforce_arm_rules(self):
        self.assertEqual(len(P.validate_connections(self.write_log('ok.jsonl',[self.log('S')]),'S')),1)
        sug='SUG-0123456789ab'
        bad=[{'connection_id':sug},{'found_via':'GRAPH_ONLY','operator':'revisit'},{'operator':'revisit'},{'arm_decision':'ACCEPTED'},
             {'discovery_lab_record':'CAND-1'},{'kind':'AVOIDED_REPEAT'},{'analyst_minutes':-1},{'arm':'G'},{'found_via':'MAGIC'}]
        for change in bad:
            with self.assertRaises(P.PilotError,msg=str(change)):P.validate_connections(self.write_log('bad.jsonl',[{**self.log('S'),**change}]),'S')
        with self.assertRaises(P.PilotError):P.validate_connections(self.write_log('dup.jsonl',[self.log('S'),self.log('S')]),'S')
        graph_row=self.log('G',connection_id=sug,operator='revisit',found_via='GRAPH_ONLY')
        self.assertEqual(len(P.validate_connections(self.write_log('g.jsonl',[graph_row]),'G')),1)

    def blinded(self):
        self.arm('S');self.arm('G')
        s=[self.log('S'),self.log('S',connection_id=P.connection_id('x','HIST-F01/claim-v1',['AUTHOR_TAG_CANDIDATE']),target_record='HIST-F01/claim-v1',
                                basis=['AUTHOR_TAG_CANDIDATE'])]
        g=[self.log('G',connection_id='SUG-0123456789ab',operator='complements',found_via='GRAPH_ONLY',target_record='relationship:DLC-GPKT-1/REL-P-1@1'),
           self.log('G',kind='AVOIDED_REPEAT',connection_id=P.connection_id('y','HIST-F01/F6',['AVOIDED']),operator='revisit',found_via='GRAPH_ONLY',
                    target_record='HIST-F01/F6',basis=['AVOIDED: vessel tracks'])]
        logs={'S':self.write_log('connections-S.jsonl',s),'G':self.write_log('connections-G.jsonl',g)}
        export=P.blind(self.snap,logs,'test-salt-0123456789',self.d/'blind.json',self.d/'key.json')
        return export,logs

    def test_blinding_hides_arms_and_adjudication_is_human_and_complete(self):
        export,logs=self.blinded();text=json.dumps(export['items'])
        self.assertEqual(len(export['items']),4)
        for leak in ('DLC-GP1-S','DLC-GP1-G','SUG-','CON-','GRAPH_ONLY','ANALYST_READING','"arm"','DECLINED','complements','baseline-search'):
            self.assertNotIn(leak,text)
        self.assertEqual(len({tuple(sorted(i['from'])) for i in export['items'] if i['from']['kind']=='observation'}),1)  # one rendering for both arms
        self.assertEqual(hashlib.sha256((self.d/'key.json').read_bytes()).hexdigest(),export['key_sha256'])
        rel=next(i for i in export['items'] if i['to']['kind']=='relationship')
        good=lambda i,**c:{'blind_id':i['blind_id'],'outcome':'REJECTED_TRIVIAL','economic_meaning':'NOT_MEANINGFUL','checked_evidence':[],
                           'adjudicator':'Owner','adjudicator_kind':'HUMAN','adjudicator_minutes':2,'recorded_at_utc':DR.START.isoformat(),'notes':'',**c}
        rows=[good(i) for i in export['items'] if i is not rel]
        adj=self.write_log('adjudications.jsonl',rows)
        with self.assertRaisesRegex(P.PilotError,'not adjudicated'):P.validate_adjudications(self.d/'blind.json',adj)
        sha=rel['to']['evidence'][0]['sha256']
        for change,why in (({'outcome':'CONFIRMED_AGAINST_ORIGINALS','checked_evidence':['f'*64]},'checked against'),({'adjudicator':'Claude'},'human'),
                           ({'outcome':'MAYBE'},'invalid outcome')):
            with self.assertRaisesRegex(P.PilotError,why):P.validate_adjudications(self.d/'blind.json',self.write_log('adjudications.jsonl',rows+[good(rel,**change)]))
        self.write_log('adjudications.jsonl',rows+[good(rel,outcome='CONFIRMED_AGAINST_ORIGINALS',economic_meaning='MEANINGFUL',checked_evidence=[sha])])
        live=dict(export,fixture='LIVE');(self.d/'live.json').write_text(json.dumps(live),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'human'):P.validate_adjudications(self.d/'live.json',self.write_log('fx.jsonl',[good(i,adjudicator_kind='SYNTHETIC_FIXTURE') for i in export['items']]))
        rows=P.unblind(self.d)
        self.assertEqual(sorted(r['arm'] for r in rows),['G','G','S','S'])
        (self.d/'key.json').write_bytes((self.d/'key.json').read_bytes()+b' ')
        with self.assertRaisesRegex(P.PilotError,'sealed'):P.unblind(self.d)

    def test_aliased_export_supports_adjudication_and_unblinding(self):
        export,_=self.blinded();before=sha(self.d/'blind.json')
        v2=P.alias_export(self.d/'blind.json',self.d/'blind_v2.json',self.dir/'alias.json')
        self.assertEqual(P.scan_leaks(v2['items'],P.own_records(export)),[])
        good=lambda i:{'blind_id':i['blind_id'],'outcome':'REJECTED_TRIVIAL','economic_meaning':'NOT_MEANINGFUL','checked_evidence':[],
                       'adjudicator':'Owner','adjudicator_kind':'HUMAN','adjudicator_minutes':1,'recorded_at_utc':DR.START.isoformat(),'notes':''}
        self.write_log('adjudications.jsonl',[good(i) for i in v2['items']])
        self.assertEqual(len(P.validate_adjudications(self.d/'blind_v2.json',self.d/'adjudications.jsonl')),4)
        self.assertEqual(sorted(r['arm'] for r in P.unblind(self.d,'blind_v2.json')),['G','G','S','S'])
        self.assertEqual(sha(self.d/'blind.json'),before)

    def test_blinding_refuses_endpoints_outside_the_arm_inputs(self):
        self.arm('S');self.arm('G')
        logs={'S':self.write_log('cs.jsonl',[self.log('S',target_record='DLC-GP1-G/OBS-1')]),'G':self.write_log('cg.jsonl',[])}
        with self.assertRaisesRegex(P.PilotError,'outside the arm S inputs'):P.blind(self.snap,logs,'test-salt-0123456789',self.d/'b.json',self.d/'k.json')

    def test_accounting_counts_all_time_and_flags_violations(self):
        s,_=self.arm('S');g,_=self.arm('G')
        eff=lambda i,cat,m,kind='ANALYST_TIME':DR.effort(f'EFF-{i}',cat,m,kind)
        s.append('effort',eff(1,'READING',10));s.append('effort',eff(2,'GRAPH_QUERY',5))
        s.append('effort',dict(eff(3,'READING',3),description='untagged'))
        for i in range(11):s.append('effort',eff(10+i,'SOURCE_SEARCH',1,'SEARCH'))
        acc=P.account(self.d/'S.jsonl','S')
        self.assertEqual(acc['used']['analyst_minutes'],29);self.assertEqual(acc['used']['searches'],11)
        self.assertEqual(sorted({v['code'] for v in acc['violations']}),['GRAPH_TIME_IN_STRUCTURED_ARM','OVER_CAMPAIGN_CEILING','UNCATEGORISED_EFFORT'])
        g.append('effort',eff(1,'GRAPH_QUERY',10));g.append('effort',eff(2,'SUGGESTION_REVIEW',5));g.append('effort',eff(3,'READING',20))
        acc=P.account(self.d/'G.jsonl','G')
        self.assertEqual((acc['used']['analyst_minutes'],acc['graph_minutes'],acc['violations']),(35,15,[]))

    def test_decision_rules_use_every_dimension(self):
        def arm(**kw):
            base={'analyst_minutes_all':120,'verified_connections':2,'verified_connections_per_hour':1.0,'graph_only_verified':0,
                  'false_or_premature_joins_made':2,'median_minutes_per_connection':6,'median_minutes_to_decisive_falsification':60,
                  'duplicate_research_avoided':0,'original_frozen_m_passes_per_hour':0.0,'review_burden_items':6,'adjudicator_minutes':12,
                  'graph_suggestions_false_or_trivial':[0,0]}
            return {**base,**kw}
        better=[{'S':arm(),'G':arm(false_or_premature_joins_made=0,median_minutes_to_decisive_falsification=40,graph_suggestions_false_or_trivial=[3,8])}]*4
        verdict,notes=P.classify(better)
        self.assertEqual(verdict,'GRAPH_INCREMENT_OBSERVED')  # with zero graph-only connections in every pair
        self.assertTrue(all(p['G']['graph_only_verified']==0 for p in better))
        worse=[{'S':arm(),'G':arm(verified_connections=1,verified_connections_per_hour=0.5,false_or_premature_joins_made=3)}]*4
        verdict,notes=P.classify(worse);self.assertEqual(verdict,'NO_GRAPH_INCREMENT_OBSERVED');self.assertIn('separate owner decision',notes[-1])
        mixed=[{'S':arm(),'G':arm(false_or_premature_joins_made=0,median_minutes_per_connection=9,duplicate_research_avoided=0)}]*2+\
              [{'S':arm(),'G':arm(median_minutes_per_connection=9,median_minutes_to_decisive_falsification=90)}]*2
        self.assertEqual(P.classify(mixed)[0],'INCONCLUSIVE')
        self.assertEqual(P.classify(better[:2])[0],'INCONCLUSIVE')
        noisy=[{'S':p['S'],'G':dict(p['G'],graph_suggestions_false_or_trivial=[9,10])} for p in better]
        self.assertEqual(P.classify(noisy)[0],'INCONCLUSIVE')
        self.assertEqual(P.classify(better,['cross-arm access'])[0],'INVALID_CRITICAL_STOP')

    def test_pilot_dry_run_record_is_current(self):
        self.assertEqual(DR.check()['dry_run'],'PASS')


class GraphPilotBlindingTests(unittest.TestCase):
    """Revision 3 blinding defect: arm-chosen record ids (OBS-G-7) and id styles leaked through V001 exports."""

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=Path(self.tmp.name)

    def endpoint(self,campaign,record,text,locator='https://example.org/doc',passage='p'):
        return {'kind':'observation','campaign':campaign,'record':record,'text':text,'entities':[{'id':'NAME:Firm','name':'Firm'}],
                'evidence':[{'locator':locator,'sha256':'a'*64,'depth':'VERIFIED_ORIGINAL_FIELD','passage':passage}],'tags':[],'value':3,'occurred':'2025-07-02'}

    def export(self):
        items=[{'blind_id':'ADJ-0000000001','kind':'CONNECTION',
                'from':self.endpoint('CURRENT_ARM_CAMPAIGN','OBS-G-7','Relies on REL-G-1 for CAND-G-1; filed by DLC-GP3-G.',
                                     'data/raw/graph_pilot_r3_20261021/P3/G/receipts/001.json','see OBS-G-7 and graph-pilot-r3/P3-G'),
                'to':self.endpoint('FROZEN_PACKET','OBS-P-1','Packet record OBS-P-1 cites HIST-F01/F6.'),
                'shared_structure':{'same_identified_entity':[],'shared_document_hashes':['a'*64],'shared_requirement_tags':[],'name_or_ticker_only_entities':[]}},
               {'blind_id':'ADJ-0000000002','kind':'AVOIDED_REPEAT','avoided_action':['not fetching OBS-MGA-SUBSIDIARIES again'],
                'from':self.endpoint('CURRENT_ARM_CAMPAIGN','OBS-MGA-SUBSIDIARIES','Descriptive id style OBS-MGA-SUBSIDIARIES; also OBS-G-7.'),
                'to':self.endpoint('HISTORICAL_MEMORY','HIST-F01/F6','Historical finding.'),
                'shared_structure':{'same_identified_entity':[],'shared_document_hashes':[],'shared_requirement_tags':[],'name_or_ticker_only_entities':[]}}]
        e={'version':P.BLIND_VERSION,'packet':'P3','fixture':'LIVE','snapshot_sha256':'b'*64,'key_sha256':'c'*64,'hidden_from_adjudicator':['arm'],
           'instructions':['adjudicate'],'items':items}
        path=self.dir/'blind.json';path.write_text(json.dumps(e),encoding='utf-8');return path,e

    def test_alias_export_removes_nested_arm_identifiers_and_keeps_evidence(self):
        path,e=self.export();before=sha(path)
        codes={f['code'] for f in P.scan_leaks(e['items'],P.own_records(e))}
        self.assertTrue({'ARM_LETTER_RECORD_ID','OWN_ARM_RECORD_ID','ARM_CAMPAIGN_ID','ARM_PATH','ARM_BRANCH'}<=codes)
        v2=P.alias_export(path,self.dir/'blind_v2.json',self.dir/'alias.json',secret='s'*32)
        self.assertEqual(sha(path),before)  # the V001 export is never rewritten
        self.assertEqual(P.scan_leaks(v2['items'],P.own_records(e)),[])
        self.assertEqual(P.scan_leaks(P.sheet(v2),P.own_records(e)),[])
        text=json.dumps(v2['items'])
        for leak in ('OBS-G-7','REL-G-1','CAND-G-1','DLC-GP3-G','/P3/G/','graph-pilot-r3','OBS-MGA-SUBSIDIARIES'):self.assertNotIn(leak,text)
        self.assertIn('OBS-P-1',text);self.assertIn('HIST-F01/F6',text);self.assertIn('/P3/ARM/',text)
        self.assertEqual([i['blind_id'] for i in v2['items']],['ADJ-0000000001','ADJ-0000000002'])
        self.assertEqual((v2['key_sha256'],v2['derived_from']['sha256']),(e['key_sha256'],before))
        a,b=v2['items']
        self.assertEqual(a['from']['evidence'][0]['sha256'],'a'*64);self.assertEqual((a['from']['value'],a['from']['occurred']),(3,'2025-07-02'))
        self.assertEqual(a['shared_structure'],e['items'][0]['shared_structure'])
        maps=json.loads((self.dir/'alias.json').read_text(encoding='utf-8'))['aliases']
        self.assertEqual(a['from']['record'],maps['ADJ-0000000001']['OBS-G-7']);self.assertIn(maps['ADJ-0000000001']['CAND-G-1'],a['from']['text'])
        self.assertNotEqual(maps['ADJ-0000000001']['OBS-G-7'],maps['ADJ-0000000002']['OBS-G-7'])  # per-item aliases: no cross-item linkage
        again=P.alias_export(path,self.dir/'again.json',self.dir/'alias2.json',secret='s'*32)
        self.assertEqual(again['items'],v2['items'])
        with self.assertRaises(FileExistsError):P.alias_export(path,self.dir/'blind_v2.json',self.dir/'alias3.json')
        with self.assertRaisesRegex(P.PilotError,'derives from'):P.alias_export(self.dir/'blind_v2.json',self.dir/'x.json',self.dir/'y.json')

    def test_leak_scan_recurses_into_keys_lists_and_text(self):
        nested={'a':[{'OBS-S-2':'x'},{'deep':['CON-0123456789ab','the G arm wrote this','see SUG-abcdef012345']}],'b':'GRAPH_ONLY and ACCEPTED',
                'c':'used revisit then baseline-search','d':'biographies; GRAPHIC exhibit; paragraph'}
        codes=sorted({f['code'] for f in P.scan_leaks(nested)})
        self.assertEqual(codes,['ARM_LABEL','ARM_LETTER_RECORD_ID','ATTRIBUTION_OR_DECISION','PILOT_CONNECTION_ID','TOOL_WORD'])
        self.assertFalse(P.scan_leaks({'d':'biographies; GRAPHIC exhibit; paragraph; OBS-P-1'}))
        self.assertTrue(P.scan_leaks('## item\n- From: `CURRENT_ARM_CAMPAIGN/OBS-7`',own_records=['OBS-7']))

    def test_committed_r3_exports_reproduce_the_defect_and_v2_presentations_are_clean(self):
        base=ROOT/'docs/strategy/graph_pilot_r3'
        for packet in ('P3','P4'):
            v1=json.loads((base/packet/'blind.json').read_text(encoding='utf-8'));own=P.own_records(v1)
            self.assertTrue(P.scan_leaks(v1['items'],own))  # the original presentation was compromised
            v2=json.loads((base/packet/'blind_v2.json').read_text(encoding='utf-8'))
            self.assertEqual(v2['derived_from']['sha256'],sha(base/packet/'blind.json'))
            self.assertEqual([i['blind_id'] for i in v2['items']],[i['blind_id'] for i in v1['items']])
            self.assertEqual(P.scan_leaks(v2['items'],own),[])
            self.assertEqual(P.scan_leaks((base/packet/'adjudication_sheet_v2.md').read_text(encoding='utf-8'),own),[])
            self.assertEqual((base/packet/'adjudication_sheet_v2.md').read_text(encoding='utf-8'),P.sheet(v2))


class GraphV11ConnectionClassTests(unittest.TestCase):
    """Graph v1.1: economic connection candidates, methodological warnings and unsupported matches (R3 used only as a diagnostic)."""

    def setUp(self):
        from src.research.graph import connections as K,quality as Q
        self.K,self.Q=K,Q
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=Path(self.tmp.name)
        self.paths=Q.build_fixtures(self.dir)
        self.g=build(self.paths,catalogue_path=None,mode='synthetic',with_memory=False,requirements=Q.VOCABULARY)

    def pick(self,res,match):
        return next(r for r in res['results'] if r['match'].startswith(match) or r['match']==match)

    def test_recall_and_unrelated_capacity_claim_share_only_a_warning(self):
        res=O.revisit(self.g,'DLC-QSYN-D/OBS-QD-1',V)
        w=self.pick(res,'claim:DLC-QSYN-H/CAND-QH-1')
        self.assertEqual(w['connection_class'],self.K.WARNING);self.assertNotIn('grounding',w)
        self.assertTrue(w['warning']['not_an_economic_connection']);self.assertEqual(w['warning']['shared_requirements'],['REQ_AVAILABLE_CAPACITY'])
        self.assertTrue(w['warning']['lesson'])
        self.assertEqual(res['connection_summary']['methodological_warnings'],1)

    def test_exact_product_identifier_is_a_grounded_candidate_and_outranks_tags(self):
        res=O.revisit(self.g,'DLC-QSYN-D/OBS-QD-1',V)
        e=self.pick(res,'claim:DLC-QSYN-R/CAND-QR-1')
        self.assertEqual(e['connection_class'],self.K.ECONOMIC)
        self.assertIn('AUTHOR_TAG_CANDIDATE',e['match_bases'])  # the weaker tag is kept, the class follows the stronger evidence
        gnd=e['grounding'];self.assertTrue(self.K.provenance_complete(e))
        self.assertEqual([b['basis'] for b in gnd['documented_basis']],['EXACT_ENTITY_ID'])
        self.assertIn('entity:SYN_PRODUCT:UDI-001',[j['object'] for j in gnd['joining_objects']])
        self.assertIn('financial exposure of any listed company',gnd['not_established'])
        classes=[r['connection_class'] for r in res['results']]
        self.assertEqual(classes,sorted(classes,key=self.K.CLASS_ORDER.get))  # grounded first, always

    def test_documented_supersession_is_grounded_and_period_checked(self):
        res=O.complements(self.g,'DLC-QSYN-D/OBS-QD-2',V)
        e=self.pick(res,'relationship:DLC-QSYN-R/REL-QR-1')
        self.assertEqual(e['connection_class'],self.K.ECONOMIC)
        self.assertEqual(e['grounding']['temporal']['relationship_period_covers_source'],'YES')
        self.assertIn('supersedes',json.dumps(e['grounding']['joining_objects']))
        self.assertEqual(e['grounding']['first_unsupported_inference']['code'],'FINANCIAL_TRANSMISSION_UNVERIFIED')

    def test_out_of_period_relationship_and_name_only_supplier_never_join(self):
        res=O.complements(self.g,'DLC-QSYN-D/OBS-QD-3',V)
        self.assertFalse(res['results']);self.assertIn('PERIOD_INCOMPATIBLE',[r['code'] for r in res['rejected']])
        res=O.complements(self.g,'DLC-QSYN-D/OBS-QD-4',V)
        self.assertFalse(res['results']);self.assertEqual(res['abstentions'][0]['code'],'NO_VERIFIED_IDENTITY')
        self.assertEqual(self.g.nodes['entity:NAME:DLC-QSYN-D/Acme Optics']['attrs']['identity_status'],'NAME_ONLY')

    def test_shared_document_is_not_corroboration_and_reused_citation_is_unsupported(self):
        independent=self.pick(O.shared(self.g,'DLC-QSYN-D/OBS-QD-6',V),'campaign:DLC-QSYN-R')
        self.assertEqual(independent['connection_class'],self.K.ECONOMIC)
        self.assertIn('NOT_INDEPENDENT_CORROBORATION',json.dumps(independent['grounding']['joining_objects']))
        copied=self.pick(O.shared(self.g,'DLC-QSYN-D/OBS-QD-5',V),'campaign:DLC-QSYN-R')
        self.assertEqual((copied['match_bases'],copied['connection_class']),(['REUSED_CITATION'],self.K.UNSUPPORTED))
        self.assertIn('unsupported',copied)

    def test_shared_allocation_blocker_and_next_questions_are_warnings_only(self):
        res=O.same_gap(self.g,'REQ_DOCUMENTED_ALLOCATION',V)
        self.assertEqual({r['claim'].split(':',1)[1].rsplit('@',1)[0] for r in res['results']},{'DLC-QSYN-H/CAND-QH-1','DLC-QSYN-D/CAND-QD-1'})
        self.assertTrue(all(r['connection_class']==self.K.WARNING and r['warning']['not_an_economic_connection'] for r in res['results']))
        self.assertEqual(res['connection_summary']['economic_connection_candidates'],0)
        nxt=O.next_questions(self.g,V)
        self.assertTrue(nxt['results']);self.assertTrue(all(r['connection_class']==self.K.WARNING for r in nxt['results']))

    def test_historical_memory_warnings_remain_retrievable(self):
        paths=build_all(self.dir/'v1',Clock())
        g=build([paths['S']],mode='synthetic',with_memory=True)
        res=O.revisit(g,'DLC-GSYN-S',V)
        hist=[r for r in res['results'] if r['match'].startswith('history:')]
        self.assertTrue(hist)
        self.assertTrue(all(r['connection_class']==self.K.WARNING for r in hist))  # R3 failure pattern: capacity tag only
        self.assertTrue(any(cite.endswith('.md') for r in hist for _,cite in r['warning']['lesson']))
        self.assertTrue(all(r['previous_status_stands'] for r in hist))

    def test_classes_are_categorical_and_outputs_deterministic_and_read_only(self):
        K=self.K
        self.assertEqual(K.classify(['AUTHOR_TAG_CANDIDATE']),K.WARNING);self.assertEqual(K.classify(['REUSED_CITATION']),K.UNSUPPORTED)
        self.assertEqual(K.classify(['AUTHOR_TAG_CANDIDATE','EXACT_DOCUMENT_HASH']),K.ECONOMIC)
        before=[sha(p) for p in self.paths]
        a=json.dumps(O.revisit(self.g,'DLC-QSYN-D/OBS-QD-1',V),sort_keys=True,default=str)
        g2=build(self.paths,catalogue_path=None,mode='synthetic',with_memory=False,requirements=self.Q.VOCABULARY)
        self.assertEqual(json.dumps(O.revisit(g2,'DLC-QSYN-D/OBS-QD-1',V),sort_keys=True,default=str),a)
        self.assertEqual(g2.digest(),self.g.digest());self.assertEqual([sha(p) for p in self.paths],before)
        self.assertEqual(self.Q.check()['quality'],'PASS')

    def test_exported_suggestions_carry_class_and_grounding_completeness(self):
        sug=[s for s in E.export_suggestions(self.g,'DLC-QSYN-D/OBS-QD-1',self.paths) if s['match'].startswith('claim:DLC-QSYN-R')][0]
        self.assertEqual(sug['connection_class'],self.K.ECONOMIC);self.assertTrue(sug['grounded_explanation_complete'])
        self.assertEqual(sug['suggestion_id'],O.suggestion_id(sug['operator'],sug['target'],sug['match'],sug['match_bases']))  # recomputable

    def test_same_gap_and_next_rows_have_recomputable_ids_and_basis_order_is_deterministic(self):
        for res,op in ((O.same_gap(self.g,'REQ_DOCUMENTED_ALLOCATION',V),'same-gap'),(O.next_questions(self.g,V),'next')):
            for r in res['results']:self.assertEqual(r['suggestion_id'],O.suggestion_id(op,r['target'],r['match'],r['match_bases']))
        self.assertEqual(O.order_bases(['SAME_LOCATOR_ONLY','REUSED_CITATION']),O.order_bases(['REUSED_CITATION','SAME_LOCATOR_ONLY']))
        self.assertEqual(O.suggestion_id('shared','a','b',['REUSED_CITATION','SAME_LOCATOR_ONLY']),O.suggestion_id('shared','a','b',['SAME_LOCATOR_ONLY','REUSED_CITATION']))

    def test_r3_historical_records_and_results_are_unchanged(self):
        base=ROOT/'docs/strategy/graph_pilot_r3'
        for packet in ('P3','P4'):
            for arm in P.ARMS:self.assertTrue(P.validate_connections(base/packet/f'connections-{arm}.jsonl',arm))  # V1 rows still valid
        rep=P.report([base/'P3',base/'P4'],export_name='blind_v2.json')
        self.assertEqual(rep['classification'],'INCONCLUSIVE')
        pooled=[n for n in rep['notes'] if n.startswith('pooled')][0]
        self.assertIn('G 3.151, S 4.162',pooled)


class GraphPilotV2ProvenanceTests(unittest.TestCase):
    """Prospective V2 workflow: a graph-originated row is accepted only against the frozen, replayable suggestion export."""
    arm=GraphPilotProtocolTests.arm;log=GraphPilotProtocolTests.log;write_log=GraphPilotProtocolTests.write_log

    def setUp(self):
        GraphPilotProtocolTests.setUp(self)
        frozen=json.loads(self.snap.read_text(encoding='utf-8'))['frozen_at_utc'];self.snap.unlink()  # refreeze the same packet for V2 logs
        P.make_snapshot(self.snap,'P1',self.d/'packet.jsonl',{'S':(self.d/'S.jsonl','DLC-GP1-S'),'G':(self.d/'G.jsonl','DLC-GP1-G')},self.bundle,
                        frozen_at=frozen,connection_log=P.CONNECTION_LOG_V2,implementation=R4.synthetic_pin())
        self.arm('S');_,self.t=self.arm('G')
        g,view=P.arm_graph(self.snap,'G',self.t)
        receipt=json.loads(json.dumps(view['receipt']))
        self.sugg={'banner':M.BANNER,'input':'DLC-GP1-G','visibility':receipt,
                   'suggestions':E.export_suggestions(g,'DLC-GP1-G',view['ledgers'],C.load(view['catalogue'])[0],None,view['cuts'])}
        self.gap=json.loads(json.dumps({**O.same_gap(g,'REQ_REALISED_ACTIVITY',V),'visibility':receipt},default=str))
        self.comp=json.loads(json.dumps({**O.complements(g,'DLC-GP1-G/OBS-1',V),'visibility':receipt},default=str))
        self.save('001-suggestions.json',self.sugg);self.save('002-same-gap.json',self.gap);self.save('003-complements.json',self.comp)
        self.clock.advance(1);self.now=self.clock.at()
        self.index,self.manifest=P.load_suggestion_exports(P.default_exports(self.snap),self.snap)
        self.econ=next(e for e in self.index.values() if e['match']=='relationship:DLC-GPKT-1/REL-P-1@1')
        self.warn=next(e for e in self.index.values() if e['operator']=='same-gap')

    def save(self,name,doc):
        d=self.d/P.SUGGESTION_EXPORT_DIR;d.mkdir(exist_ok=True)
        (d/name).write_text(json.dumps(doc,indent=1,default=str),encoding='utf-8');return d/name

    def row(self,e,**change):
        r=self.log('G',connection_id=e['suggestion_id'],operator=e['commands'][0],found_via='GRAPH_ONLY',
                   source_record=e['target'] if e['source_endpoints'] else 'DLC-GP1-G/OBS-1',
                   target_record=e['target_endpoints'][0],basis=list(e['match_bases']),recorded_at_utc=self.now,
                   kind='CONNECTION' if e['connection_class']==K_ECONOMIC else 'METHODOLOGICAL_WARNING')
        r.update(log_version=P.CONNECTION_LOG_V2,origin_suggestion_id=e['suggestion_id'],origin_operator=e['operator'],
                 origin_bases=list(e['match_bases']),connection_class=e['connection_class'])
        return {**r,**change}

    def reading(self,arm):
        return self.log(arm,recorded_at_utc=self.now,log_version=P.CONNECTION_LOG_V2,origin_suggestion_id=None,origin_operator=None,
                        origin_bases=[],connection_class=None)

    def check(self,rows,arm='G',index='frozen'):
        return P.validate_connections(self.write_log('log.jsonl',rows),arm,self.index if index=='frozen' else index,True)

    def test_exact_origins_are_accepted_and_every_mismatch_is_refused(self):
        self.assertEqual(self.econ['connection_class'],K_ECONOMIC);self.assertEqual(self.warn['connection_class'],'METHODOLOGICAL_WARNING')
        self.assertEqual(len(self.check([self.row(self.econ),self.row(self.warn),self.reading('G')])),3)
        other=next(e for e in self.index.values() if e['suggestion_id']!=self.econ['suggestion_id'] and e['operator']=='complements')
        bad=(({},None,'none was supplied'),
             ({'origin_suggestion_id':'SUG-'+'0'*12,'connection_id':'SUG-'+'0'*12},'frozen','not in the frozen suggestion export'),
             ({'origin_operator':'revisit'},'frozen','origin operator'),({'operator':'shared'},'frozen','origin operator'),
             ({'origin_bases':['EXACT_ENTITY_ID']},'frozen','bases or class'),
             ({'connection_class':'METHODOLOGICAL_WARNING','kind':'METHODOLOGICAL_WARNING'},'frozen','bases or class'),
             ({'target_record':'DLC-GPKT-1/OBS-P-1'},'frozen','endpoints'),({'source_record':'DLC-GPKT-1/OBS-P-1'},'frozen','endpoints'),
             ({'recorded_at_utc':DR.START.isoformat()},'frozen','recorded before'),
             ({'connection_id':other['suggestion_id']},'frozen','is its origin id'),({'operator':'explain'},'frozen','suggestion-producing'),
             ({'origin_suggestion_id':None},'frozen','SUG- origin'),({'log_version':'X'},'frozen','unknown log_version'))
        for change,index,why in bad:
            with self.assertRaisesRegex(P.PilotError,why,msg=str(change)):self.check([self.row(self.econ,**change)],index=None if index is None else 'frozen')
        with self.assertRaisesRegex(P.PilotError,'cannot be logged as an economic connection'):self.check([self.row(self.warn,kind='CONNECTION')])
        with self.assertRaisesRegex(P.PilotError,'V1 rows are refused'):
            self.check([self.log('G',connection_id=self.econ['suggestion_id'],operator='complements',found_via='GRAPH_ONLY')])
        with self.assertRaisesRegex(P.PilotError,'no graph suggestions'):self.check([self.row(self.econ,arm='S')],arm='S',index=None)
        with self.assertRaisesRegex(P.PilotError,'only graph-originated'):self.check([dict(self.reading('G'),origin_suggestion_id=self.econ['suggestion_id'])])
        args=['pilot','connections',str(self.write_log('cli.jsonl',[self.row(self.econ)])),'--arm','G']
        out=io.StringIO()
        with contextlib.redirect_stdout(out):GCLI.main(args+['--suggestions',*map(str,P.default_exports(self.snap)),'--packet-snapshot',str(self.snap)])
        self.assertEqual(json.loads(out.getvalue())['format'],'PASS')
        err=io.StringIO()
        with contextlib.redirect_stderr(err),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):GCLI.main(args)
        self.assertIn('frozen suggestion export',err.getvalue())

    def test_edited_fabricated_or_foreign_exports_are_refused(self):
        files=P.default_exports(self.snap);original=files[0].read_bytes()
        last=self.sugg['suggestions'][-1];fake={**last,'match':'observation:DLC-GPKT-1/OBS-P-9@1'}  # self-consistent: only replay can expose it
        fake['suggestion_id']=O.suggestion_id(fake['operator'],fake['target'],fake['match'],fake['match_bases'])
        edited=json.loads(original);w=next(s for s in edited['suggestions'] if s['connection_class']=='METHODOLOGICAL_WARNING')
        w['connection_class']=K_ECONOMIC  # a warning relabelled as an economic connection
        for doc,why in ((edited,'differs from its snapshot replay|class differs'),
                        ({**self.sugg,'suggestions':self.sugg['suggestions']+[fake]},'differs from its snapshot replay'),
                        ({**self.sugg,'visibility':dict(self.sugg['visibility'],arm='S')},'not a graph-arm output'),
                        ({**self.sugg,'visibility':dict(self.sugg['visibility'],snapshot_sha256='0'*64)},'not a graph-arm output')):
            files[0].write_text(json.dumps(doc),encoding='utf-8')
            with self.assertRaisesRegex(P.PilotError,why):P.load_suggestion_exports(files,self.snap)
        files[0].write_bytes(original)
        self.assertEqual(P.load_suggestion_exports(files,self.snap)[0],self.index)

    def test_replay_covers_the_full_saved_output_not_only_indexed_fields(self):
        by_name={f.name:f for f in P.default_exports(self.snap)}
        def edit(name,change):
            doc=json.loads(by_name[name].read_text(encoding='utf-8'));change(doc);return doc
        def grounding(doc):
            r=next(r for r in doc['results'] if r['connection_class']==K_ECONOMIC);r['grounding']['worth_investigating_because']='edited after the query'
        def lesson(doc):doc['results'][0]['warning']['lesson']=[]
        def not_established(doc):next(r for r in doc['results'] if 'grounding' in r)['grounding']['not_established'].pop()
        def rejection(doc):doc['rejected']=doc['rejected'][1:] if doc['rejected'] else [{'node':'x','code':'ONLY_SHARED_KEYWORD','reason':'invented'}]
        def note(doc):doc['notes'].append('extra note')
        def extra_field(doc):doc['results'][0]['reviewer_comment']='looks good'
        def receipt(doc):doc['visibility']['own_ledger']['head_hash_visible']='0'*64
        def baseline_flag(doc):doc['suggestions'][0]['baseline_structured_discoverable']=not doc['suggestions'][0]['baseline_structured_discoverable']
        cases=(('003-complements.json',grounding),('002-same-gap.json',lesson),('003-complements.json',not_established),('003-complements.json',rejection),
               ('002-same-gap.json',note),('002-same-gap.json',extra_field),('003-complements.json',receipt),('001-suggestions.json',baseline_flag))
        for name,change in cases:
            original=by_name[name].read_bytes();doc=edit(name,change)
            self.assertEqual(P.export_entries(doc),P.export_entries(json.loads(original)),change.__name__)  # id, bases and class untouched
            by_name[name].write_text(json.dumps(doc),encoding='utf-8')
            with self.assertRaisesRegex(P.PilotError,'differs from its snapshot replay',msg=change.__name__):P.load_suggestion_exports(list(by_name.values()),self.snap)
            by_name[name].write_bytes(original)
        g=Ledger(self.d/'G.jsonl');self.clock.advance(1)  # later appends change only the volatile ledger length, never the replayed output
        g.append('observation',DR.observation('OBS-9','Later record.',1,'count',DR.doc('arm/later',b'later')))
        self.assertEqual(P.load_suggestion_exports(list(by_name.values()),self.snap)[0],self.index)

    def test_blinding_seals_the_export_and_unblinding_rechecks_it(self):
        logs={'S':self.write_log('connections-S.jsonl',[self.reading('S')]),'G':self.write_log('connections-G.jsonl',[self.row(self.econ),self.row(self.warn)])}
        moved=self.d/'moved';(self.d/P.SUGGESTION_EXPORT_DIR).rename(moved)
        with self.assertRaisesRegex(P.PilotError,'none was supplied'):P.blind(self.snap,logs,'test-salt-0123456789',self.d/'b0.json',self.d/'k0.json')
        moved.rename(self.d/P.SUGGESTION_EXPORT_DIR)
        export=P.blind(self.snap,logs,'test-salt-0123456789',self.d/'blind.json',self.d/'key.json')
        key=json.loads((self.d/'key.json').read_text(encoding='utf-8'))
        self.assertEqual([m['sha256'] for m in key['suggestion_exports']],[m['sha256'] for m in self.manifest])
        text=json.dumps(export)
        for leak in ('SUG-',P.SUGGESTION_EXPORT_DIR,'same-gap','complements'):self.assertNotIn(leak,text)
        v2=P.alias_export(self.d/'blind.json',self.d/'blind_v2.json',self.dir/'alias.json')  # R4 presents only the aliased, leak-scanned export
        self.assertEqual(P.scan_leaks(v2['items'],P.own_records(export)),[])
        self.write_log('adjudications.jsonl',[{'blind_id':i['blind_id'],'outcome':'REJECTED_TRIVIAL','economic_meaning':'NOT_MEANINGFUL','checked_evidence':[],
                                               'adjudicator':'Owner','adjudicator_kind':'HUMAN','adjudicator_minutes':1,'recorded_at_utc':self.now,'notes':''}
                                              for i in v2['items']])
        rows=P.unblind(self.d,'blind_v2.json')
        self.assertEqual(sorted(r['origin_suggestion_id'] for r in rows if r['arm']=='G'),sorted([self.econ['suggestion_id'],self.warn['suggestion_id']]))
        self.assertEqual({r['connection_class'] for r in rows if r['arm']=='G'},{K_ECONOMIC,'METHODOLOGICAL_WARNING'})
        g_metrics=P.arm_metrics(Ledger(self.d/'G.jsonl').load(),'G',rows)
        self.assertEqual(g_metrics['graph_suggestions_false_or_trivial'],[1,1])  # economic candidates logged as connections
        self.assertEqual(g_metrics['graph_rows_false_or_trivial_by_class'],{K_ECONOMIC:[1,1],'METHODOLOGICAL_WARNING':[1,1]})
        self.assertEqual((g_metrics['methodological_warnings_logged'],g_metrics['review_burden_items']),(1,2))
        target=P.default_exports(self.snap)[0];target.write_bytes(target.read_bytes()+b' ')
        with self.assertRaisesRegex(P.PilotError,'changed after blinding'):P.unblind(self.d,'blind_v2.json')
        target.write_bytes(target.read_bytes()[:-1]);self.assertTrue(P.unblind(self.d,'blind_v2.json'))
        self.snap.rename(self.d/'moved.json')  # without the sealed snapshot the V2 rules cannot be assumed away
        with self.assertRaisesRegex(P.PilotError,'snapshot is missing'):P.unblind(self.d,'blind_v2.json')

    def test_v2_snapshot_pins_the_operator_version_and_old_snapshots_stay_v1(self):
        snap=json.loads(self.snap.read_text(encoding='utf-8'))
        self.assertEqual((snap['connection_log'],snap['graph_operator_version']),(P.CONNECTION_LOG_V2,'GRAPH_OPERATORS_V1_1'))
        (self.d/'old.json').write_text(json.dumps(dict(snap,graph_operator_version='GRAPH_OPERATORS_V1_0')),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'pins GRAPH_OPERATORS_V1_0'):P.arm_graph(self.d/'old.json','G',self.t)
        with self.assertRaisesRegex(P.PilotError,'connection_log'):P.make_snapshot(self.dir/'x.json','P9',self.d/'packet.jsonl',{},connection_log='V9')
        for packet in ('P3','P4'):self.assertNotIn('connection_log',json.loads((ROOT/f'docs/strategy/graph_pilot_r3/{packet}/snapshot.json').read_text(encoding='utf-8')))


class GraphPilotR4ReadinessTests(unittest.TestCase):
    """R4 readiness Phase A: implementation pinning, timestamp-derived effort, full suggestion accounting, adversarial checks."""

    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='graph-r4-test-'));self.addCleanup(R4.remove_tree,self.tmp)

    def test_pin_binds_commit_and_content_and_defines_dirty_unrelated_and_missing_git(self):
        impl=R4.pinned_copy(self.tmp/'impl');pin=I.pin(impl)
        self.assertEqual((I.verify(pin,impl)['status'],len(pin['commit']),pin['normalisation']),('EXACT_COMMIT',40,'CRLF_TO_LF'))
        self.assertIn('src/research/graph/pilot.py',pin['files']);self.assertIn('src/research/spec.py',pin['files'])
        for path in ('src/research/sec_pilot/parsing.py','docs/strategy/graph_pilot/fetch_one.py'):self.assertIn(path,pin['files'])  # acquisition and enforcement path
        self.assertIn('src/research/exp004_policy.py',pin['files'])  # imported only inside a spec.py function: the static closure still follows it
        self.assertEqual(set(pin['runtime']),{'python','implementation','dependencies'});self.assertIn('jsonschema',pin['runtime']['dependencies'])
        with self.assertRaisesRegex(I.PinError,'the runtime differs'):I.verify(dict(pin,runtime=dict(pin['runtime'],python='0.0.0')),impl)
        f=impl/'src/research/discovery/ledger.py';original=f.read_bytes()
        f.write_bytes(original+b'# local edit\n')
        with self.assertRaisesRegex(I.PinError,'uncommitted changes'):I.pin(impl)
        with self.assertRaisesRegex(I.PinError,"'changed': \\['src/research/discovery/ledger.py'\\]"):I.verify(pin,impl)
        f.write_bytes(original.replace(b'\n',b'\r\n'));self.assertEqual(I.verify(pin,impl)['status'],'EXACT_COMMIT')  # line endings normalised
        f.write_bytes(original);(impl/'README.md').write_text('unrelated\n',encoding='utf-8')
        R4.git(impl,'add','-A');R4.git(impl,'commit','-q','-m','unrelated')
        self.assertEqual(I.verify(pin,impl)['status'],'UNRELATED_COMMIT_CHANGE')
        (impl/'src/research/graph/new_module.py').write_text('X = 1\n',encoding='utf-8')
        with self.assertRaisesRegex(I.PinError,"'added'"):I.verify(pin,impl)
        (impl/'src/research/graph/new_module.py').unlink();bare=self.tmp/'bare'
        for rel in I.closure(impl)[0]:(bare/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(impl/rel,bare/rel)
        with self.assertRaisesRegex(I.PinError,'git metadata is unavailable'):I.pin(bare)
        self.assertEqual(I.verify(pin,bare)['status'],'GIT_UNAVAILABLE_CONTENT_VERIFIED')
        with self.assertRaisesRegex(I.PinError,'unknown implementation pin version'):I.verify(dict(pin,version='X'),impl)

    def test_v2_snapshots_require_and_enforce_the_pin_and_legacy_snapshots_are_unpinned(self):
        GraphPilotProtocolTests.setUp(self)
        frozen=json.loads(self.snap.read_text(encoding='utf-8'))['frozen_at_utc'];self.snap.unlink()
        arms={'S':(self.d/'S.jsonl','DLC-GP1-S'),'G':(self.d/'G.jsonl','DLC-GP1-G')}
        with patch.object(I,'git_state',return_value={'status':'DIRTY','commit':'a'*40,'dirty':['src/research/graph/pilot.py']}):
            with self.assertRaisesRegex(P.PilotError,'uncommitted changes'):P.make_snapshot(self.snap,'P1',self.d/'packet.jsonl',arms,frozen_at=frozen,connection_log=P.CONNECTION_LOG_V2)
        with patch.object(I,'git_state',return_value={'status':'GIT_UNAVAILABLE','commit':None,'dirty':None}):
            with self.assertRaisesRegex(P.PilotError,'git metadata is unavailable'):P.make_snapshot(self.snap,'P1',self.d/'packet.jsonl',arms,frozen_at=frozen,connection_log=P.CONNECTION_LOG_V2)
        P.make_snapshot(self.snap,'P1',self.d/'packet.jsonl',arms,frozen_at=frozen,connection_log=P.CONNECTION_LOG_V2,implementation=R4.synthetic_pin())
        _,t=GraphPilotProtocolTests.arm(self,'G')
        g,view=P.arm_graph(self.snap,'G',t)
        self.assertEqual(view['receipt']['graph_implementation']['commit'],R4.synthetic_pin()['commit'])
        snap=json.loads(self.snap.read_text(encoding='utf-8'))
        wrong=dict(snap,graph_implementation=dict(snap['graph_implementation'],tree_digest='0'*64));(self.d/'wrong.json').write_text(json.dumps(wrong),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'differs from the snapshot pin'):P.arm_graph(self.d/'wrong.json','G',t)
        (self.d/'none.json').write_text(json.dumps({k:v for k,v in snap.items() if k!='graph_implementation'}),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'must pin'):P.load_snapshot(self.d/'none.json')
        self.assertEqual(P.verify_summary(self.snap)['implementation']['status'],'UNRELATED_COMMIT_CHANGE')  # synthetic commit, same content
        for packet in ('P3','P4'):
            self.assertEqual(P.verify_summary(ROOT/f'docs/strategy/graph_pilot_r3/{packet}/snapshot.json')['implementation'],{'status':'NOT_PINNED_LEGACY'})

    def test_effort_material_threshold_is_the_greater_of_5_minutes_or_10_percent(self):
        self.assertFalse(P.compare_minutes(20,15)['material']);self.assertTrue(P.compare_minutes(21,15)['material'])  # 5-minute floor
        self.assertFalse(P.compare_minutes(132,120)['material']);self.assertTrue(P.compare_minutes(133,120)['material'])  # 10% of 120
        small=P.compare_minutes(16,15.5)
        self.assertEqual((small['material'],small['difference_minutes'],small['difference_percent']),(False,0.5,3.2))  # still reported
        self.assertEqual(P.compare_minutes(3,0)['difference_percent'],'UNDEFINED_ZERO_DENOMINATOR')
        self.assertEqual(P.ratio(0,0)['value'],'UNDEFINED_ZERO_DENOMINATOR');self.assertEqual(P.ratio('UNKNOWN',3)['value'],'UNKNOWN')

    def test_r3_effort_and_accounting_are_diagnostic_and_its_results_are_unchanged(self):
        base=ROOT/'docs/strategy/graph_pilot_r3';before={f:sha(f) for f in sorted(base.rglob('*')) if f.is_file()}
        rep=P.report([base/'P3',base/'P4'],export_name='blind_v2.json')
        self.assertEqual(rep['classification'],'INCONCLUSIVE');self.assertIn('G 3.151, S 4.162',[n for n in rep['notes'] if n.startswith('pooled')][0])
        accounts=[p['suggestion_accounting'] for p in rep['packets']]
        self.assertEqual({a['traceability'] for a in accounts},{'NOT_TRACEABLE_V1'})
        self.assertEqual(sum(a['untraced_graph_operator_rows'] for a in accounts),10)  # R3's ten untraced graph-operator connections
        self.assertTrue(all(a['totals']['exported']=='UNKNOWN' for a in accounts))
        for p in rep['packets']:
            for arm in P.ARMS:
                e=p['effort_check'][arm]
                self.assertGreaterEqual(e['excluded_human_decision_records']['disposition'],1)  # the owner's later dispositions are not arm effort
                self.assertLess(e['observed_span_minutes'],120);self.assertEqual(e['session']['status'],'NOT_RECORDED')
        self.assertEqual({f:sha(f) for f in sorted(base.rglob('*')) if f.is_file()},before)

    def test_r4_dry_run_record_is_current(self):
        self.assertEqual(R4.check()['r4_dry_run'],'PASS')

    def test_adversarial_evaluation_is_current_and_reports_the_trivial_identifier_weakness(self):
        from src.research.graph import adversarial as AD
        self.assertEqual(AD.check()['adversarial'],'PASS')
        rep=AD.run(self.tmp/'adv');v11,st=rep['totals']['graph_v1_1'],rep['totals']['structured_search']
        self.assertEqual((v11['true_positives'],v11['false_negatives'],v11['identity_or_timing_errors']),(4,0,0))
        self.assertEqual(v11['false_positives_by_challenge'],{'trivial shared identifier':2})  # reported as found, not tuned away
        self.assertEqual(st['false_positives'],4);self.assertEqual(v11['warnings_correct'],1)


class GraphPilotR4HardeningTests(unittest.TestCase):
    """Phase A hardening: effort-evidence gate, row/suggestion accounting levels, uniform pin, v1.2 rule mechanics."""

    def arm(self,**kw):
        base={'analyst_minutes_all':60,'verified_connections':2,'verified_connections_per_hour':2.0,'graph_only_verified':0,'false_or_premature_joins_made':2,
              'median_minutes_per_connection':6,'median_minutes_to_decisive_falsification':60,'duplicate_research_avoided':0,'original_frozen_m_passes':0,
              'original_frozen_m_passes_per_hour':0.0,'review_burden_items':6,'adjudicator_minutes':12,'graph_suggestions_false_or_trivial':[0,0]}
        return {**base,**kw}

    def packets(self,evidence,session=(60,60)):
        effort=lambda m:{'session':{'status':'RECORDED','minutes':m} if m else {'status':'NOT_RECORDED','minutes':'UNKNOWN'},'observed_span_minutes':50}
        g=self.arm(false_or_premature_joins_made=0,median_minutes_to_decisive_falsification=40,verified_connections=3,verified_connections_per_hour=3.0)
        return [{'S':self.arm(),'G':g,'effort_check':{'S':effort(session[0]),'G':effort(session[1])},'effort_evidence':{'S':evidence[0],'G':evidence[1]}}]*3

    def test_definitive_classifications_need_supporting_effort_evidence(self):
        final,primary,sens,notes=P.final_classification(self.packets(('CONSISTENT','CONSISTENT')))
        self.assertEqual((final,primary),('GRAPH_INCREMENT_OBSERVED','GRAPH_INCREMENT_OBSERVED'))
        final,primary,sens,_=P.final_classification(self.packets(('INCOMPLETE','CONSISTENT')))  # robust under the attested-session sensitivity
        self.assertEqual((final,sens['session']),('GRAPH_INCREMENT_OBSERVED','GRAPH_INCREMENT_OBSERVED'))
        final,primary,sens,notes=P.final_classification(self.packets(('CONTRADICTORY','CONSISTENT')))
        self.assertEqual((final,primary),('INCONCLUSIVE','GRAPH_INCREMENT_OBSERVED'));self.assertTrue(any('EFFORT_EVIDENCE_UNRESOLVED' in n for n in notes))
        final,_,sens,_=P.final_classification(self.packets(('INCOMPLETE','CONSISTENT'),session=(None,60)))
        self.assertTrue(sens['session'].startswith('NOT_VALID'));self.assertEqual(final,'INCONCLUSIVE')
        final,_,sens,_=P.final_classification(self.packets(('MATERIAL_DISCREPANCY','CONSISTENT'),session=(10,600)))  # sensitivity reverses the rate comparison: not definitive
        self.assertNotEqual(sens['session'],'GRAPH_INCREMENT_OBSERVED');self.assertEqual(final,'INCONCLUSIVE')
        self.assertTrue(any('Primary measure: self-reported analyst minutes' in n for n in notes))

    def test_accounting_rates_use_compatible_levels_and_rows_keep_their_outcomes(self):
        V2=GraphPilotV2ProvenanceTests;case=V2('test_exact_origins_are_accepted_and_every_mismatch_is_refused');V2.setUp(case);self.addCleanup(case.doCleanups)
        dup=case.row(case.econ,connection_id=P.connection_id('a','b',['second look']),basis=['second look'],arm_decision='DECLINED')
        case.write_log('connections-G.jsonl',[case.row(case.econ,arm_decision='ACCEPTED',discovery_lab_record='CAND-1'),dup,case.row(case.warn)])
        a=P.suggestion_accounting(case.d)['by_class'][K_ECONOMIC]
        self.assertEqual((a['logged_rows'],a['logged_suggestions'],a['rows_sharing_an_origin']),(2,1,2))
        self.assertEqual(a['rates']['declined_share_of_logged_rows'],{'numerator':1,'denominator':2,'value':0.5})
        self.assertEqual(a['rates']['all_declined_share_of_logged_suggestions'],{'numerator':0,'denominator':1,'value':0.0})
        rows=[{'arm':'G','connection_id':r['connection_id'],'origin_suggestion_id':r['origin_suggestion_id'],'connection_class':r['connection_class'],
               'kind':r['kind'],'arm_decision':r['arm_decision'],'outcome':o,'economic_meaning':'MEANINGFUL'}
              for r,o in zip(P.read_jsonl(case.d/'connections-G.jsonl'),('CONFIRMED_AGAINST_ORIGINALS','REJECTED_FALSE','REJECTED_TRIVIAL'))]
        b=P.suggestion_accounting(case.d,rows)
        e=b['by_class'][K_ECONOMIC]['adjudicated']
        self.assertEqual((e['rows_adjudicated'],e['rows']['CONFIRMED_AGAINST_ORIGINALS'],e['rows']['REJECTED_FALSE'],e['suggestions_with_conflicting_outcomes']),(2,1,1,1))
        self.assertEqual((b['confirmed_economic_discoveries']['rows'],b['confirmed_economic_discoveries']['distinct_origin_suggestions']),(1,1))

    def test_pin_is_enforced_on_structured_search_graph_and_replay_paths(self):
        V2=GraphPilotV2ProvenanceTests;case=V2('test_exact_origins_are_accepted_and_every_mismatch_is_refused');V2.setUp(case);self.addCleanup(case.doCleanups)
        real=I.content;changed=lambda root=I.ROOT:{**real(root),'tree_digest':'0'*64}
        s_when=Ledger(case.d/'S.jsonl').load().events[-1]['recorded_at_utc']
        with patch.object(I,'content',changed):
            for fn in (lambda:P.arm_view(case.snap,'S',s_when),lambda:P.arm_graph(case.snap,'G',case.t),lambda:P.load_suggestion_exports(P.default_exports(case.snap),case.snap),
                       lambda:P.derived_effort(case.d,'G'),lambda:P.suggestion_accounting(case.d),lambda:P.load_snapshot(case.snap)):
                with self.assertRaisesRegex(P.PilotError,'differs from the snapshot pin'):fn()
            err=io.StringIO()
            with contextlib.redirect_stderr(err),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                GCLI.main(['baseline-search','DLC-GP1-S','OBS-1','--snapshot',str(case.snap),'--arm','S','--query-at',s_when])
            self.assertIn('differs from the snapshot pin',err.getvalue())
        self.assertEqual(P.arm_view(case.snap,'G',case.t)['receipt']['implementation_check']['status'],'UNRELATED_COMMIT_CHANGE')

    def test_v1_2_rule_mechanics_and_v1_1_default_unchanged(self):
        from src.research.graph import connections as K
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);d=Path(tmp.name);clock=Clock()
        reg=entity('REGULATOR','SYN_AUTH:A-1','Synthetic authority')
        a=Ledger.create(d/'A.jsonl',campaign('DLC-MECH-A','a','OBSERVATION_FIRST','?'),clock);a.append('source',passport('SRC-A','s',field='f',units='u'))
        a.append('observation',obs('OBS-A','SRC-A','Authority count.',1,'count',reg,'2025-01-01','2025-01-01','2026-10-01T00:00:00+00:00','x'))
        b=Ledger.create(d/'B.jsonl',campaign('DLC-MECH-B','b','OBSERVATION_FIRST','?'),clock);b.append('source',passport('SRC-B','s',field='f',units='u'))
        b.append('observation',obs('OBS-B','SRC-B','Authority act.',1,'count',reg,'2025-02-01','2025-02-01','2026-10-01T00:00:00+00:00','y'))
        g=build([d/'A.jsonl',d/'B.jsonl'],catalogue_path=None,mode='synthetic',with_memory=False,requirements=__import__('src.research.graph.quality',fromlist=['VOCABULARY']).VOCABULARY)
        v11=O.complements(g,'DLC-MECH-B/OBS-B',V)['results'][0]
        self.assertEqual(v11['connection_class'],K.ECONOMIC);self.assertNotIn('classification_rules',v11)  # v1.1 default untouched
        K.use_rules(g,K.CLASSIFICATION_V1_2)
        v12=O.complements(g,'DLC-MECH-B/OBS-B',V)['results'][0]
        self.assertEqual((v12['connection_class'],v12['classification_rules']),(K.UNSUPPORTED,K.CLASSIFICATION_V1_2))
        self.assertEqual(v12['generic_identifier']['entities'],[{'entity':'entity:SYN_AUTH:A-1','category':'REGULATOR'}])
        self.assertEqual(v12['suggestion_id'],v11['suggestion_id'])  # ids are rule-independent
        with self.assertRaisesRegex(ValueError,'classification rules'):K.use_rules(g,'V9')
        reg_=K.load_register();self.assertEqual(reg_['identifiers'],[])



class GraphV12HoldoutTests(unittest.TestCase):
    """The v1.2 holdout, written after the rule was registered (commit 426c211); results pinned as found, not tuned."""

    def test_holdout_record_is_current_and_results_are_as_registered(self):
        import subprocess
        from src.research.graph import holdout_v1_2 as HO
        self.assertEqual(HO.check()['holdout'],'PASS')
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);rep=HO.run(Path(tmp.name))
        v11,v12=rep['totals']['graph_v1_1'],rep['totals']['graph_v1_2']
        self.assertEqual((v12['true_positives'],v12['false_negatives'],v11['false_negatives']),(5,0,0))
        self.assertEqual((v11['false_positives_by_case'],v12['false_positives_by_case']),(['H1','H2','H3','H7','H10'],['H7']))  # H7: declared expected miss
        self.assertEqual(v11['review_load'],v12['review_load'])  # labelling never hides items
        rule_commit=HO.RULE_COMMIT
        def git(*a):return subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True)
        if git('cat-file','-t',rule_commit).returncode!=0:
            if os.environ.get('GITHUB_ACTIONS'):self.fail('CI must check out full history (fetch-depth: 0) so the registration order is verified')
            self.skipTest('git history unavailable outside CI')
        self.assertEqual(git('merge-base','--is-ancestor',rule_commit,'HEAD').returncode,0)  # the rule commit precedes the holdout
        self.assertEqual(git('cat-file','-e',f'{rule_commit}:docs/strategy/graph_v1_2_rule_registration.md').returncode,0)
        self.assertEqual(git('cat-file','-e',f'{rule_commit}:docs/strategy/graph/generic_identifiers_v001.json').returncode,0)
        for absent in ('src/research/graph/holdout_v1_2.py','docs/strategy/graph_v1_2_holdout.md'):
            self.assertNotEqual(git('cat-file','-e',f'{rule_commit}:{absent}').returncode,0)  # the holdout did not exist when the rule was frozen
        self.assertEqual(git('diff','--quiet',rule_commit,'HEAD','--','docs/strategy/graph/generic_identifiers_v001.json').returncode,0)  # register unchanged since


class GraphPilotProvenanceAndConfigurationTests(unittest.TestCase):
    """Saved execution provenance is validated separately from replay; the registered R4 graph configuration is frozen."""

    def setUp(self):
        V2=GraphPilotV2ProvenanceTests;self.case=V2('test_exact_origins_are_accepted_and_every_mismatch_is_refused');V2.setUp(self.case)
        self.addCleanup(self.case.doCleanups)
        self.export=self.case.d/P.SUGGESTION_EXPORT_DIR/'001-suggestions.json';self.original=self.export.read_bytes()

    def tamper(self,change,whole_receipt=False):
        # Change only the saved execution-provenance record (or, for removal, the receipt holding it); every other field stays intact.
        doc=json.loads(self.original);change(doc['visibility'] if whole_receipt else doc['visibility']['implementation_check'])
        self.export.write_text(json.dumps(doc),encoding='utf-8')

    def load(self):return P.load_suggestion_exports(P.default_exports(self.case.snap),self.case.snap)

    def test_modified_execution_provenance_is_refused_before_sealing(self):
        saved=json.loads(self.original)['visibility']['implementation_check']
        self.assertEqual(saved['status'],'UNRELATED_COMMIT_CHANGE')  # synthetic pin commit differs from the running HEAD
        main=subprocess.run(['git','rev-parse','origin/main'],cwd=ROOT,capture_output=True,text=True).stdout.strip() or saved['running_commit']
        cases=((lambda c:c.update(running_commit='f'*40),'not in this repository'),
               (lambda c:c.update(running_commit=main) if main!=saved['running_commit'] else c.update(running_commit='e'*40),'differs from the pin at|not in this repository'),
               (lambda c:c.update(status='EXACT_COMMIT'),'inconsistent'),
               (lambda c:c.update(dirty_pinned_paths=sorted(set(c['dirty_pinned_paths'])|{'src/research/spec.py'}) if 'src/research/spec.py' not in c['dirty_pinned_paths'] else c['dirty_pinned_paths'].remove('src/research/spec.py')),'declares uncommitted pinned paths'),
               (lambda c:c.update(running_commit='HEAD'),'40-hex'),(lambda c:c.update(status='VERIFIED'),'is not one of'),
               (lambda c:c.update(extra='x'),'exactly the fields'),(lambda c:c.pop('dirty_pinned_paths'),'exactly the fields'),
               (lambda c:c.update(status='GIT_UNAVAILABLE_CONTENT_VERIFIED'),'names no running commit'))
        for change,why in cases:
            self.tamper(change)
            with self.assertRaisesRegex(P.PilotError,why):self.load()
        self.tamper(lambda v:v.pop('implementation_check'),whole_receipt=True)
        with self.assertRaisesRegex(P.PilotError,'record \\(implementation_check\\) is missing'):self.load()
        logs={'S':self.case.write_log('connections-S.jsonl',[self.case.reading('S')]),'G':self.case.write_log('connections-G.jsonl',[self.case.row(self.case.econ)])}
        self.tamper(lambda c:c.update(running_commit='f'*40))
        with self.assertRaisesRegex(P.PilotError,'not in this repository'):P.blind(self.case.snap,logs,'test-salt-0123456789',self.case.d/'b.json',self.case.d/'k.json')
        self.export.write_bytes(self.original)
        P.blind(self.case.snap,logs,'test-salt-0123456789',self.case.d/'blind.json',self.case.d/'key.json')
        sealed=json.loads((self.case.d/'key.json').read_text(encoding='utf-8'))['suggestion_exports'][0]['execution_provenance']
        self.assertEqual((sealed['level'],sealed['running_commit']),('COMMIT_CONSISTENT_WITH_PIN',saved['running_commit']))

    def test_legitimate_replay_at_an_unrelated_commit_is_accepted(self):
        moved=lambda root=I.ROOT,paths=None:{'status':'CLEAN','commit':'1'*40,'dirty':[]}  # HEAD has moved on; pinned content unchanged
        with patch.object(I,'git_state',moved):
            index,manifest=self.load()
            self.assertTrue(index)
            self.assertEqual(P.arm_view(self.case.snap,'G',self.case.t)['receipt']['implementation_check']['running_commit'],'1'*40)
        self.assertEqual(manifest[0]['execution_provenance']['level'],'COMMIT_CONSISTENT_WITH_PIN')

    def test_validator_scope_is_consistency_not_proof(self):
        snap=json.loads(self.case.snap.read_text(encoding='utf-8'));files=list(snap['graph_implementation']['files'])
        older=subprocess.run(['git','rev-list','--max-count=1','HEAD~1'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
        if not older:self.skipTest('no earlier commit available')
        at=I.files_at_commit(I.ROOT,older,files);differing=sorted(p for p in files if at.get(p)!=snap['graph_implementation']['files'][p])
        claim={'status':'UNRELATED_COMMIT_CHANGE','running_commit':older,'dirty_pinned_paths':differing}
        ok=P.validate_execution_provenance(claim,snap,self.case.t,'probe')  # consistent, so accepted: consistency is all it can show
        self.assertEqual(ok['level'],'COMMIT_CONSISTENT_WITH_PIN');self.assertIn('not a cryptographic',ok['does_not_establish'])
        with self.assertRaisesRegex(P.PilotError,'dated after the query'):
            P.validate_execution_provenance(claim,dict(snap,fixture='LIVE'),'2000-01-01T00:00:00+00:00','probe')
        from datetime import datetime,timedelta  # exact boundary: no clock-skew allowance is registered
        dated=datetime.fromisoformat(I.commit_time(I.ROOT,older))
        live=dict(snap,fixture='LIVE')
        self.assertEqual(P.validate_execution_provenance(claim,live,dated.isoformat(),'probe')['date_check'],'COMMIT_DATED_BEFORE_QUERY')  # equal: no later than
        for late in (timedelta(seconds=1),timedelta(minutes=4,seconds=59)):
            with self.assertRaisesRegex(P.PilotError,'dated after the query'):
                P.validate_execution_provenance(claim,live,(dated-late).isoformat(),'probe')  # commit one second (or under 5 minutes) after the query

    def test_hand_recorded_times_never_postdate_their_commits_and_corrections_are_preserved(self):
        from datetime import datetime
        def added(path):
            out=subprocess.run(['git','log','--diff-filter=A','--format=%H %cI','--',path],cwd=ROOT,capture_output=True,text=True).stdout.split()
            return out[-2:] if out else None
        corr=json.loads((ROOT/'docs/strategy/graph_timestamp_corrections_2026-10-22.json').read_text(encoding='utf-8'))
        for path in ('docs/strategy/graph_pilot_r4_graph_configuration_v002.json','docs/strategy/graph_timestamp_corrections_2026-10-22.json'):
            first=added(path)
            if first is None:
                if os.environ.get('GITHUB_ACTIONS'):self.fail(f'{path} must be committed')
                continue  # not yet committed in a local working tree
            recorded=datetime.fromisoformat(json.loads((ROOT/path).read_text(encoding='utf-8'))['recorded_at_utc'])
            self.assertLessEqual(recorded,datetime.fromisoformat(first[1]),path)  # never later than the commit that introduced it
        for c in corr['corrections']:  # the defective files are preserved byte-for-byte and their defect is real
            self.assertEqual(sha(ROOT/c['file']),c['sha256'])
            self.assertGreater(datetime.fromisoformat(c['recorded_at_utc_as_written']),datetime.fromisoformat(c['commit_committer_date_utc']))
        v1=json.loads((ROOT/'docs/strategy/graph_pilot_r4_graph_configuration_v001.json').read_text(encoding='utf-8'));v2=P.load_r4_configuration()
        same=('graph_operator_version','classification','generic_register','connection_log','implementation_pin_version','register_policy','dependency_boundary')
        self.assertEqual({k:v1[k] for k in same},{k:v2[k] for k in same})  # identical configuration; only time fields corrected
        self.assertEqual(v2['supersedes']['sha256'],sha(ROOT/'docs/strategy/graph_pilot_r4_graph_configuration_v001.json'))

    def test_registered_r4_configuration_is_frozen_and_is_the_v2_default(self):
        from src.research.graph import connections as K
        cfg=P.load_r4_configuration()
        self.assertEqual((cfg['graph_operator_version'],cfg['classification']),('GRAPH_OPERATORS_V1_1','GRAPH_CLASSIFICATION_V1_2'))
        self.assertEqual(cfg['generic_register']['sha256'],sha(ROOT/cfg['generic_register']['path']))
        snap=json.loads(self.case.snap.read_text(encoding='utf-8'))
        self.assertEqual((snap['classification']['rules'],snap['r4_configuration']['conforms']),(K.CLASSIFICATION_V1_2,True))
        bad=self.case.dir/'cfg.json';bad.write_text(json.dumps(dict(cfg,generic_register=dict(cfg['generic_register'],sha256='0'*64))),encoding='utf-8')
        with self.assertRaisesRegex(P.PilotError,'differs from the registered R4 configuration'):P.load_r4_configuration(bad)
        GraphPilotProtocolTests.setUp(self.case)  # a fresh packet frozen with an explicit deviation
        frozen=json.loads(self.case.snap.read_text(encoding='utf-8'))['frozen_at_utc'];self.case.snap.unlink()
        P.make_snapshot(self.case.snap,'P1',self.case.d/'packet.jsonl',{'S':(self.case.d/'S.jsonl','DLC-GP1-S'),'G':(self.case.d/'G.jsonl','DLC-GP1-G')},
                        frozen_at=frozen,connection_log=P.CONNECTION_LOG_V2,implementation=R4.synthetic_pin(),classification=K.CLASSIFICATION_V1_1)
        self.assertFalse(json.loads(self.case.snap.read_text(encoding='utf-8'))['r4_configuration']['conforms'])  # a deviation is recorded


class GraphPilotPhaseBTests(unittest.TestCase):
    """Phase B: dual human adjudication, exposure, warning usefulness and conformance (synthetic only)."""

    @classmethod
    def setUpClass(cls):
        from src.research.graph import pilot_r4_phase_b_dryrun as PB
        cls.PB=PB;cls.tmp=Path(tempfile.mkdtemp(prefix='graph-phase-b-test-'));cls.res=PB.run(cls.tmp);cls.p1=cls.tmp/'P1'

    @classmethod
    def tearDownClass(cls):R4.remove_tree(cls.tmp)

    def test_agreement_statistics_and_undefined_cases(self):
        from src.research.graph import adjudication as AD
        a={'1':'C','2':'P','3':'P','4':'C'};b={'1':'C','2':'P','3':'T','4':'C'}
        r=AD.agreement(a,b);self.assertEqual((r['items'],r['agreements'],r['kappa']),(4,3,0.6))
        self.assertEqual(r['disagreements'],[{'blind_id':'3','R1':'P','R2':'T'}])
        self.assertEqual(AD.agreement({},{})['kappa'],'UNDEFINED_ZERO_DENOMINATOR')
        self.assertEqual(AD.agreement({'1':'C','2':'C'},{'1':'C','2':'C'})['kappa'],'UNDEFINED_NO_VARIATION')

    def test_rehearsal_record_is_current_and_every_check_passes(self):
        self.assertTrue(all(r['result']=='PASS' for r in self.res['checks']))
        self.assertEqual(self.PB.check()['r4_phase_b_dry_run'],'PASS')

    def test_usefulness_never_becomes_an_economic_discovery(self):
        from src.research.graph import adjudication as AD
        dual=AD.dual(self.p1,'blind_v2.json');base=P.suggestion_accounting(self.p1,P.unblind(self.p1,'blind_v2.json',dual['adjudications']))
        forced={b:(dict(a,usefulness='USEFUL_LESSON_REUSED') if a['usefulness'] is not None else a) for b,a in dual['adjudications'].items()}
        after=P.suggestion_accounting(self.p1,P.unblind(self.p1,'blind_v2.json',forced))
        self.assertEqual(after['confirmed_economic_discoveries'],base['confirmed_economic_discoveries'])
        self.assertEqual(after['methodological_warnings_confirmed']['rows'],base['methodological_warnings_confirmed']['rows']+1)
        rows=P.unblind(self.p1,'blind_v2.json',forced)
        self.assertTrue(all(r['outcome']=='NOT_ECONOMICALLY_ADJUDICATED' for r in rows if r['kind']!='CONNECTION'))

    def test_deviation_never_admits_and_conformance_needs_everything(self):
        from src.research.graph import adjudication as AD
        snap=P.load_snapshot(self.p1/'snapshot.json')['snapshot'];dual=AD.dual(self.p1,'blind_v2.json')
        self.assertEqual(AD.conformance(self.p1,snap,dual)['status'],'CONFORMING')
        for change,problem in (({'r4_configuration':dict(snap['r4_configuration'],conforms=False)},'NON_CONFORMING_CONFIGURATION'),
                               ({'r4_configuration':None},'NON_CONFORMING_CONFIGURATION'),({'fixture':'LIVE'},None)):
            c=AD.conformance(self.p1,{**snap,**change},dual)
            if problem:self.assertIn(problem,c['problems'])
            else:self.assertEqual(c['status'],'CONFORMING')  # reveal order VERIFIED also satisfies a live packet
        for key,problem in (('CONFLICTED','ADJUDICATOR_CONFLICT'),('NOT_INDEPENDENT','ADJUDICATION_NOT_INDEPENDENT')):
            self.assertIn(problem,AD.conformance(self.p1,snap,{**dual,'item_status':{**dual['item_status'],key:1}})['problems'])
        self.assertIn('REVEAL_ORDER_UNVERIFIED',AD.conformance(self.p1,{**snap,'fixture':'LIVE'},{**dual,'reveal_order':{'status':'NOT_COMMITTED'}})['problems'])
        self.assertIn('ADJUDICATION_NOT_DUAL',AD.conformance(self.p1,snap,{'status':'ADJUDICATION_NOT_DUAL'})['problems'])
        with self.assertRaisesRegex(P.PilotError,'an assistant cannot adjudicate'):AD.seal(self.tmp/'P2','blind_v2.json','R1','ChatGPT reviewer','SYNTHETIC_FIXTURE')

    def test_legacy_reports_are_unchanged_by_phase_b(self):
        base=ROOT/'docs/strategy/graph_pilot_r3'
        rep=P.report([base/'P3',base/'P4'],export_name='blind_v2.json')
        self.assertEqual((rep['classification'],rep['excluded_from_primary']),('INCONCLUSIVE',[]))
        self.assertIn('G 3.151, S 4.162',[n for n in rep['notes'] if n.startswith('pooled')][0])
        self.assertTrue(all('conformance' not in p and 'warning_usefulness' not in p['G'] for p in rep['packets']))
        self.assertEqual(DR.check()['dry_run'],'PASS')


if __name__=='__main__':unittest.main()
