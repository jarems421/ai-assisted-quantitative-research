"""Adversarial journal assurance with fictional recordings only."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.research.opportunity_scout import schema as S, v004_package as P
from src.research.opportunity_scout import v004_replay as J, v004_transport as T
from tests.opportunity_scout import v004_fixtures as F


class JournalAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.package = self.root/'package'
        P.build(self.package, F.blueprints(), F.runtime(), mode='SYNTHETIC')
        self.run = J.OfflineRun.create(self.root/'run', self.package)

    def pending(self):
        c = self.run.start(); request = P.load(self.package)[1][c['slot']]
        return c, T.Recording(F.encode(F.events(request,c['session_id']))), F.window(c['session_id'],c['slot'])

    def test_complete_consumption_suffix_removal_is_detected(self):
        self.run.start(); p = self.run.root/'journal.jsonl'
        p.write_bytes(p.read_bytes().splitlines()[0]+b'\n')
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()

    def test_complete_result_suffix_removal_is_detected(self):
        _, recording, window = self.pending(); self.run.finish(recording,window)
        p = self.run.root/'journal.jsonl'; p.write_bytes(b'\n'.join(p.read_bytes().splitlines()[:-1])+b'\n')
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).status()

    def test_original_handle_cannot_reselect_after_finish_interruption(self):
        _, recording, window = self.pending()
        with patch.object(J,'evaluate',side_effect=OSError('fictional pre-archival interruption')):
            with self.assertRaises(OSError): self.run.finish(recording,window)
        with self.assertRaises(S.ScoutError): self.run.finish(recording,window)
        with self.assertRaises(S.ScoutError): self.run.start()

    def test_raw_evidence_survives_evaluation_interruption(self):
        c, recording, window = self.pending()
        with patch.object(J,'evaluate',side_effect=OSError('fictional evaluation interruption')):
            with self.assertRaises(OSError): self.run.finish(recording,window)
        folder = self.run.root/'attempts'/c['slot']
        self.assertEqual((folder/'stdout.bin').read_bytes(),recording.stdout)
        self.assertEqual((folder/'stderr.bin').read_bytes(),recording.stderr)

    def test_invalid_recording_tag_does_not_leave_same_handle_retryable(self):
        _, recording, window = self.pending()
        with self.assertRaises(S.ScoutError): self.run.finish(T.Recording(recording.stdout,fictional=False),window)
        with self.assertRaises(S.ScoutError): self.run.finish(recording,window)

    def test_submission_witness_mutation_fails_closed(self):
        c, _, _ = self.pending()
        p = self.run.root/'witnesses'/'00000002.json'
        self.assertTrue(p.is_file())
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(S.ScoutError): self.run.status()

    def test_interruption_between_witness_and_append_cannot_reuse_slot(self):
        original = P.write_bytes
        def interrupted(path, data):
            original(path,data)
            if Path(path).name == '00000002.json': raise OSError('fictional post-witness crash')
        with patch.object(P,'write_bytes',side_effect=interrupted):
            with self.assertRaises(OSError): self.run.start()
        with self.assertRaises(S.ScoutError): J.OfflineRun(self.run.root).start()


if __name__ == '__main__': unittest.main()
