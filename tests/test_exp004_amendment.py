"""Pre-performance amendment, temporary exclusion and ordinary split controls."""
import copy
import unittest
from datetime import date

from src.research.exp004_actions import classify_groups, crossing
from src.research.amend_exp004 import allowed_amendment, RULE
from src.research.spec import ROOT
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from src.research import amend_exp004
from src.research.store import Store


class AmendmentTests(unittest.TestCase):
    def rows(self):
        return [{'ticker':'OLD','executionDate':'2016-06-17','splitFrom':1,'splitTo':2},
                {'ticker':'NEW','executionDate':'2016-06-17','splitFrom':1,'splitTo':.01}]

    def test_aliases_group_by_stable_identity_not_ticker(self):
        groups=classify_groups(self.rows(),lambda ticker,day:'stable')
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['distinct_factors'],[.01,2])
        self.assertIsNone(groups[0]['factor'])
        self.assertEqual(groups[0]['tickers_at_event'],['NEW','OLD'])

    def test_window_stays_unavailable_until_maximum_horizon_ages_out(self):
        groups=classify_groups(self.rows(),lambda ticker,day:'stable')
        self.assertEqual(len(crossing(groups,'2017-06-17')),1)
        self.assertEqual(crossing(groups,'2017-06-18'),[])
        self.assertEqual(crossing(groups,'2016-06-16'),[])
        # There is deliberately no horizon argument: M180 cannot reenter first.
        self.assertEqual(len(crossing(groups,'2017-03-01')),1)

    def test_ordinary_and_same_factor_duplicate_are_unique_without_revision_history(self):
        rows=self.rows()[:1];rows.append(dict(rows[0],splitFrom=2,splitTo=4))
        before=copy.deepcopy(rows)
        g=classify_groups(rows,lambda ticker,day:'stable')[0]
        self.assertIsNone(g['ambiguity_reason']);self.assertEqual(g['factor'],2)
        self.assertEqual(g['source_row_count'],2);self.assertEqual(rows,before)

    def test_invalid_and_explicit_revision_ambiguity_are_fail_closed(self):
        for change in ({'splitFrom':0},{'splitTo':-1},{'revisionUnresolved':True}):
            r=dict(self.rows()[0],**change)
            self.assertIsNotNone(classify_groups([r],lambda t,d:'stable')[0]['ambiguity_reason'])

    def test_noneligible_ambiguous_groups_remain_in_ledger(self):
        g=classify_groups(self.rows(),lambda ticker,day:None)
        self.assertEqual(len(g),2)  # No unproven alias identity joins.
        r=self.rows();r[1]['ticker']='OLD'
        g=classify_groups(r,lambda ticker,day:None)[0]
        self.assertIsNotNone(g['ambiguity_reason']);self.assertIsNone(g['security_id'])
        self.assertEqual(g['excluded_security_decisions'],0)

    def test_only_single_rule_may_change(self):
        old=json.loads((ROOT/'experiments/EXP004/freeze_versions/v001/experiments/EXP004/spec.json').read_bytes())
        new=copy.deepcopy(old);new['dynamic_universe']['definition']+=RULE
        allowed_amendment(old,new)
        for key,value in [('hypothesis','different'),('research_cutoff','2021-01-01')]:
            bad=copy.deepcopy(new);bad[key]=value
            with self.assertRaisesRegex(ValueError,'more than'):allowed_amendment(old,bad)

    def prepare_temporary_freeze(self,root):
        p=root/'experiments/EXP004';archive=p/'freeze_versions/v001/experiments/EXP004'
        archive.mkdir(parents=True)
        old=(ROOT/'experiments/EXP004/freeze_versions/v001/experiments/EXP004/spec.json').read_bytes()
        (archive/'spec.json').write_bytes(old);(p/'spec.json').write_bytes(old)
        (p/'freeze_receipt.json').write_bytes((ROOT/'experiments/EXP004/freeze_receipt.json').read_bytes())
        raw=root/'raw'
        for y in range(2015,2021):
            d=raw/f'compiled_{y}_v002';d.mkdir(parents=True)
            (d/'qa_summary.json').write_text(json.dumps({'year':y,'status':'PASS_LOCAL_NUMERIC'}))
        store=Store(root);spec=json.loads(old);store.register(spec);store.transition(spec,'HYPOTHESIS_FROZEN')
        return store,spec,raw

    def test_amendment_after_development_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store,spec,raw=self.prepare_temporary_freeze(root)
            store.transition(spec,'DEVELOPMENT');store.close()
            with patch.object(amend_exp004,'ROOT',root),patch.object(amend_exp004,'RAW',raw):
                with self.assertRaisesRegex(ValueError,'precede Development'):amend_exp004.freeze_amendment()
            self.assertFalse((root/'experiments/EXP004/freeze_versions/v002/receipt.json').exists())

    def test_amendment_with_existing_job_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store,spec,raw=self.prepare_temporary_freeze(root)
            with store.db:
                store.db.execute("INSERT INTO jobs(key,experiment,kind,stage,request,status) VALUES ('existing','EXP004','backtest','DEVELOPMENT','{}','SUBMITTED')")
            store.close()
            with patch.object(amend_exp004,'ROOT',root),patch.object(amend_exp004,'RAW',raw):
                with self.assertRaisesRegex(ValueError,'Zero jobs'):amend_exp004.freeze_amendment()
            self.assertFalse((root/'experiments/EXP004/freeze_versions/v002/receipt.json').exists())
