import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from src.research.inference_feasibility import inference_design_gate
from src.research.phase3d.closure.inference import hac_se,evaluate
from src.research.phase3d.proof import compile_manifest,replay,file_hash
from src.research.phase3d.fixtures import proof_fixture
from src.research.spec import digest


class ClosureInferenceTests(unittest.TestCase):
    def test_resolution_blocks_old_sign_design_and_low_power(self):
        base={'method':'exact_sign','clusters':6,'alpha':.05,'family_size':4,'sample_units':72,'minimum_units':24,'power_lower':.8,'power_required':.5}
        result=inference_design_gate(base)
        self.assertFalse(result['INFERENCE_RESOLUTION_FEASIBLE']); self.assertEqual(result['minimum_p'],1/64)
        self.assertTrue(inference_design_gate(dict(base,method='bootstrap',draws=1999))['INFERENCE_RESOLUTION_FEASIBLE'])
        self.assertFalse(inference_design_gate(dict(base,method='asymptotic',power_lower=None))['POWER_GATE_FEASIBLE'])

    def test_hac_white_noise_variance_and_studentized_determinism(self):
        values=np.random.default_rng(999).normal(0,.002,(4,2,36))
        self.assertTrue(np.all(hac_se(values)>0))
        first=evaluate(values); self.assertEqual(first,evaluate(values))
        self.assertLess(evaluate(values+.005)['monthly_hac12']['p'][0],first['monthly_hac12']['p'][0])
        for invalid in (np.zeros((4,2,36)),np.full((4,2,36),np.nan),np.ones((4,1,36))):
            with self.assertRaises(ValueError):evaluate(invalid)

    def test_compiler_refuses_impossible_design_with_unchanged_certified_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec,a=proof_fixture(tmp); ref=spec['contracts']['inference']; path=Path(tmp,ref['path'])
            obj=json.loads(path.read_bytes()); obj['design_feasibility'].update(method='exact_sign',clusters=6)
            path.write_text(json.dumps(obj)); ref['sha256']=file_hash(path)
            with self.assertRaises(ValueError): compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)

    def test_git_difference_is_distinct_from_code_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec,a=proof_fixture(tmp); manifest,path=compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)
            manifest['code_commit']='0'*40; manifest['manifest_sha256']=digest({k:v for k,v in manifest.items() if k!='manifest_sha256'})
            path.write_text(json.dumps(manifest)); result=replay(path,tmp,authority=a)
            self.assertFalse(result['git_commit_exact']); self.assertTrue(result['relevant_code_hashes_exact'])
            manifest['code_hashes']['src/research/spec.py']='0'*64
            manifest['manifest_sha256']=digest({k:v for k,v in manifest.items() if k!='manifest_sha256'}); path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): replay(path,tmp,authority=a)
