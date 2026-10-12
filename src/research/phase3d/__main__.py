"""Offline Phase 3D entry point, separate from real experiment state and transport."""
import argparse
import json
from pathlib import Path
from .report import self_check,generate,DOCS
from .proof import compile_manifest,replay
from .review import candidate_census
from .inference import calibrate

parser=argparse.ArgumentParser(description=__doc__)
commands=parser.add_subparsers(dest='command',required=True)
commands.add_parser('check')
report=commands.add_parser('report'); report.add_argument('--check',action='store_true')
review=commands.add_parser('review'); review.add_argument('--check',action='store_true',required=True)
calibration=commands.add_parser('calibrate'); calibration.add_argument('--check',action='store_true',required=True)
compile_cmd=commands.add_parser('compile'); compile_cmd.add_argument('spec'); compile_cmd.add_argument('root'); compile_cmd.add_argument('output'); compile_cmd.add_argument('--authority',required=True)
replay_cmd=commands.add_parser('replay'); replay_cmd.add_argument('manifest'); replay_cmd.add_argument('root'); replay_cmd.add_argument('--authority',required=True)
args=parser.parse_args()
if args.command=='check':
    self_check(); print('Synthetic proof replay and hand-accounted execution fixtures PASS; Nexus disabled')
elif args.command=='report': print('Reports verified/generated:',generate(check=args.check))
elif args.command=='review':
    actual=candidate_census(); expected=json.loads((DOCS/'phase3d_source_census.json').read_bytes())
    if actual!=expected: raise ValueError('Source census changed')
    print('89-original offline census reconciles exactly; zero acquisition')
elif args.command=='calibrate':
    protocol=json.loads((DOCS/'phase3d_inference_protocol.json').read_bytes())
    actual=calibrate(protocol); expected=json.loads((DOCS/'phase3d_inference_calibration.json').read_bytes())
    expected.pop('freeze_receipt_sha256')
    if actual!=expected: raise ValueError('Synthetic calibration changed')
    print('Frozen synthetic calibration reproduces exactly; no selected method')
elif args.command=='compile':
    manifest,path=compile_manifest(json.loads(Path(args.spec).read_bytes()),args.root,args.output,
                                  authority=json.loads(Path(args.authority).read_bytes()))
    print('Synthetic immutable manifest:',path)
else:
    print(replay(args.manifest,args.root,authority=json.loads(Path(args.authority).read_bytes()))['status'])
