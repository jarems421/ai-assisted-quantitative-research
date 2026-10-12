import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from src.research.phase3c.sources import SourceHTTP, put
from src.research.phase3c.quality import completeness, rounding, compatible, revenue_chain, identity_gate, terminal_gate, figi_gate, market_quality, stage_receipt
from src.research.phase3c.inference import paired_test, synthetic_windows, four_effect_family, hac_effective
from src.research.sec_pilot.acquisition import Archive
from src.research.sec_pilot.parsing import digest
from src.research.sec_pilot.planning import ambiguity_probe
from src.nexus.process_exp001 import session_dates


class SourceTests(unittest.TestCase):
    def test_interrupted_http_stream_preserves_every_received_byte(self):
        from http.client import IncompleteRead
        class Response:
            status=200; headers={}; calls=0
            def __enter__(self): return self
            def __exit__(self,*args): return None
            def read(self,limit):
                self.calls+=1
                if self.calls==1: return b'first'
                raise IncompleteRead(b'partial',20)
        response=Response()
        class Opener:
            def open(self,*args,**kwargs): return response
        with patch('src.research.phase3c.sources.build_opener',return_value=Opener()):
            with self.assertRaises(IncompleteRead) as caught:
                SourceHTTP._transport('https://example.invalid',{},None)
        self.assertEqual(caught.exception.partial_body,b'firstpartial')
    def test_source_registry_classification_and_missing_fields(self):
        from src.research.phase3c.registry import validate_registry
        row = {k: 'documented' for k in ('name', 'authority', 'purpose', 'review_date', 'authentication', 'free_tier',
               'documented_rate', 'enforced_rate', 'fields', 'pit_limitations', 'lifecycle_limitations', 'licensing', 'authoritative_for')}
        row.update(role='SECONDARY_CROSS_CHECK', documentation=['https://example.invalid/official'])
        validate_registry({'sources': [row]})
        with self.assertRaises(ValueError): validate_registry({'sources': [row, row]})
        row.pop('pit_limitations')
        with self.assertRaises(ValueError): validate_registry({'sources': [row]})
    def test_original_bytes_versions_cache_and_transport_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def fake(url, headers, payload):
                calls.append(url); return 200, {'Content-Length': '3'}, b'abc', url
            url = 'https://example.invalid/source'
            s = SourceHTTP({url}, root=tmp, transport=fake)
            a, raw = s.fetch('Documentation', url); b, raw2 = s.fetch('Documentation', url)
            self.assertEqual(a, b); self.assertEqual(raw, raw2); self.assertEqual(calls, [url])
            with self.assertRaises(ValueError): s.fetch('Documentation', url + '/escape')
            with self.assertRaises(ValueError): s.allow('http://example.invalid')
            store = Archive(Path(tmp) / 'another')
            x = store.body('0000000999-00-000001', b'old'); y = store.body('0000000999-00-000001', b'new')
            self.assertNotEqual(x['path'], y['path']); self.assertEqual(store.read(x), b'old')
            with self.assertRaises(ValueError): store.read(dict(x, path='../escape'))

    def test_persistent_restriction_redirect_and_error_receipts(self):
        url = 'https://example.invalid/source'
        for transport in (lambda *args: (403, {}, b'denied', url),
                          lambda *args: (200, {}, b'x', url + '/redirect')):
            with tempfile.TemporaryDirectory() as tmp:
                s = SourceHTTP({url}, root=tmp, transport=transport, sleep=lambda x: None)
                with self.assertRaises(ValueError): s.fetch('Documentation', url)
                self.assertTrue(list((Path(tmp) / 'attempts/Documentation').glob('*.json')))
                with self.assertRaises(ValueError): s.fetch('Documentation', url)

    def test_oversize_prefix_retained_and_stop_not_overwritten(self):
        def failed(*args):
            e = ValueError(); e.partial_body = b'partial'; e.reason_code = 'LOCAL_RESPONSE_BYTE_CEILING'; raise e
        with tempfile.TemporaryDirectory() as tmp:
            s = SourceHTTP({'https://example.invalid'}, root=tmp, transport=failed)
            with self.assertRaises(ValueError): s.fetch('Documentation', 'https://example.invalid')
            records = [json.loads(p.read_bytes()) for p in (Path(tmp) / 'attempts/Documentation').glob('*.json')]
            self.assertEqual(s.archive.read(records[0]['partial_body']), b'partial')
            stop = (Path(tmp) / 'Documentation_stop.json').read_bytes()
            s._stop('Documentation', {'reason': 'second_independent_stop'})
            self.assertEqual((Path(tmp) / 'Documentation_stop.json').read_bytes(), stop)

    def test_frozen_cohort_integrity_and_determinism(self):
        from src.research.phase3c.acquire import rows
        from src.research.phase3c.sources import require_cohort
        rows1 = sorted(rows(), key=lambda r: r['case_key']); rows2 = sorted(reversed(rows()), key=lambda r: r['case_key'])
        self.assertEqual(digest(rows1), digest(rows2)); self.assertEqual(len(rows1), 60)
        self.assertEqual(sum(r['revenue_candidate'] for r in rows1), 30)
        real = Path('docs/acceleration/phase3c_pilot_cohort.json')
        if real.exists():
            cohort = json.loads(real.read_bytes()); bad = copy.deepcopy(cohort); bad['cases'].pop()
            with self.assertRaises(ValueError): require_cohort(bad)
            bad = dict(cohort, frozen_before_price=False)
            with self.assertRaises(ValueError): require_cohort(bad)


class ChainTests(unittest.TestCase):
    def filings(self):
        values = ('100000000', '110000000', '120000000')
        records = []
        for i, year in enumerate((2018, 2019, 2020)):
            r = {'concept': 'RevenueFromContractWithCustomerExcludingAssessedTax', 'namespace': 'http://fasb.org/us-gaap/2019',
                 'dimensions': [], 'unit': 'USD', 'entity_cik': '999', 'locator': 'original', 'value': values[i],
                 'decimals': '-6', 'original_element_reconciled': True}
            records.append({'issuer_cik': '999', 'accession': f'EXP999-{year}', 'form': '10-K', 'version': 'ORIGINAL',
                            'source_sha256': 'a' * 64, 'revenue': r, 'period_start': f'{year}-01-01', 'period_end': f'{year}-12-31',
                            'comparative': dict(r, value=values[i-1], start=f'{year-1}-01-01', end=f'{year-1}-12-31') if i else None,
                            'accounting_basis_status': 'CERTIFIED', 'basis_evidence': 'synthetic-source-locator',
                            'entity_scope_status': 'CERTIFIED', 'scope_evidence': 'synthetic-source-locator'})
        return records

    def test_three_original_numeric_chain_no_growth_series(self):
        result = revenue_chain(self.filings()); self.assertEqual(result['status'], 'CERTIFIED_CHAIN')
        self.assertNotIn('acceleration', result)
        self.assertEqual(revenue_chain(self.filings()[:2])['status'], 'UNAVAILABLE_MISSING_ORIGINAL')

    def test_missing_comparative_and_precision_intervals(self):
        rows = self.filings(); rows[1]['comparative'] = None
        self.assertEqual(revenue_chain(rows)['status'], 'UNAVAILABLE_ROUNDING_COMPARABILITY')
        self.assertTrue(compatible({'value': '100', 'decimals': '-1'}, {'value': '104', 'decimals': '0'}))
        self.assertFalse(compatible({'value': '100', 'decimals': 'INF'}, {'value': '101', 'decimals': 'INF'}))
        with self.assertRaises(ValueError): rounding('10', None)

    def test_concept_context_basis_perimeter_and_version_fail(self):
        cases = [('concept', 'IssuerRevenue', 'CONCEPT'), ('unit', 'EUR', 'CONTEXT'),
                 ('dimensions', ['segment'], 'CONTEXT'), ('value', '0', 'CONTEXT'),
                 ('original_element_reconciled', False, 'CONTEXT')]
        for key, value, reason in cases:
            with self.subTest(key=key):
                rows = self.filings(); rows[1]['revenue'][key] = value
                self.assertEqual(revenue_chain(rows)['status'], 'UNAVAILABLE_' + reason)
        for key, reason in [('accounting_basis_status', 'ACCOUNTING_BASIS'), ('entity_scope_status', 'ENTITY_SCOPE')]:
            rows = self.filings(); rows[1][key] = 'UNRESOLVED'
            self.assertEqual(revenue_chain(rows)['status'], 'UNAVAILABLE_' + reason)
        rows = self.filings(); rows[1]['form'] = '10-K/A'
        self.assertEqual(revenue_chain(rows)['status'], 'UNAVAILABLE_RESTATEMENT_OR_VERSION')
        rows = self.filings(); rows[1]['version'] = 'MODERN_COMPANYFACTS_AGGREGATE'
        self.assertEqual(revenue_chain(rows)['status'], 'UNAVAILABLE_RESTATEMENT_OR_VERSION')


class PopulationTests(unittest.TestCase):
    def test_survivor_delisted_omission_failed_retrieval_and_denominator(self):
        population = [{'case_key': k} for k in ('active', 'ended', 'classB')]
        result = completeness(population, [{'case_key': 'active', 'state': 'KNOWN_ELIGIBLE', 'evidence_sha256': 'a'}])
        self.assertEqual(result['denominator'], 3); self.assertEqual(result['resolved_fraction'], 1/3)
        for state in ('KNOWN_FILING_MISSING', 'KNOWN_NO_REQUIRED_FILING'):
            with self.assertRaises(ValueError): completeness(population, [{'case_key': 'ended', 'state': state}])
        with self.assertRaises(ValueError): completeness(population, [{'case_key': 'replacement', 'state': 'PRICE_UNRESOLVED'}])
        for state in ('SOURCE_RETRIEVAL_FAILED', 'IDENTITY_UNRESOLVED', 'PRICE_UNRESOLVED', 'TERMINAL_EVENT_UNRESOLVED'):
            self.assertEqual(completeness(population, [{'case_key': 'active', 'state': state}])['resolved_count'], 0)

    def test_class_rename_ticker_reuse_exchange_transfer_and_overlap(self):
        from src.research.sec_pilot.certification import resolve_class
        row = {'issuer_cik': '999', 'class': 'A', 'start': '2019-01-01T00:00:00Z', 'end': '2020-01-01T00:00:00Z',
               'source_sha256': 'a', 'status': 'CERTIFIED', 'security_id': 'EXP999-A', 'ticker': 'OLD'}
        new = dict(row, ticker='NEW', start=row['end'], end='2021-01-01T00:00:00Z', exchange='OTHER')
        records = [row, new, dict(row, issuer_cik='998', security_id='EXP999-reused'), dict(row, **{'class': 'B', 'security_id': 'EXP999-B'})]
        self.assertEqual(resolve_class(records, '999', 'A', '2020-06-01T00:00:00Z')['ticker'], 'NEW')
        self.assertEqual(resolve_class(records, '999', 'B', '2019-06-01T00:00:00Z')['security_id'], 'EXP999-B')
        self.assertEqual(resolve_class([row, row], '999', 'A', '2019-06-01T00:00:00Z')['status'], 'UNAVAILABLE')

    def test_figi_ambiguity_and_dated_identity_not_current_metadata(self):
        self.assertEqual(figi_gate({'data': [{'shareClassFIGI': 'A'}, {'shareClassFIGI': 'B'}]}), 'AMBIGUOUS')
        self.assertEqual(figi_gate({'data': [{'shareClassFIGI': 'A'}, {'shareClassFIGI': 'A'}]}), 'IDENTIFIER_ONLY_NOT_HISTORICAL_INTERVAL')
        self.assertEqual(identity_gate({'class': 'A', 'ticker': 'OLD', 'exchange': 'X', 'stable_id': 'Q', 'identifier_level': 'share_class'}), 'PROVISIONAL')
        self.assertEqual(identity_gate({'contradictions': ['providers_disagree']}), 'AMBIGUOUS')

    def test_merger_delisting_cancellation_and_terminal_missing(self):
        self.assertEqual(terminal_gate(None), 'TERMINAL_EVENT_UNRESOLVED')
        for kind, fields in [('cash_merger', {'cash_per_share': 10, 'currency': 'USD'}),
                             ('stock_merger', {'exchange_ratio': .5, 'successor_security_id': 'NEW'}),
                             ('cancellation', {'explicit_zero_recovery_evidence': 'primary-order'})]:
            event = dict(fields, kind=kind, source_sha256='a', effective_at='2020-01-01', class_and_position_terms_certified=True)
            self.assertEqual(terminal_gate(event), 'TERMINAL_EVENT_CERTIFIED')
            event.pop(next(iter(fields)))
            self.assertEqual(terminal_gate(event), 'TERMINAL_EVENT_PARTIAL')


class PriceTests(unittest.TestCase):
    def rows(self):
        return [{'date': '2020-01-02', 'open': 100, 'high': 100, 'low': 100, 'close': 100, 'volume': 1000,
                 'adjClose': 25, 'splitFactor': 1, 'divCash': 0},
                {'date': '2020-01-03', 'open': 25, 'high': 25, 'low': 25, 'close': 25, 'volume': 4000,
                 'adjClose': 25, 'splitFactor': 4, 'divCash': 0}]

    def test_raw_schema_splits_dividends_and_missing_sessions(self):
        records = self.rows(); expected = ['2020-01-02', '2020-01-03']
        r = market_quality(records, expected); self.assertEqual(r['session_status'], 'PASS')
        self.assertEqual(r['split_reconciliation_candidates_passed'], 1)
        self.assertEqual(market_quality(records[:1], expected)['missing_sessions'], ['2020-01-03'])
        self.assertEqual(market_quality(records + records[:1], expected)['duplicate_sessions'], 1)
        records[1].update(close=24, open=24, high=24, low=24, splitFactor=1, divCash=1, adjClose=24)
        records[0].update(close=25, open=25, high=25, low=25, adjClose=24)
        self.assertEqual(market_quality(records, expected)['dividend_reconciliation_candidates_passed'], 1)
        records[0]['adjClose']=25/ (1+1/24)
        self.assertEqual(market_quality(records, expected)['cash_exdate_price_internal_consistency_passed'],1)
        records[0]['close'] = float('nan')
        self.assertEqual(market_quality(records, expected)['session_status'], 'UNRESOLVED')


class InferenceTests(unittest.TestCase):
    def test_synthetic_null_positive_negative_and_determinism(self):
        rng = np.random.default_rng(999); data = rng.normal(0, .01, 1512)
        null = paired_test(synthetic_windows(data), draws=200)
        positive = paired_test(synthetic_windows(data + .002), draws=200)
        negative = paired_test(synthetic_windows(data - .002), draws=200)
        self.assertLess(positive['one_sided_null_p'], null['one_sided_null_p'])
        self.assertGreater(negative['one_sided_null_p'], null['one_sided_null_p'])
        self.assertEqual(null, paired_test(synthetic_windows(data), draws=200))
        for block in (126, 504): self.assertEqual(paired_test(synthetic_windows(data), block=block, draws=200)['block'], block)

    def test_zero_variance_missing_nav_and_few_blocks_fail_closed(self):
        for values in (np.zeros(1512), np.ones(1512)):
            with self.assertRaises(ValueError): paired_test(synthetic_windows(values), draws=200)
        w = synthetic_windows(np.random.default_rng(999).normal(0, .01, 1512))
        w[0]['strategy'][0] = None
        with self.assertRaises(ValueError): paired_test(w, draws=200)
        w = synthetic_windows(np.random.default_rng(999).normal(0, .01, 1100))
        self.assertFalse(paired_test(w, draws=200)['sample_gate_pass'])
        w[1]['dates'][0] = w[0]['dates'][0]
        with self.assertRaises(ValueError): paired_test(w, draws=200)

    def test_dependence_effective_n_and_holm_failures(self):
        rng = np.random.default_rng(999); iid = rng.normal(0, .01, 1512); persistent = np.zeros(1512)
        for i in range(1, len(iid)): persistent[i] = .99 * persistent[i-1] + iid[i]
        self.assertLess(hac_effective([persistent[:756], persistent[756:]], 252)['effective_n'],
                        hac_effective([iid[:756], iid[756:]], 252)['effective_n'])
        family = four_effect_family({'base': {'sample_gate_pass': True, 'one_sided_null_p': .01},
                                     'double_cost': None, 'delay1': {'status': 'UNRESOLVED'}, 'delay5': None})
        self.assertEqual(family['base']['adjusted_p'], .04); self.assertEqual(family['delay1']['raw_p'], 1)
        with self.assertRaises(ValueError): four_effect_family({'base': None})


class StageTests(unittest.TestCase):
    def fixture(self):
        h = 'a' * 64
        record = {k: h for k in ('source_hash', 'policy_hash', 'identity_snapshot_hash', 'execution_engine_hash', 'result_hash')}
        record.update(stage='DEVELOPMENT', trial_key='EXP999_synthetic', control_relationship={'trial_key': 'EXP999_control',
                      'population_hash': h, 'calendar_hash': h}, scenario='base', status='COMPLETE', cost_scenario='base30bps')
        context = {'active_stage': 'DEVELOPMENT', 'allowed_source_hashes': [h], 'approved_policy_hash': h,
                   'identity_snapshot_hash': h, 'execution_engine_hash': h, 'population_hash': h, 'calendar_hash': h,
                   'source_end': '2020-12-31', 'window_end': '2020-12-31'}
        return record, context

    def test_sealed_stage_source_control_and_certificate_isolation(self):
        r, c = self.fixture(); self.assertIn('receipt_sha256', stage_receipt(r, context=c))
        for key, value in [('stage', 'VALIDATION'), ('source_hash', 'b'*64), ('policy_hash', 'b'*64),
                           ('execution_engine_hash', 'b'*64), ('identity_snapshot_hash', 'b'*64), ('scenario', 'new_feature')]:
            bad = dict(r, **{key: value})
            with self.assertRaises(ValueError): stage_receipt(bad, context=c)
        bad = dict(r, control_relationship={'trial_key': 'other', 'population_hash': 'b'*64, 'calendar_hash': 'a'*64})
        with self.assertRaises(ValueError): stage_receipt(bad, context=c)
        with self.assertRaises(ValueError): stage_receipt(dict(r, stage='TEST_AUTHORIZED'), context=dict(c, active_stage='TEST_AUTHORIZED'))
        with self.assertRaises(ValueError): stage_receipt(r, context=dict(c, source_end='2021-01-01'))

    def test_existing_pause_and_absent_experiment_no_state_writes(self):
        from src.research.capabilities import require_remote_enabled
        from src.research.sec_pilot.acquisition import ROOT
        with self.assertRaises(ValueError): require_remote_enabled(ROOT, 'EXP004')
        self.assertFalse((ROOT / 'experiments/EXP005').exists())
