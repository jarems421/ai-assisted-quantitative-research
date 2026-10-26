"""Internal capture assessment; shared request/result mapping is deliberately absent."""
from __future__ import annotations

from dataclasses import dataclass

from .common import Artifacts, Invalid, MAX_BYTES, array, loads, need, public_url, text, token
from .providers import CaptureParser, Observation

Path = tuple[str | int, ...]


@dataclass(frozen=True)
class CandidatePointers:
    """Caller-selected JSON locations, to be supplied by the future shared binding.

    No candidate property names or top-level wire layout are defined here.
    publisher_host is optional; it is a model assertion, never a registry lookup.
    """
    url: Path
    requirements: Path
    publisher: Path
    source_kind: Path
    publisher_host: Path | None = None


def at(document, path):
    need(isinstance(path, tuple) and len(path) <= 32, 'INVALID_POINTER')
    value = document
    for part in path:
        if isinstance(value, list):
            need(type(part) is int and 0 <= part < len(value), 'POINTER_NOT_FOUND')
        else:
            need(isinstance(value, dict) and isinstance(part, str) and part in value, 'POINTER_NOT_FOUND')
        value = value[part]
    return value


@dataclass(frozen=True)
class Candidate:
    pointers: CandidatePointers
    url: str | None
    requirements: tuple[str, ...]
    publisher_claim: str | None
    source_kind_claim: str | None
    publisher_host_claim: str | None
    classification: str
    url_key: str | None
    observed_url_refs: tuple[str, ...]
    faults: tuple[str, ...]
    uncertainties: tuple[str, ...]


@dataclass(frozen=True)
class Review:
    artifacts: Artifacts
    observation: Observation
    requested_model: str | None
    candidates: tuple[Candidate, ...]
    duplicate_groups: tuple[tuple[int, ...], ...]
    faults: tuple[str, ...]
    uncertainties: tuple[str, ...]

    @property
    def valid(self):
        return not self.faults and not any(c.faults for c in self.candidates)


def host_allowed(host, domains):
    return not domains or any(host == d or host.endswith('.' + d) for d in domains)


def candidate(document, pointers, requirements, observation, allowed_domains):
    url = publisher = kind = claimed_host = key = None
    reqs, refs, faults = (), (), []
    uncertain = ['URL_EXISTENCE_UNVERIFIED', 'PUBLISHER_IDENTITY_UNVERIFIED', 'DATASET_USABILITY_UNKNOWN']
    try:
        url = text(at(document, pointers.url))
        host, key = public_url(url)
        need(host_allowed(host, allowed_domains), 'OUT_OF_DOMAIN_CANDIDATE')
        reqs = tuple(token(r) for r in array(at(document, pointers.requirements), 32))
        need(reqs and set(reqs) <= set(requirements), 'UNKNOWN_OR_MISSING_REQUIREMENT')
        publisher = text(at(document, pointers.publisher))
        kind = text(at(document, pointers.source_kind), 32)
        need(kind in ('ORIGINAL', 'SECONDARY', 'UNKNOWN'), 'INVALID_SOURCE_KIND')
        if kind != 'ORIGINAL':
            uncertain.append('SECONDARY_SOURCE_CLAIM' if kind == 'SECONDARY' else 'SOURCE_KIND_UNKNOWN')
        if pointers.publisher_host is not None:
            claimed_host = text(at(document, pointers.publisher_host), 253)
            need(public_url('https://' + claimed_host + '/')[0] == claimed_host, 'INVALID_PUBLISHER_HOST')
            if host != claimed_host:
                uncertain.append('PUBLISHER_HOST_MISMATCH')
        refs = tuple(s.locator for s in observation.searches
                     if any(public_url(u)[1] == key for u in s.urls))
        if not refs:
            uncertain.append('URL_NOT_OBSERVED_IN_PROVIDER_METADATA')
    except Invalid as exc:
        faults.append(str(exc))
    classification = ('BASELINE_PROPOSED_SOURCE' if observation.provider == 'DETERMINISTIC_BASELINE'
                      else 'MODEL_PROPOSED_SOURCE')
    return Candidate(pointers, url, reqs, publisher, kind, claimed_host, classification, key, refs,
                     tuple(faults), tuple(uncertain))


def inspect_capture(parser: CaptureParser, *, input_bytes: bytes, output_bytes: bytes, event_bytes: bytes,
                    requested_model: str | None, locations: tuple[CandidatePointers, ...],
                    requirements: tuple[str, ...], allowed_domains: tuple[str, ...] = ()) -> Review:
    """Validate caller-supplied captures only. All raw bytes, including failures, survive.

    Locations must exhaustively enumerate candidates under the future shared
    contract. This utility cannot establish that enumeration or negative meaning.
    allowed_domains is a post-capture lead filter, never retrieval authorisation.
    """
    for value in (input_bytes, output_bytes, event_bytes):
        need(isinstance(value, bytes), 'BYTES_REQUIRED')
    if requested_model is not None:
        token(requested_model)
    artifacts = Artifacts(input_bytes, output_bytes, event_bytes)
    faults, uncertainties = [], []
    # Hash oversize artifacts but do not parse them. This is not a streaming capture bound.
    if len(input_bytes) > MAX_BYTES or len(output_bytes) + len(event_bytes) > MAX_BYTES:
        return Review(artifacts, Observation('UNKNOWN', 'UNPARSED', faults=('CAPTURE_SIZE',)), requested_model,
                      (), (), ('CAPTURE_SIZE',), ())
    observation = parser.parse(event_bytes)
    faults.extend(observation.faults)
    if not observation.complete:
        faults.append('COMPLETION_NOT_ESTABLISHED')
    baseline = observation.provider == 'DETERMINISTIC_BASELINE'
    try:
        if baseline:
            need(requested_model is None, 'BASELINE_MODEL_NOT_APPLICABLE')
        else:
            token(requested_model)
            if not observation.models:
                uncertainties.append('OBSERVED_MODEL_UNKNOWN')
            else:
                need(observation.models == (requested_model,), 'MODEL_IDENTITY_MISMATCH')
            need(observation.final_output == output_bytes, 'OUTPUT_CAPTURE_MISMATCH')
            if not any(s.action != 'citation' for s in observation.searches):
                uncertainties.append('SEARCH_EXECUTION_NOT_OBSERVED')
        need(isinstance(requirements, tuple) and 0 < len(requirements) <= 32, 'INVALID_REQUIREMENTS')
        for r in requirements:
            token(r)
        need(isinstance(allowed_domains, tuple), 'INVALID_DOMAINS')
        for d in allowed_domains:
            need(public_url('https://' + d + '/')[0] == d, 'INVALID_DOMAIN')
        for s in observation.searches:
            for u in s.urls:
                need(host_allowed(public_url(u)[0], allowed_domains), 'OUT_OF_DOMAIN_PROVIDER_URL')
        document = loads(output_bytes)
        need(isinstance(locations, tuple) and len(locations) <= 64
             and all(isinstance(p, CandidatePointers) for p in locations), 'INVALID_LOCATIONS')
        rows = tuple(candidate(document, p, requirements, observation, allowed_domains) for p in locations)
    except Invalid as exc:
        faults.append(str(exc))
        rows = ()
    groups = {}
    for i, row in enumerate(rows):
        if row.url_key is not None:
            groups.setdefault(row.url_key, []).append(i)
    return Review(artifacts, observation, requested_model, rows,
                  tuple(tuple(g) for g in groups.values() if len(g) > 1),
                  tuple(dict.fromkeys(faults)), tuple(uncertainties))
