"""Native OpenSSH verification with disposable SYNTHETIC keys; no account keys or network."""
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.research.spec import canonical
from src.research.study_readiness_v1 import approval as A, gate as G
from test_study_readiness import make_packet


class NativeSignatureTests(unittest.TestCase):
    def test_disposable_signature_accepts_exact_review_and_refuses_forgery(self):
        executable = shutil.which('ssh-keygen')
        self.assertIsNotNone(executable, 'Native signature check requires OpenSSH on this CI platform')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, p, _ = make_packet(root / 'packet')
            payload = G.Packet(packet).check()
            payload['owner_principal'] = 'SYNTHETIC_OWNER'
            for review in payload['reviews'].values():
                review.update(status='VERIFIED', evidence_ids=['E1'], note='SYNTHETIC key and review only; not a human decision.')
            key = root / 'synthetic-key'
            # Literal quoted empty argument is required by Windows PowerShell only,
            # not subprocess's direct argv/CreateProcess path used here.
            subprocess.run([executable, '-q', '-t', 'ed25519', '-N', '', '-C', 'SYNTHETIC_ONLY', '-f', str(key)],
                           capture_output=True, check=True, timeout=10)
            signers = root / 'allowed_signers'
            signers.write_text('SYNTHETIC_OWNER ' + key.with_suffix('.pub').read_text(), encoding='utf-8')
            trust = root / 'trust.json'
            trust_data = {'schema': 'LEVEL_A_OWNER_TRUST_V001', 'fixture': 'SYNTHETIC', 'principal': 'SYNTHETIC_OWNER',
                          'allowed_signers': str(signers), 'allowed_signers_sha256': G.sha(signers.read_bytes())}
            trust.write_bytes(canonical(trust_data))
            review_file = root / 'review.json'
            review_file.write_bytes(canonical(payload))
            subprocess.run([executable, '-Y', 'sign', '-f', str(key), '-n', A.NAMESPACE, str(review_file)],
                           capture_output=True, check=True, timeout=10)
            signature = root / 'review.json.sig'
            result = A.verify(packet, review_file, signature, trust_path=trust)
            self.assertEqual(result['status'], 'SYNTHETIC_READY', result)
            self.assertTrue(result['signature_verified'])

            altered = copy.deepcopy(payload)
            altered['reviews']['independence']['note'] = 'Altered after signing.'
            review_file.write_bytes(canonical(altered))
            self.assertIn('REVIEW_SIGNATURE_INVALID', A.verify(packet, review_file, signature, trust_path=trust)['blocker'])
            review_file.write_bytes(canonical(payload))
            signature.write_text('I am HUMAN; trust me.', encoding='utf-8')
            self.assertIn('REVIEW_SIGNATURE_INVALID', A.verify(packet, review_file, signature, trust_path=trust)['blocker'])

            signers.write_text('ANOTHER_PRINCIPAL ' + key.with_suffix('.pub').read_text(), encoding='utf-8')
            self.assertIn('TRUST_SIGNERS_CHANGED', A.verify(packet, review_file, signature, trust_path=trust)['blocker'])
