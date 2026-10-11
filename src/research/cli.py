"""Research OS CLI. Commands are local plans unless --execute is explicit."""
from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from jsonschema import ValidationError

from src.research.analysis import controls, stress_matrix
from src.research.aurora import prompts, evaluation_plan
from src.research.nexus import Jobs, SDK
from src.research.spec import ROOT, digest, experiment_id, validate, stage_window
from src.research.store import Store

COMMANDS = ("propose", "audit", "freeze-hypothesis", "develop", "research", "optimize", "freeze-candidate",
            "validate", "walk-forward", "stress", "authorize-test", "test", "report", "authorize-paper", "paper", "resume", "assess", "ingest-surface", "evaluate-agent", "demo")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def emit(value):
    print(json.dumps(value, indent=2, allow_nan=False))


def handle(args, root):
    exp=experiment_id(args.experiment)
    path=root/"experiments"/exp/"spec.json"
    if args.command=="propose":
        if path.exists():raise ValueError("Specification already exists; refusing overwrite")
        if args.dry_run:
            return {"dry_run":True,"would_create":f"experiments/{exp}/spec.json","stage":"DRAFT","nexus_calls":0}
        spec=load(ROOT/"experiments/_template/spec.example.json")
        spec['experiment_id']=exp
        if exp!='EXP999':
            spec.update(title="TODO: research title",hypothesis="",rationale="",expected_effect="")
            for source in spec['data_sources']:source['point_in_time_verified']=False
            spec['dynamic_universe']['point_in_time_verified']=False
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as f:json.dump(spec,f,indent=2)
        return {'created':str(path.relative_to(root)),'stage':'DRAFT','next':'Edit the specification and establish point-in-time evidence before audit/freeze.','nexus_calls':0}
    spec=validate(load(args.spec or path))
    if spec['experiment_id']!=exp:raise ValueError('Specification identifier mismatch')
    store=Store(root)
    try:
        try:state=store.state(exp)
        except ValueError:
            store.register(spec);state=store.state(exp)
        state=store.verify(spec)
        if args.command=='audit':
            return {'valid':True,'stage':state['stage'],'spec_hash':digest(spec),'point_in_time_assertions':'Require human source audit; schema validation alone is not proof.','nexus_calls':0}
        if args.command=='research':
            return {'roles':prompts(spec),'remote_execution':'disabled: no server tool/date isolation exposed','nexus_calls':0}
        if args.command=='evaluate-agent':return evaluation_plan(args.agent_id or 'SUPPLY_AGENT_ID')
        if args.command=='ingest-surface':
            if not args.input or not args.job_key:raise ValueError('--input audited full-cell normalization and --job-key required')
            from src.research.ingestion import sweep_cells
            return sweep_cells(store,spec,args.job_key,load(args.input))
        if args.command=='assess':
            if not args.input or not args.job_key:raise ValueError('--input and --job-key required')
            job=store.db.execute('SELECT * FROM jobs WHERE key=? AND experiment=?',(args.job_key,exp)).fetchone()
            if job is None or job['status'] not in ('COMPLETE','COMPLETED'):raise ValueError('Only completed evidenced jobs can be assessed')
            from src.research.report import compute
            evidence=load(args.input)
            metrics=compute(spec,{'candidate':{'stage':job['stage'],'closes':evidence['closes']}},test_authorized=job['stage']=='TEST_AUTHORIZED')['candidate']
            from src.research.ingestion import eligible as assess_eligibility
            eligible=assess_eligibility(spec,metrics,evidence)
            request=json.loads(job['request'])
            store.record_trial(args.job_key,exp,request['family'],request['candidate'],request['parameters'],job['stage'],
                               {'status':job['status'],'metrics':metrics,'evidence_hash':digest(evidence),'evaluations':request['budget']['planned_evaluations']},
                               run_id=job['operation_id'],eligibility=eligible)
            return {'metrics':metrics,'eligible':eligible}
        if args.command=='freeze-hypothesis':return store.transition(spec,'HYPOTHESIS_FROZEN')
        if args.command=='freeze-candidate':
            if not args.candidate:raise ValueError('--candidate JSON required')
            candidate=load(args.candidate)
            candidate['controls']=controls(candidate['signals'])
            return store.transition(spec,'CANDIDATE_FROZEN',candidate=candidate)
        if args.command in ('authorize-test','authorize-paper'):
            target='TEST_AUTHORIZED' if args.command=='authorize-test' else 'PAPER_AUTHORIZED'
            expected=f'OPEN {exp} TEST' if target=='TEST_AUTHORIZED' else f'DEPLOY {exp} PAPER'
            if args.dry_run:return {'dry_run':True,'current_stage':state['stage'],'target':target,'required_interactive_confirmation':expected,'no_authorization_written':True}
            if not sys.stdin.isatty():raise ValueError('Authorization requires the owner in an interactive terminal; automation may not supply confirmation')
            confirmation=input(f'Type exactly {expected}: ')
            return store.transition(spec,target,confirmation=confirmation,human=True)
        if args.command=='report':
            if not args.input:raise ValueError('--input normalized report evidence JSON required')
            from src.research.report import write
            trials=load(root/'experiments'/exp/'trials.json') if (root/'experiments'/exp/'trials.json').exists() else []
            result=write(root,spec,state,load(args.input),trials)
            if root==ROOT and state['stage'] in ('TEST_COMPLETE','PAPER_AUTHORIZED','PAPER'):
                from src.presentation.exp001 import generate
                generate(ROOT,ROOT)
            return {'metrics':result,'report':f'reports/{exp}_report.md','nexus_calls':0}
        if args.command=='stress':
            if state['stage']=='WALK_FORWARD':state=store.transition(spec,'ROBUSTNESS')
            if state['stage']!='ROBUSTNESS':raise ValueError('Stress requires completed walk-forward evidence')
            observations=load(args.input) if args.input else {}
            matrix=stress_matrix(spec['stress_scenarios'],observations)
            review={'spec_hash':digest(spec),'candidate_hash':state['candidate_hash'],
                    'matrix':matrix,'review_complete':all(r['status']=='observed' for r in matrix.values())}
            (root/'experiments'/exp/'robustness.json').write_text(json.dumps(review,indent=2)+'\n')
            return review
        if args.command in ('develop','validate','walk-forward'):
            target={'develop':'DEVELOPMENT','validate':'VALIDATION','walk-forward':'WALK_FORWARD'}[args.command]
            if state['stage']!=target:state=store.transition(spec,target)
        if args.command=='test' and state['stage']!='TEST_AUTHORIZED':raise ValueError('Historical Test is sealed until human authorization')
        if args.command=='optimize' and state['stage']!='DEVELOPMENT':raise ValueError('Optimization confined to Development')
        if args.command not in ('develop','validate','walk-forward','optimize','test','paper','resume'):
            raise ValueError('Unsupported command')
        if args.execute:
            if not args.mcp_bridge:raise ValueError('--mcp-bridge module:call required; no automatic MCP OAuth endpoint is invented')
            module,function=args.mcp_bridge.split(':',1)
            bridge=getattr(importlib.import_module(module),function)
            sdk=SDK(api_key=os.environ.get('NEXUSTRADE_API_KEY'))
        else:
            bridge=None;sdk=None
        jobs=Jobs(store,sdk,mcp=bridge)
        if args.command=='paper':
            if not args.paper_portfolio:raise ValueError('--paper-portfolio saved matching chat draft required')
            return jobs.deploy_paper(spec,args.paper_portfolio,execute=args.execute)
        if args.command=='resume':
            if not args.job_key:raise ValueError('--job-key required')
            if not args.execute:return {'dry_run':True,'resume_same_key':args.job_key,'no_new_submission':True}
            return jobs.poll(spec,args.job_key)
        kind={'optimize':'sweep','walk-forward':'walk_forward'}.get(args.command,'backtest')
        window=stage_window(spec,state['stage'])
        if args.candidate:
            candidate=load(args.candidate)
        else:
            candidate=store.candidate(spec) if state['candidate'] else None
        if not candidate:
            return {'stage':state['stage'],'operation':kind,'window':window,'requires':'Reviewed inline candidate JSON; no candidate or Nexus portfolio generated','nexus_calls':0}
        if args.benchmark:
            if args.benchmark not in candidate.get('benchmarks',{}):raise ValueError('Benchmark portfolio not frozen')
            candidate=dict(candidate,portfolio=candidate['benchmarks'][args.benchmark],name=args.benchmark)
        if args.job_config:
            payload=load(args.job_config)
        elif kind=='backtest':
            import nexustrade
            p=importlib.import_module('nexustrade.portfolio')
            payload=p.backtest(candidate['portfolio'],start_date=window['start'],end_date=window['end'],
                               baseline_symbol=spec['benchmarks'][0],interval=spec['execution']['interval'],
                               initial_value=spec['costs']['initial_value'],generate_events=spec['execution']['requires_events'],
                               fee_config=spec['costs']['fee_contract'],dividend_policy=spec['costs']['dividend_policy'])
        else:
            return {'stage':state['stage'],'operation':kind,'window':window,'planned_evaluations':math.prod(len(v) for v in spec['optimization_ranges'].values())*args.folds,
                    'requires':'--job-config observed SDK handle with reviewed compiled genes and fold calendar; no invented sweep fields','nexus_calls':0}
        planned=math.prod(len(v) for v in spec['optimization_ranges'].values()) if kind=='sweep' else args.evaluations
        result=jobs.submit(spec,kind,payload,load(ROOT/'config/research_pricing.json'),family=candidate.get('family','declared'),
                           candidate=candidate.get('name','candidate'),parameters=candidate.get('parameters',{}),
                           assets=args.assets,evaluations=planned,folds=args.folds,execute=args.execute)
        if args.execute:
            result=jobs.poll(spec,result['key'])
            if args.command=='test' and str(result.get('status')).lower() in ('complete','completed'):
                store.transition(spec,'TEST_COMPLETE')
        return result
    finally:store.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=COMMANDS)
    parser.add_argument('experiment',nargs='?',default='EXP999')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--execute',action='store_true',help='Explicit remote submission; absent means local planning only')
    for name in ('spec','candidate','job-config','input','mcp-bridge','paper-portfolio','job-key','agent-id'):
        parser.add_argument('--'+name)
    parser.add_argument('--assets',type=int,default=500)
    parser.add_argument('--evaluations',type=int,default=1)
    parser.add_argument('--folds',type=int,default=1)
    parser.add_argument('--benchmark',help='Run an explicitly frozen benchmark instead of the candidate')
    args=parser.parse_args(argv)
    if args.dry_run and args.execute:parser.error('--dry-run and --execute are mutually exclusive')
    try:
        if args.command=='demo':
            if args.experiment!='EXP999' or args.execute:raise ValueError('Demo is synthetic EXP999 only')
            from src.research.demo import demo
            emit(demo());return
        if args.dry_run:
            with tempfile.TemporaryDirectory(prefix='research-dry-run-') as directory:
                root=Path(directory)
                actual=ROOT/'.research/state.sqlite'
                if actual.exists():
                    (root/'.research').mkdir()
                    source=sqlite3.connect(f'file:{actual.as_posix()}?mode=ro',uri=True)
                    destination=sqlite3.connect(root/'.research/state.sqlite')
                    source.backup(destination);source.close();destination.close()
                if not args.spec and args.command!='propose':args.spec=str(ROOT/'experiments'/args.experiment/'spec.json')
                emit(handle(args,root))
        else:emit(handle(args,ROOT))
    except (ValueError,KeyError,PermissionError,FileNotFoundError,ValidationError) as error:
        parser.exit(2,f'Research gate: {error}\n')


if __name__=='__main__':main()
