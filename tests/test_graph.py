import builtins,copy,hashlib,json,shutil,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from src.research.discovery import records as R
from src.research.discovery.demo import Clock,clk,entity,rec,syn,observation_first
from src.research.discovery.ledger import Ledger
from src.research.graph import catalogue as C,demo as D,evaluate as E,model as M,operators as O,render as RN
from src.research.graph.fixtures import AUTHORITY,ECHO,T7,build_all,campaign,obs
from src.research.graph.project import GraphError,build
from src.research.graph.rules import View,find_paths,verified_assertion

ROOT=Path(__file__).resolve().parents[1]
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
        allowed={str(p.resolve()) for p in self.abc}|{str(C.CATALOGUE_PATH.resolve())}|{str((ROOT/p).resolve()) for p in json.loads(C.CATALOGUE_PATH.read_text(encoding='utf-8'))['report_hashes']}
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

    def test_adjudication_log_requires_human_decisions(self):
        good={'suggestion_id':'SUG-0123456789ab','operator':'revisit','found_via':'GRAPH_ONLY','outcome':'CONFIRMED_AGAINST_ORIGINALS',
              'analyst_minutes':12,'arm_time_budget_minutes':60,'adjudicator':'Owner','recorded_at_utc':'2026-11-01T00:00:00+00:00',
              'discovery_lab_record':'DLC-X/CAND-1@1','notes':''}
        path=self.dir/'log.jsonl';path.write_text(json.dumps(good)+'\n',encoding='utf-8')
        self.assertEqual(E.validate_log(path),{'CONFIRMED_AGAINST_ORIGINALS':1})
        for change in ({'adjudicator':'Claude'},{'discovery_lab_record':None},{'found_via':'MAGIC'},{'analyst_minutes':-1}):
            path.write_text(json.dumps({**good,**change})+'\n',encoding='utf-8')
            with self.assertRaises(ValueError):E.validate_log(path)


if __name__=='__main__':unittest.main()
