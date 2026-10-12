"""Read-only documentation consistency check; no acquisition or experiment path."""
import argparse,json,re
from pathlib import Path
from src.research.spec import digest

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs/acceleration'


def check():
    status=json.loads((DOCS/'phase4a_status.json').read_bytes())
    expected={'PHASE3_COMPLETION':'COMPLETE_EXP005_ABANDONED','PHASE4A':'ACTIVE_EXPERIMENT_SELECTION',
              'NEXT_EXPERIMENT':'NOT_YET_FROZEN','PERFORMANCE_AUTHORIZED':False,'NEXUS_EXECUTION':'BLOCKED',
              'PAPER_TRADING':'NOT_AUTHORIZED','LIVE_TRADING':'NOT_AUTHORIZED'}
    if any(status.get(k)!=v for k,v in expected.items()) or status['family_owner_approval'] is not None:
        raise ValueError('Selection authority/state mismatch')
    scores=json.loads((DOCS/'phase4a_candidate_scorecard.json').read_bytes())
    if len(scores['candidates'])!=3 or len(scores['criteria'])!=16:raise ValueError('Frozen shortlist/rubric changed')
    if len({c['id'] for c in scores['candidates']})!=3:raise ValueError('Repeated family')
    for c in scores['candidates']:
        if set(c['criteria'])!=set(scores['criteria']):raise ValueError('Missing score criterion')
        values=[r['score'] for r in c['criteria'].values()]
        if any(v is not None and (type(v) is not int or v not in (0,1,2)) for v in values):raise ValueError('Invalid qualitative score')
        total=sum(v for v in values if v is not None);unknown=values.count(None)
        if (c['known_subtotal']!=total or c['unknown_criteria']!=unknown or c['possible_score_interval']!=[total,total+2*unknown]
            or c['usable_event_count'] is not None or c['effective_independent_count'] is not None
            or c['design_advance_eligible'] or c['performance_authorized'] or c['family_approved']):
            raise ValueError('Unknown count, gate or score promoted')
        if any(not r['reason'] or not r['evidence_references'] for r in c['criteria'].values()):raise ValueError('Unexplained score')
        expected_row=f"| {c['family']} | {total}/32 | {unknown} | {total}–{total+2*unknown} | Deferred |"
        if expected_row not in (DOCS/'phase4a_candidate_families.md').read_text(encoding='utf-8'):raise ValueError('Score table differs from canonical judgments')
    policy=json.loads((DOCS/'availability_policy_v003_proposed.json').read_bytes())
    if digest(policy)!='438d7bcf7d091f596009ba841e6dacbd960c18493c34ffec798d8c1aaf1dacbd' or policy['activation']!='NOT_ACTIVATED':
        raise ValueError('Historical policy changed')
    current=[ROOT/'README.md',ROOT/'AGENTS.md',ROOT/'docs/research_os.md',DOCS/'master_plan.md',
             DOCS/'phase4a_plan.md',DOCS/'phase4a_feasibility_framework.md',DOCS/'phase4a_candidate_families.md']
    broken=[]
    for path in current:
        text=path.read_text(encoding='utf-8')
        if '@@' in text:raise ValueError('Unrendered public documentation')
        for target in re.findall(r'\]\(([^\s)]+)\)',text):
            if target.startswith(('http:','https:','#','app:')):continue
            local=target.split('#',1)[0]
            if local and not (path.parent/local).exists():broken.append((str(path.relative_to(ROOT)),target))
    if broken:raise ValueError('Broken local links: '+str(broken))
    master=(DOCS/'master_plan.md').read_text(encoding='utf-8')
    if '| 4A | Separately authorized source acquisition, EXP005 freeze' in master:raise ValueError('Obsolete current milestone')
    return {'documentation':'PASS','families':3,'criteria_per_family':16,'broken_links':0,'performance':False,'acquisition':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    if not parser.parse_args().check:parser.error('Only --check is supported')
    print(check())
