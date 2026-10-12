"""Public feasibility reports only; no acquire, calibrate or execute command."""
import argparse
from .report import generate
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('command',choices=['report'])
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
print('Phase 3E artifacts verified/generated:',generate(args.check))
