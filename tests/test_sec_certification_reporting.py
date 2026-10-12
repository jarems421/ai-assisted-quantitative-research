import json
from pathlib import Path
import unittest
from src.research.sec_pilot.phase3a_report import render


class CertificationReportingTests(unittest.TestCase):
    def test_reports_ignore_json_object_insertion_order(self):
        root = Path(__file__).resolve().parents[1]
        evidence = json.loads((root/'docs/acceleration/phase3a_evidence.json').read_bytes())
        def reorder(value):
            if isinstance(value, dict): return {k: reorder(value[k]) for k in reversed(list(value))}
            if isinstance(value, list): return [reorder(v) for v in value]
            return value
        self.assertEqual(render(evidence), render(reorder(evidence)))
