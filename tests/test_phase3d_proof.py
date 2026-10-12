import copy
import json
from pathlib import Path
import tempfile
import unittest
from src.research.phase3d.proof import compile_manifest,replay,file_hash,ROLES
from src.research.phase3d.fixtures import proof_fixture
from src.research.spec import digest


class ProofTests(unittest.TestCase):
    def test_deterministic_immutable_manifest_and_exact_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec,authority=proof_fixture(tmp)
            one,path=compile_manifest(spec,tmp,Path(tmp)/'out',authority=authority)
            two,_=compile_manifest(spec,tmp,Path(tmp)/'out',authority=authority)
            self.assertEqual(one,two); self.assertFalse(one['performance_executed'])
            self.assertEqual(replay(path,tmp,authority=authority)['status'],'PASS_EXACT_INPUT_REPLAY')
            path.write_text('corrupt')
            with self.assertRaises(ValueError): compile_manifest(spec,tmp,Path(tmp)/'out',authority=authority)

    def test_every_referenced_role_mutation_fails(self):
        for role in (*ROLES,'snapshot'):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as tmp:
                spec,a=proof_fixture(tmp)
                _,path=compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)
                ref=spec['contracts'][role] if role!='snapshot' else spec['source_snapshots'][0]
                Path(tmp,ref['path']).write_bytes(b'changed')
                with self.assertRaises(ValueError): replay(path,tmp,authority=a)

    def test_unapproved_policy_and_inference_even_with_updated_hash(self):
        for role,status in [('availability','PROPOSED'),('inference','BLOCKED')]:
            with self.subTest(role=role),tempfile.TemporaryDirectory() as tmp:
                spec,a=proof_fixture(tmp); ref=spec['contracts'][role]; p=Path(tmp,ref['path'])
                obj=json.loads(p.read_bytes()); obj['status']=status; p.write_text(json.dumps(obj))
                ref['sha256']=file_hash(p)
                with self.assertRaises(ValueError): compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)

    def test_missing_contract_gate_terminal_and_future_source(self):
        mutations=[lambda s:s['contracts'].pop('identity'),lambda s:s['gates'].pop('terminal'),
                   lambda s:s['gates']['inference'].update(status='BLOCKED'),
                   lambda s:s['source_snapshots'][0].update(source_end='2021-01-01'),
                   lambda s:s.update(research_stage='VALIDATION'),lambda s:s.update(experiment_id='EXP005'),
                   lambda s:s['source_snapshots'][0].update(path='../escape')]
        for change in mutations:
            with tempfile.TemporaryDirectory() as tmp:
                spec,a=proof_fixture(tmp); change(spec)
                with self.assertRaises((ValueError,KeyError)): compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)
        with tempfile.TemporaryDirectory() as tmp:
            spec,a=proof_fixture(tmp); ref=spec['contracts']['execution']; p=Path(tmp,ref['path'])
            p.write_text(json.dumps({'unresolved_terminal_events':['EXP999-A']})); ref['sha256']=file_hash(p)
            with self.assertRaises(ValueError): compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)

    def test_authority_manifest_and_environment_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec,a=proof_fixture(tmp); manifest,path=compile_manifest(spec,tmp,Path(tmp)/'out',authority=a)
            changed=copy.deepcopy(a); changed['stage']='TEST_AUTHORIZED'
            with self.assertRaises(ValueError): replay(path,tmp,authority=changed)
            manifest['environment']['python']='changed'
            manifest['manifest_sha256']=digest({k:v for k,v in manifest.items() if k!='manifest_sha256'})
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): replay(path,tmp,authority=a)
            result=replay(path,tmp,authority=a,strict_environment=False)
            self.assertFalse(result['environment_exact'])
