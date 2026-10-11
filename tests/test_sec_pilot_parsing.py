import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT/'.research/sec-pilot-venv/Scripts/python.exe'


class OfflineParserTests(unittest.TestCase):
    def run_isolated(self, body):
        if not PYTHON.exists(): self.skipTest('Pinned isolated SEC interpreter unavailable; not a parser pass')
        code = "import sys;sys.path.insert(0,'tests')\nfrom sec_pilot_fixture import *\nfrom src.research.sec_pilot.parsing import parse,canonical\nsources={'submission':SUBMISSION,'instance':INSTANCE,'primary':b'<html>EXP999</html>'}\n"+body
        result = subprocess.run([str(PYTHON), '-c', code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_determinism_clocks_contexts_and_zero(self):
        self.run_isolated("a=parse(FIXTURE,sources,code_git_sha='synthetic')\nb=parse(FIXTURE,sources,code_git_sha='synthetic')\nassert canonical(a)==canonical(b)\nassert len(a['facts'])==2\nassert a['accepted_at_utc'] is None and a['public_available_at_utc'] is None\nassert a['facts'][0]['numeric_value']=='0'\nassert a['facts'][0]['context']['period']['type']=='duration'\nassert a['facts'][1]['context']['period']['type']=='instant'\nassert a['security_bindings']==[]")

    def test_conflicting_facts_retained(self):
        self.run_isolated("sources['instance']=INSTANCE.replace(b'</xbrl>',b'<s:Revenue contextRef=\"flow\" unitRef=\"USD\" decimals=\"0\">5</s:Revenue></xbrl>')\na=parse(FIXTURE,sources,code_git_sha='synthetic')\nassert len(a['facts'])==3\nassert sum(f['status']=='AMBIGUOUS' for f in a['facts'])==2")

    def test_fiscal_period_nil_and_missing_are_not_calendar_or_zero(self):
        self.run_isolated("sources['instance']=INSTANCE.replace(b'2019-01-01',b'2018-10-01').replace(b'2019-12-31',b'2019-09-28')\nsources['instance']=sources['instance'].replace(b'</xbrl>',b'<s:Missing contextRef=\"flow\" unitRef=\"USD\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:nil=\"true\"/></xbrl>')\na=parse(FIXTURE,sources,code_git_sha='synthetic')\nassert a['facts'][0]['context']['period']['endDate']=='2019-09-28'\nassert a['facts'][-1]['status']=='UNAVAILABLE' and a['facts'][-1]['numeric_value'] is None\nassert all(f['concept']!='AbsentTag' for f in a['facts'])")

    def test_malformed_future_and_external_entity_rejected(self):
        self.run_isolated("for value in (INSTANCE[:-8],b'<!DOCTYPE x [<!ENTITY y SYSTEM \"https://example.invalid/x\">]>'+INSTANCE):\n sources['instance']=value\n try:parse(FIXTURE,sources,code_git_sha='synthetic')\n except Exception:pass\n else:raise AssertionError('Malformed source accepted')\nsources['instance']=INSTANCE\nsources['submission']=SUBMISSION.replace(b'20200309183000',b'20210309183000')\ntry:parse(FIXTURE,sources,code_git_sha='synthetic')\nexcept ValueError:pass\nelse:raise AssertionError('Future source accepted')")
