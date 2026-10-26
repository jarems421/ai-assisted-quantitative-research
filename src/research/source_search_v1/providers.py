"""Restricted offline capture profiles. These parsers never invoke a provider.

Codex accepts one JSONL turn. Responses accepts a final Response JSON snapshot,
not SSE/deltas. Neither profile is runtime-qualified by synthetic acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .common import Invalid, MAX_BYTES, MAX_ITEMS, array, loads, need, obj, public_url, text, token


@dataclass(frozen=True)
class SearchEvent:
    locator: str
    call_id: str
    action: str
    queries: tuple[str, ...]
    urls: tuple[str, ...]


@dataclass(frozen=True)
class Observation:
    provider: str
    profile: str
    models: tuple[str, ...] = ()
    usage: tuple[tuple[str, int], ...] = ()
    searches: tuple[SearchEvent, ...] = ()
    final_output: bytes | None = None
    complete: bool = False
    faults: tuple[str, ...] = ()


class CaptureParser(Protocol):
    """Future runtimes supply retained bytes to this interface; no execute method."""
    def parse(self, events: bytes) -> Observation: ...


def usage(value, keys):
    obj(value)
    result = []
    for key in keys:
        n = value.get(key)
        need(type(n) is int and 0 <= n <= 10**12, 'INVALID_USAGE')
        result.append((key, n))
    return tuple(result)


def search(action, call_id, locator):
    obj(action)
    kind = action.get('type')
    need(kind in ('search', 'open_page', 'find_in_page'), 'UNKNOWN_SEARCH_ACTION')
    queries, urls = [], []
    if kind == 'search':
        if 'queries' in action:
            queries.extend(text(q) for q in array(action['queries'], 64))
        if 'query' in action:
            queries.append(text(action['query']))
        for source in array(action.get('sources', []), 256):
            obj(source)
            need(source.get('type') == 'url', 'UNKNOWN_SOURCE_TYPE')
            public_url(source.get('url'))
            urls.append(source['url'])
    else:
        public_url(action.get('url'))
        urls.append(action['url'])
        if kind == 'find_in_page':
            text(action.get('pattern'))
    return SearchEvent(locator, token(call_id), kind, tuple(queries), tuple(urls))


@dataclass(frozen=True)
class CodexJSONL:
    def parse(self, events: bytes) -> Observation:
        models, searches, completed, messages, pending, item_types = set(), [], set(), [], set(), {}
        observed_usage = ()
        complete = False
        faults = []
        try:
            need(isinstance(events, bytes) and len(events) <= MAX_BYTES, 'CAPTURE_SIZE')
            lines = events.splitlines()
            need(0 < len(lines) <= MAX_ITEMS and all(lines), 'INVALID_JSONL')
            rows = [obj(loads(line)) for line in lines]
            kinds = [r.get('type') for r in rows]
            need(kinds[:2] == ['thread.started', 'turn.started'] and kinds[-1] == 'turn.completed'
                 and kinds.count('thread.started') == kinds.count('turn.started') == kinds.count('turn.completed') == 1,
                 'INCOMPLETE_OR_MULTIPLE_TURNS')
            token(rows[0].get('thread_id'))
            for i, row in enumerate(rows):
                kind = row['type']
                need(kind in ('thread.started', 'turn.started', 'item.started', 'item.updated',
                              'item.completed', 'turn.completed'), 'UNEXPECTED_EVENT')
                # Root event metadata only. Never inspect model identity inside message JSON.
                for key in ('model', 'model_slug'):
                    if key in row:
                        models.add(token(row[key]))
                if kind.startswith('item.'):
                    item = obj(row.get('item'))
                    iid = token(item.get('id'))
                    typ = item.get('type')
                    need(typ in ('agent_message', 'reasoning', 'web_search'), 'UNEXPECTED_TOOL_ITEM')
                    need(iid not in completed, 'ITEM_AFTER_COMPLETION')
                    need(iid not in item_types or item_types[iid] == typ, 'ITEM_TYPE_CHANGED')
                    need(kind != 'item.started' or iid not in pending, 'DUPLICATE_ITEM_START')
                    item_types[iid] = typ
                    if kind != 'item.completed':
                        pending.add(iid)
                    if kind == 'item.completed':
                        pending.discard(iid)
                        completed.add(iid)
                        if typ == 'agent_message':
                            messages.append(text(item.get('text'), MAX_BYTES, multiline=True).encode('utf-8'))
                        elif typ == 'web_search':
                            need(item.get('status') in (None, 'completed'), 'INCOMPLETE_SEARCH')
                            # This fixture profile requires explicit action metadata. No inference from prose.
                            searches.append(search(item.get('action'), iid, f'line:{i + 1}/item/action'))
            need(len(messages) == 1, 'FINAL_MESSAGE_COUNT')
            need(not pending, 'INCOMPLETE_ITEM')
            observed_usage = usage(rows[-1].get('usage'), ('input_tokens', 'cached_input_tokens', 'output_tokens'))
            need(dict(observed_usage)['cached_input_tokens'] <= dict(observed_usage)['input_tokens'], 'INVALID_USAGE')
            complete = True
        except Invalid as exc:
            faults.append(str(exc))
        return Observation('CODEX_CLI', 'CODEX_JSONL_OFFLINE_V001', tuple(sorted(models)), observed_usage,
                           tuple(searches), messages[0] if len(messages) == 1 else None, complete, tuple(faults))


@dataclass(frozen=True)
class ResponsesSnapshot:
    def parse(self, events: bytes) -> Observation:
        models, searches, messages = [], [], []
        observed_usage = ()
        complete = False
        faults = []
        try:
            root = obj(loads(events))
            need(root.get('object') == 'response', 'NOT_RESPONSE_SNAPSHOT')
            token(root.get('id'))
            if root.get('model') is not None:
                models.append(token(root['model']))
            need(root.get('status') == 'completed' and root.get('error') is None
                 and root.get('incomplete_details') is None, 'INCOMPLETE_RESPONSE')
            ids = set()
            for i, item in enumerate(array(root.get('output'))):
                obj(item)
                iid = token(item.get('id'))
                need(iid not in ids, 'DUPLICATE_ITEM')
                ids.add(iid)
                kind = item.get('type')
                need(kind in ('web_search_call', 'reasoning', 'message'), 'UNEXPECTED_TOOL_ITEM')
                if kind == 'web_search_call':
                    need(item.get('status') == 'completed', 'INCOMPLETE_SEARCH')
                    searches.append(search(item.get('action'), iid, f'/output/{i}/action'))
                elif kind == 'message':
                    need(item.get('role') == 'assistant' and item.get('status') == 'completed', 'INVALID_MESSAGE')
                    parts = array(item.get('content'), 32)
                    need(len(parts) == 1 and obj(parts[0]).get('type') == 'output_text', 'REFUSED_OR_INVALID_OUTPUT')
                    messages.append(text(parts[0].get('text'), MAX_BYTES, multiline=True).encode('utf-8'))
                    for j, annotation in enumerate(array(parts[0].get('annotations', []), 256)):
                        obj(annotation)
                        need(annotation.get('type') == 'url_citation', 'UNKNOWN_ANNOTATION')
                        public_url(annotation.get('url'))
                        searches.append(SearchEvent(f'/output/{i}/content/0/annotations/{j}', iid,
                                                    'citation', (), (annotation['url'],)))
            need(len(messages) == 1, 'FINAL_MESSAGE_COUNT')
            observed_usage = usage(root.get('usage'), ('input_tokens', 'output_tokens', 'total_tokens'))
            u = dict(observed_usage)
            need(u['input_tokens'] + u['output_tokens'] == u['total_tokens'], 'INVALID_USAGE')
            complete = True
        except Invalid as exc:
            faults.append(str(exc))
        return Observation('RESPONSES_API', 'RESPONSES_SNAPSHOT_OFFLINE_V001', tuple(models), observed_usage,
                           tuple(searches), messages[0] if len(messages) == 1 else None, complete, tuple(faults))


@dataclass(frozen=True)
class BaselineCapture:
    """No baseline search implemented: inspect a caller's already-supplied output.

The caller binds its exact local index/algorithm bytes in the opaque input.
Empty provider events mean no observed provider events, not proof of execution.
"""
    def parse(self, events: bytes) -> Observation:
        return Observation('DETERMINISTIC_BASELINE', 'BASELINE_CAPTURE_OFFLINE_V001', complete=events == b'',
                           faults=() if events == b'' else ('UNEXPECTED_BASELINE_EVENTS',))
