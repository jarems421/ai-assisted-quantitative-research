# Source Retrieval loopback TLS fixtures (offline tests only)

These certificates are fictional and exist only for `tests/test_source_retrieval_transport_v1.py`. Its server listens on `127.0.0.1` and nothing else.

| File | Purpose |
|---|---|
| `ca.pem` | Self-signed "Fictional Source Retrieval Test CA". Only these tests trust it. Its private key was deleted after signing, so no further certificate can be issued from it |
| `server.pem`, `server-key.pem` | Leaf for `documents.example.org` (an RFC 2606 example domain), signed by the test CA |
| `wrong-host.pem`, `wrong-host-key.pem` | Leaf for `other.example.net`, used to prove hostname verification |

The private keys are deliberately public test material. Never trust this CA anywhere else, and never use these keys outside these tests. All certificates were generated on 2026-10-26 with OpenSSL 3.5.7 (P-256, SHA-256) and expire in 2126.
