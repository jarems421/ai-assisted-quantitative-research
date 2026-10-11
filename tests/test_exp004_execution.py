"""Production compiler safeguards, without publication or job submission."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.research import exp004_execute as execution


class BindingTests(unittest.TestCase):
    def manifest(self):
        names=('momentum180','momentum365','ordinal180','ordinal365','validity','session','schedule')
        return {'freeze_specification_sha256':'synthetic-freeze','runtime_population_preservation_certified':True,
                'streams':{n:{'custom_indicator_id':'synthetic-'+n} for n in names},'assets':['OLD','NEW']}

    def build(self,name='M180_K20',start='2017-01-03',end='2017-12-31'):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'published_manifest.json').write_text(json.dumps(self.manifest()))
            with patch.object(execution,'OUT',p),patch.object(execution,'verify_freeze',return_value={'frozen_specification_sha256':'synthetic-freeze'}):
                return execution.binding(name,start,end)

    def test_no_held_out_or_extra_cells(self):
        for args in [('M90_K20','2017-01-03','2017-12-31'),('EW','2021-01-04','2021-12-31'),('SPY','2024-01-02','2024-12-31')]:
            with self.assertRaises(ValueError):self.build(*args)

    def test_each_cell_uses_its_frozen_rank_and_shared_date_validity_schedule(self):
        for horizon in (180,365):
            for k in (20,40):
                p=self.build(f'M{horizon}_K{k}');encoded=json.dumps(p)
                for required in (f'synthetic-momentum{horizon}',f'synthetic-ordinal{horizon}',
                                 'synthetic-session','synthetic-validity','synthetic-schedule','9.5'):
                    self.assertIn(required,encoded)
                self.assertNotIn(f'synthetic-momentum{545-horizon}',encoded)
                self.assertNotIn('UNPUBLISHED',encoded)

    def test_equal_weight_has_no_topk_and_spy_exact_run_inception(self):
        ew=json.dumps(self.build('EW'));spy=json.dumps(self.build('SPY'))
        self.assertIn('synthetic-session',ew);self.assertNotIn('synthetic-ordinal',ew)
        self.assertIn('20170103',spy);self.assertNotIn('20150102',spy)

    def test_publication_freeze_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'published_manifest.json').write_text(json.dumps(self.manifest()))
            with patch.object(execution,'OUT',p),patch.object(execution,'verify_freeze',return_value={'frozen_specification_sha256':'other'}):
                with self.assertRaisesRegex(ValueError,'another freeze'):execution.binding('EW','2017-01-03','2017-12-31')

    def test_silent_native_universe_pruning_cannot_be_submitted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);m=self.manifest();m['runtime_population_preservation_certified']=False
            (p/'published_manifest.json').write_text(json.dumps(m))
            with patch.object(execution,'OUT',p),patch.object(execution,'verify_freeze',return_value={'frozen_specification_sha256':'synthetic-freeze'}):
                with self.assertRaisesRegex(ValueError,'native symbol pruning'):execution.binding('EW','2017-01-03','2017-12-31')
