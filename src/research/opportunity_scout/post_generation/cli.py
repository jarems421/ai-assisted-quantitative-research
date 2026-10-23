"""Post-generation Jev shadow review: import a saved response, build a label packet, compare. No hosted call, ever."""
from __future__ import annotations

import argparse
import sys

from src.research.spec import canonical, digest
from .. import BANNER
from .. import schema as S
from ..cli import emit
from ..storage import Archive, input_json, unlinked
from . import review as SR


def stores(values):
    out = dict(x.split('=', 1) for x in values)
    if len(out) != len(values) or any(not k or not v for k, v in out.items()):raise S.ScoutError('--store is NAME=PATH with distinct names')
    return {k: Archive(v).load() for k, v in out.items()}


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog=BANNER)
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('import-response', help='import a saved Jev System One response file unchanged as a shadow record')
    x.add_argument('store'); x.add_argument('idea'); x.add_argument('response')
    x.add_argument('--cost', default=S.UNKNOWN, help='only if separately evidenced; System One reports no price')
    x.add_argument('--currency', choices=('USD', S.UNKNOWN), default=S.UNKNOWN)
    x.add_argument('--synthetic-fixture', action='store_true', help='synthetic batches only')
    x = sub.add_parser('label-packet', help='non-comparative blinded packet for independent labels (no Jev output)')
    x.add_argument('--store', action='append', required=True, metavar='NAME=PATH'); x.add_argument('--salt-file', required=True)
    x.add_argument('--out', required=True, help='new folder for the packet and the private key')
    x = sub.add_parser('compare', help='descriptive Jev comparison against independent labels (shadow only)')
    x.add_argument('--store', action='append', required=True, metavar='NAME=PATH'); x.add_argument('--packet', required=True)
    x.add_argument('--key', required=True); x.add_argument('--labels', help='JSON list of label records; omit to report what is missing')
    return p


def dispatch(a):
    if a.command == 'compare':
        return SR.compare(stores(a.store), input_json(a.packet), input_json(a.key), input_json(a.labels) if a.labels else [])
    if a.command == 'label-packet':
        packet, key = SR.label_packet(stores(a.store), input_json(a.salt_file)['salt'])
        out = unlinked(a.out); out.mkdir(parents=True, exist_ok=False)
        for name, value in (('shadow-label-packet.json', packet), ('shadow-label-key-private.json', key)):(out / name).write_bytes(canonical(value))
        return {'packet': str(out / 'shadow-label-packet.json'), 'private_key': str(out / 'shadow-label-key-private.json'),
                'cards': len(packet['cards']), 'comparative_eligible': False,
                'warning': 'Labellers receive only the packet: never the key, the archives or any Jev output.'}
    archive = Archive(a.store); response = input_json(a.response)
    record = SR.import_response(archive.load(), a.idea, response, cost=a.cost if a.cost == S.UNKNOWN else float(a.cost), currency=a.currency,
                                transport='SYNTHETIC_FIXTURE' if a.synthetic_fixture else 'IMPORTED_NOT_CALLED')
    state = archive.append('shadow', record)
    return {'recorded': 'shadow', 'idea_id': a.idea, 'version': record['version'], 'request_sha256': record['request_sha256'],
            'response_sha256': digest(response), 'events': len(state.events), 'routing_changed': False, 'authorises': []}


def main(argv=None):
    try:emit(dispatch(parser().parse_args(argv)))
    except (S.ScoutError, ValueError, OSError, KeyError, TypeError) as error:
        print(f'Opportunity Scout post-generation: {error}', file=sys.stderr)
        return 2
    return 0
