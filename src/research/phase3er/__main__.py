"""Explicit source opt-in and offline design checks; no real research stage path."""
import argparse
from .report import generate
from .geometry import generate as geometry
from .audit import audit
from .sources import acquire
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('command',choices=['report','geometry','audit','acquire'])
parser.add_argument('--check',action='store_true');parser.add_argument('--execute',action='store_true')
args=parser.parse_args()
if args.command=='report':print('Redesign reports verified/generated:',generate(args.check))
elif args.command=='geometry':print('Geometry/policy verified/generated:',geometry(args.check))
elif args.command=='audit':print(audit())
else:
    if not args.execute:raise ValueError('Source acquisition is a remote mutation; explicit opt-in required')
    print('Bounded source records:',len(acquire()['records']))
