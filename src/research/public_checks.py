"""Explicit public/synthetic tests with external network and private reads denied."""
import builtins
from pathlib import Path
import unittest
from unittest.mock import patch
from src.research.sec_pilot.parsing import offline

ROOT=Path(__file__).resolve().parents[2]
PUBLIC_TESTS=('test_phase3d_execution','test_phase3d_proof','test_phase3d_certification',
              'test_phase3d_inference','test_phase3d_approval','test_phase3d_closure_inference','test_phase3d_closure_sources',
              'test_phase3e_feasibility','test_phase3er_design','test_phase3er_inference','test_phase3_final','test_procurement_pilot','test_fda_pilot','test_merger_pilot','test_source_first','test_integrations_v2','test_item202_closure','test_item202_availability','test_item202_source','test_item202_date_bound','test_item202_population','test_item202_identity')


def run():
    original=Path.open; builtin=builtins.open
    blocked=[ROOT/'data',ROOT/'.research',ROOT/'experiments']
    def guard(path):
        resolved=Path(path).resolve()
        if resolved==ROOT/'.env' or any(resolved.is_relative_to(parent) for parent in blocked):
            raise ValueError('Public CI cannot access private data or historical experiment artifacts')
    def path_open(path,*args,**kwargs):guard(path);return original(path,*args,**kwargs)
    def builtin_open(path,*args,**kwargs):
        if not isinstance(path,int):guard(path)
        return builtin(path,*args,**kwargs)
    import sys
    sys.path.insert(0,str(ROOT/'tests'))
    with offline(),patch.object(Path,'open',path_open),patch.object(builtins,'open',builtin_open):
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in PUBLIC_TESTS)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)


if __name__=='__main__':run()
