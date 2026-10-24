"""Discovery Lab command line. Local files only: no network, no acquisition, no experiment registration."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from src.research.discovery import demo, records as R
from src.research.discovery.ledger import Ledger, WriterLockNotReleased
from src.research.discovery.report import compare, summary
from src.research.discovery.review import checklist, source_next

PROMPTS = Path(__file__).resolve().parents[3] / 'docs/strategy/discovery_lab_prompts.md'


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def prompt(stage):
    text = PROMPTS.read_text(encoding='utf-8')
    sections = dict(re.findall(r'^## `([a-z-]+)`\n(.*?)(?=^## `|\Z)', text, re.M | re.S))
    if stage not in sections:raise ValueError(f'unknown stage {stage!r}; choose from {sorted(sections)}')
    return sections[stage].strip()


def context(ledger, rid):
    s = Ledger(ledger).load()
    for kind in R.VERSIONED:
        if s.latest(kind, rid):
            out = {'record': s.latest(kind, rid)}
            if kind == 'candidate':out['checklist'] = checklist(s, rid)
            if kind == 'source':out['next_evidence'] = source_next(s.latest(kind, rid))
            return out
    raise ValueError(f'{rid} not found in {ledger}')


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m src.research.discovery', description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('init', help='create a campaign ledger from a campaign record');c.add_argument('ledger');c.add_argument('campaign')
    c = sub.add_parser('template', help='print a blank record');c.add_argument('kind', choices=sorted(R.KEYS))
    c = sub.add_parser('add', help='validate and append a record');c.add_argument('ledger');c.add_argument('kind', choices=sorted(set(R.KEYS) - {'campaign'}));c.add_argument('record')
    c = sub.add_parser('freeze', help='freeze the latest version of a candidate claim');c.add_argument('ledger');c.add_argument('candidate')
    c = sub.add_parser('validate', help='verify hash chains and replay every rule');c.add_argument('ledgers', nargs='+')
    c = sub.add_parser('checklist', help='mechanical M/H checklist (never certifies M)');c.add_argument('ledger');c.add_argument('candidate');c.add_argument('--version', type=int)
    c = sub.add_parser('source', help='Source Passport next-evidence rung');c.add_argument('ledger');c.add_argument('source')
    c = sub.add_parser('summary', help='readable campaign summary');c.add_argument('ledger')
    c = sub.add_parser('compare', help='descriptive method comparison');c.add_argument('ledgers', nargs='+')
    c = sub.add_parser('prompt', help='print a structured Claude research prompt');c.add_argument('stage');c.add_argument('--ledger');c.add_argument('--record')
    c = sub.add_parser('demo', help='offline synthetic walkthrough');g = c.add_mutually_exclusive_group();g.add_argument('--write', action='store_true');g.add_argument('--check', action='store_true');c.add_argument('--out')
    a = p.parse_args(argv)
    try:
        if a.command == 'init':emit({'created': a.ledger, 'hash': Ledger.create(a.ledger, load_json(a.campaign)).load().events[0]['hash']})
        elif a.command == 'template':emit(R.template(a.kind))
        elif a.command == 'add':event = Ledger(a.ledger).append(a.kind, load_json(a.record));emit({'appended': event['seq'], 'type': a.kind, 'derived': event['derived'], 'hash': event['hash']})
        elif a.command == 'freeze':event = Ledger(a.ledger).freeze(a.candidate);emit({'frozen': event['record'], 'derived': event['derived'], 'hash': event['hash']})
        elif a.command == 'validate':emit({path: {'events': len(Ledger(path).load().events), 'chain_and_rules': 'PASS'} for path in a.ledgers})
        elif a.command == 'checklist':emit(checklist(Ledger(a.ledger).load(), a.candidate, a.version))
        elif a.command == 'source':
            s = Ledger(a.ledger).load(); passport = s.latest('source', a.source)
            if passport is None:raise ValueError(f'unknown source {a.source}')
            rung, why = source_next(passport); emit({'source': a.source, 'version': passport['version'], 'next_rung': rung, 'why': why})
        elif a.command == 'summary':print(summary(Ledger(a.ledger).load()))
        elif a.command == 'compare':print(compare([Ledger(path).load() for path in a.ledgers]))
        elif a.command == 'prompt':
            print(prompt(a.stage))
            if a.ledger and a.record:print('\n### Record context (verify against sources; context is not evidence)\n');emit(context(a.ledger, a.record))
        elif a.command == 'demo':
            if a.check:emit(demo.check())
            elif a.write:demo.WALKTHROUGH.write_text(demo.generate(), encoding='utf-8', newline='\n');emit({'written': str(demo.WALKTHROUGH.relative_to(demo.ROOT))})
            elif a.out:
                out = Path(a.out); out.mkdir(parents=True, exist_ok=True); text = demo.run(out)
                (out / 'walkthrough.md').write_text(text, encoding='utf-8', newline='\n'); emit({'ledgers_and_walkthrough': str(out)})
            else:print(demo.generate())
    except WriterLockNotReleased as error:
        # Committed, not refused: report the event so the operator reconciles instead of retrying.
        emit({'committed': error.seq, 'hash': error.hash, 'writer_lock_left': error.lock})
        print(f'committed but not released: {error}', file=sys.stderr); raise SystemExit(3)
    except ValueError as error:
        print(f'refused: {error}', file=sys.stderr); raise SystemExit(2)


if __name__ == '__main__':
    main()
