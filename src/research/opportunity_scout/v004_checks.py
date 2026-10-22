"""Full Scout offline regression entry point with private IO/process guards."""
import builtins
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from src.research.sec_pilot.parsing import offline
from .storage import ROOT


def run():
    original, builtin = Path.open, builtins.open
    blocked = [ROOT/'data', ROOT/'.research', ROOT/'experiments',
               Path.home()/'.claude', Path.home()/'.claude-research']
    def guard(path):
        resolved = Path(path).resolve()
        if (resolved in (ROOT/'.env', Path.home()/'.claude.json', Path.home()/'.claude-research.json')
                or any(resolved.is_relative_to(parent) for parent in blocked)):
            raise ValueError('Scout CI cannot access private artifacts or account contents')
    def path_open(path, *args, **kwargs): guard(path); return original(path, *args, **kwargs)
    def builtin_open(path, *args, **kwargs):
        if not isinstance(path, int): guard(path)
        return builtin(path, *args, **kwargs)
    with offline(), patch.object(Path, 'open', path_open), patch.object(builtins, 'open', builtin_open), \
         patch.object(subprocess, 'Popen', side_effect=AssertionError('Scout offline checks prohibit process launch')):
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests/opportunity_scout'), top_level_dir=str(ROOT))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__': run()
