"""Public original-element fixtures in the unchanged isolated parser environment."""
import json
from pathlib import Path
import subprocess
import unittest


class IsolatedOriginalTests(unittest.TestCase):
    def test_original_namespace_scale_unit_and_aggregate_rejection_offline(self):
        root = Path(__file__).resolve().parents[1]
        python = root / '.research/sec-pilot-venv/Scripts/python.exe'
        code = '''import copy,json,sys
from src.research.sec_pilot.parsing import offline
with offline():
 from src.research.phase3c.parsing import parse_original
 f={"accessionNumber":"0000000999-20-000001","reportDate":"2019-12-31","filingDate":"2020-02-01","issuer_cik":"0000000999","sources":{"instance":{"url":"https://example.invalid/instance.xml","body":{"sha256":"a"*64}}}}
 ns="http://fasb.org/us-gaap/2019-01-31"; concept="RevenueFromContractWithCustomerExcludingAssessedTax"
 xml=f'<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:g="{ns}" xmlns:iso="http://www.xbrl.org/2003/iso4217"><context id="annual"><entity><identifier scheme="http://www.sec.gov/CIK">0000000999</identifier></entity><period><startDate>2019-01-01</startDate><endDate>2019-12-31</endDate></period></context><unit id="usd"><measure>iso:USD</measure></unit><g:{concept} contextRef="annual" unitRef="usd" decimals="0">100</g:{concept}></xbrl>'
 primary=f'<html xmlns:g="{ns}"><body><ix:nonFraction name="g:{concept}" contextRef="annual" unitRef="usd" scale="0">100</ix:nonFraction></body></html>'
 bodies={"header":b"<ACCEPTANCE-DATETIME>20200131180000\\nCONFORMED SUBMISSION TYPE: 10-K\\nCONFORMED PERIOD OF REPORT: 20191231\\nCENTRAL INDEX KEY: 0000000999", "index":b'<table><tr><td>1</td><td>original</td><td><a href="instance.xml">instance.xml</a></td><td>EX-101.INS</td></tr></table>',"instance":xml.encode(),"primary":primary.encode()}
 normal=parse_original(f,bodies); assert normal["revenue"]["original_element_reconciled"]
 assert normal["revenue"]["value"]=="100" and normal["accounting_basis_status"]=="UNRESOLVED"
 changed=dict(bodies,instance=xml.replace(concept,"IssuerRevenue").encode()); assert parse_original(f,changed)["revenue"] is None
 changed=dict(bodies,primary=b"<html>non-inline source</html>"); n=parse_original(f,changed); assert n["revenue"]["instance_role"]=="ORIGINAL_ISSUER_EX101_INSTANCE" and n["revenue"]["primary_statement_reconciliation"]=="NOT_CERTIFIED_NON_INLINE"
 changed=dict(bodies,header=bodies["header"].replace(b"10-K",b"10-K/A")); assert parse_original(f,changed)["status"]=="UNAVAILABLE_RESTATEMENT_OR_VERSION"
 changed=dict(bodies,instance=xml.replace("iso:USD","iso:EUR").encode()); assert parse_original(f,changed)["revenue"] is None
 print(json.dumps({"passed":5,"external_network":False}))
'''
        result = subprocess.run([str(python), '-c', code], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['passed'], 5)
