import copy
import json
from pathlib import Path
import unittest
from src.research.phase3d.certification import canonical_revenue,revenue_triple,dated_identity
from src.research.spec import digest

CONTRACT=json.loads(Path('docs/acceleration/phase3d_revenue_contract.json').read_bytes())


def observation(year,value='100',concept='SalesRevenueNet',role='CURRENT',filing_year=None):
    fy=filing_year or year
    return {'issuer_cik':'999','accession':f'EXP999-{fy}','form':'10-K','original_version':'ORIGINAL',
            'concept':concept,'namespace':f'http://fasb.org/us-gaap/{fy}','context_ref':f'FY{year}','entity_cik':'999',
            'dimensions':[],'period_start':f'{year}-01-01','period_end':f'{year}-12-31','period_role':role,
            'filing_period_end':f'{fy}-12-31','unit':'USD','scale':'0','value':value,'decimals':'INF',
            'locator':f'element{year}','statement_locator':f'income-statement{year}', 'source_sha256':'a'*64,'primary_sha256':'b'*64,
            'original_element_reconciled':True,'primary_reconciled':True,'conflicting_duplicates':False}


def reviewed(row):
    r={k:row[k] for k in ('concept','namespace','locator','source_sha256','primary_sha256')}
    r.update(version='synthetic_review_v001',reviewer='SYNTHETIC_FIXTURE',reviewed_at='2026-10-12T00:00:00Z',
             reason='Synthetic accounting-equivalent statement line',decision='CERTIFIED',mapping_rule='Explicit net line fixture',
             accounting_basis='SYNTHETIC_COMMON_BASIS',perimeter='SYNTHETIC_CONSOLIDATED',evidence_locators=['note1','income-statement'],
             checks={k:True for k in CONTRACT['mandatory_review_checks']},observation_sha256=digest(row))
    return r


def certify(row):
    r=reviewed(row); return canonical_revenue(row,CONTRACT,[r],trusted_receipts={digest(r)})


class CertificationTests(unittest.TestCase):
    def test_reviewed_mapping_and_three_original_contract(self):
        rows=[certify(observation(y,concept=c)) for y,c in zip((2018,2019,2020),CONTRACT['candidate_concepts'])]
        comp=[certify(observation(y,role='COMPARATIVE',filing_year=y+1)) for y in (2018,2019)]
        r=revenue_triple(rows,comp); self.assertEqual(r['status'],'CERTIFIED_SOURCE_TRIPLE')
        self.assertFalse(r['acceleration_computed']); self.assertFalse(r['trading_eligible'])

    def test_no_fuzzy_extension_segment_or_instant(self):
        for change in ({'concept':'AmazingRevenue'},{'namespace':'http://issuer.example/revenue'}, {'dimensions':['segment']},
                       {'period_start':'2020-12-31'},{'value':'0'},{'unit':'EUR'}, {'primary_reconciled':False},
                       {'form':'10-K/A'},{'conflicting_duplicates':True},{'statement_locator':None}):
            row=observation(2020); row.update(change)
            self.assertEqual(certify(row)['status'],'UNAVAILABLE')

    def test_review_is_exact_source_value_and_trusted_receipt(self):
        row=observation(2020); r=reviewed(row)
        self.assertEqual(canonical_revenue(row,CONTRACT,[r],trusted_receipts=set())['status'],'UNAVAILABLE')
        row['value']='101'
        self.assertEqual(canonical_revenue(row,CONTRACT,[r],trusted_receipts={digest(r)})['status'],'UNAVAILABLE')
        r=reviewed(row); r['checks']['perimeter_compatible']=False
        self.assertEqual(canonical_revenue(row,CONTRACT,[r],trusted_receipts={digest(r)})['status'],'UNAVAILABLE')

    def test_perimeter_comparative_recast_and_duplicate_original(self):
        rows=[certify(observation(y)) for y in (2018,2019,2020)]
        comp=[certify(observation(y,role='COMPARATIVE',filing_year=y+1)) for y in (2018,2019)]
        bad=copy.deepcopy(rows); bad[1]['perimeter']='ACQUIRED_PERIMETER'
        self.assertEqual(revenue_triple(bad,comp)['reason'],'CERTIFIED_OBSERVATION_CHANGED')
        bad=copy.deepcopy(comp); bad[0]['original']['value']='150'
        self.assertEqual(revenue_triple(rows,bad)['status'],'UNAVAILABLE')
        self.assertEqual(revenue_triple([rows[0]]*3,comp)['status'],'UNAVAILABLE')

    def test_dated_identity_endpoints_overlap_and_ticker_reuse(self):
        row={'issuer_cik':'999','security_id':'EXP999-A','class':'A','exchange':'X','ticker':'OLD',
             'identifier_level':'share_class','effective_from':'2020-01-01T00:00:00Z','effective_to':'2020-02-01T00:00:00Z',
             'start_evidence_sha256':'a'*64,'end_evidence_sha256':'b'*64}
        trust={'a'*64,'b'*64}; at='2020-01-15T00:00:00Z'
        self.assertEqual(dated_identity([row],at=at,trusted_evidence=trust)['rows'],[row])
        self.assertEqual(dated_identity([row],at=row['effective_to'],trusted_evidence=trust)['rows'],[])
        for rows,evidence in [([row],set()),([row,row],trust),([dict(row,end_evidence_sha256=None)],trust)]:
            with self.assertRaises(ValueError): dated_identity(rows,at=at,trusted_evidence=evidence)
