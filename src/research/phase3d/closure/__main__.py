"""Bounded offline closure review/report verification; never acquire sources."""
import argparse,json
from .report import generate,DOCS
from .accounting import build as accounting
from .lifecycle import build as lifecycle

parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('command',choices=['report','sources']);parser.add_argument('--check',action='store_true')
args=parser.parse_args()
if args.command=='report':print('Closure reports verified/generated',generate(args.check))
else:
    if not args.check:raise ValueError('Source review is verification-only through this public entry point')
    a=accounting();i,t=lifecycle()
    for name,actual in [('phase3d_accounting_review.json',a),('phase3d_identity_closure.json',i),('phase3d_terminal_closure.json',t)]:
        if actual!=json.loads((DOCS/name).read_bytes()):raise ValueError('Source review changed: '+name)
    print('All89 originals /60 cases reconcile to retained private packets; zero acquisition')
