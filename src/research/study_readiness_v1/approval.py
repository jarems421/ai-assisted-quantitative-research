"""Verify a separate owner-controlled review; no signing or trust-enrolment commands.

SSH proves possession of a trusted key, not that its holder is human or inspected a
source. The owner must enrol/protect trust outside the checkout and keep the signing
key unavailable to assistants. Processes that can replace that trust can bypass it.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.research.spec import canonical
from .gate import CHECKS, Packet, NotReady, read_json, require, sha, text

NAMESPACE = 'research-os-level-a-v001'
TRUST = Path.home() / '.research-os' / 'level-a-trust.json'


def verify_signature(payload, signature, trust):
    executable = shutil.which('ssh-keygen')
    require(executable is not None, 'REVIEW: OpenSSH ssh-keygen unavailable')
    signers = Path(trust['allowed_signers'])
    require(signers.is_absolute() and sha(signers.read_bytes()) == trust['allowed_signers_sha256'], 'TRUST_SIGNERS_CHANGED')
    signers = signers.resolve()
    result = subprocess.run([executable, '-Y', 'verify', '-f', str(signers), '-I', trust['principal'],
                             '-n', NAMESPACE, '-s', str(Path(signature).resolve())],
                            input=canonical(payload), capture_output=True, timeout=10, check=False)
    require(result.returncode == 0, 'REVIEW_SIGNATURE_INVALID')


def verify(packet_path, approval_path, signature_path, *, trust_path=None):
    """No execution path. trust_path is for controlled embedding/tests, never from a packet."""
    try:
        packet = Packet(packet_path)
        expected = packet.check()
        trust_file = Path(trust_path) if trust_path is not None else TRUST
        require(not trust_file.resolve().is_relative_to(packet.root), 'TRUST: must be independently enrolled outside packet')
        trust = read_json(trust_file.read_bytes())
        require(trust['schema'] == 'LEVEL_A_OWNER_TRUST_V001' and text(trust['principal']), 'OWNER_TRUST_REQUIRED')
        require(trust['fixture'] == expected['fixture'], 'TRUST_FIXTURE_MISMATCH')
        require(not Path(trust['allowed_signers']).resolve().is_relative_to(packet.root), 'TRUST: signers must be outside packet')
        if expected['fixture'] != 'SYNTHETIC':
            checkout = Path(__file__).resolve().parents[3]
            require(not trust_file.resolve().is_relative_to(checkout)
                    and not Path(trust['allowed_signers']).resolve().is_relative_to(checkout), 'TRUST: outside checkout required')
        approval = read_json(Path(approval_path).read_bytes())
        require(set(approval) == set(expected) | {'owner_principal'}, 'REVIEW_FIELDS_INVALID')
        require(approval['owner_principal'] == trust['principal'], 'OWNER_PRINCIPAL_MISMATCH')
        require({k: v for k, v in approval.items() if k not in ('reviews', 'owner_principal')}
                == {k: v for k, v in expected.items() if k != 'reviews'}, 'REVIEW_SCOPE_OR_INPUT_CHANGED')
        require(set(approval['reviews']) == set(CHECKS), 'INDEPENDENT_REVIEW_INCOMPLETE')
        all_evidence = sorted(e['id'] for e in packet.p['evidence'])
        for key, review in approval['reviews'].items():
            require(set(review) == {'status', 'evidence_ids', 'note'} and review['status'] == 'VERIFIED'
                    and review['evidence_ids'] == all_evidence and text(review['note']), f'INDEPENDENT_REVIEW_REQUIRED:{key}')
        verify_signature(approval, signature_path, trust)
        return {'status': 'SYNTHETIC_READY' if expected['fixture'] == 'SYNTHETIC' else 'OWNER_REVIEWED_LEVEL_A_PREFLIGHT',
                'ready': True, 'authorises': [], 'design_sha256': expected['design_sha256'],
                'scope_sha256': expected['owner_scope_sha256'], 'signature_verified': True,
                'human_identity_authenticated': False, 'source_meaning_certified_by_software': False}
    except (ValueError, KeyError, TypeError, OSError, IndexError, RecursionError, subprocess.SubprocessError) as error:
        return {'status': 'BLOCKED', 'ready': False, 'authorises': [], 'blocker': str(error)}
