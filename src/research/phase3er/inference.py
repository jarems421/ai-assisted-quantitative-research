"""Frozen v003 synthetic comparison; no real return loader or execution transport."""
from functools import lru_cache
from itertools import product
import math
import numpy as np
from src.research.phase3d.inference import wilson
from src.research.spec import digest

METHODS=('session_weighted_group_student','symmetric_group_sign')


def student_survival(t,df):
    if df<1 or not math.isfinite(t):raise ValueError('Invalid Student reference')
    theta=math.atan(t/math.sqrt(df));c=math.gamma((df+1)/2)/(math.sqrt(math.pi)*math.gamma(df/2))
    integrals=[theta,math.sin(theta)]
    for n in range(2,df):integrals.append(math.sin(theta)*math.cos(theta)**(n-1)/n+(n-1)*integrals[n-2]/n)
    return min(1.,max(0.,.5-c*integrals[df-1]))


@lru_cache(None)
def critical(df):
    lo,hi=0.,1000.
    for _ in range(70):
        mid=(lo+hi)/2
        if student_survival(mid,df)>.025:lo=mid
        else:hi=mid
    return (lo+hi)/2


@lru_cache(None)
def sign_matrix(groups):return np.asarray(list(product((-1.,1.),repeat=groups)))


def evaluate(annual_means,counts):
    """[replication,effect,group] or [effect,group]; output target is annual fraction."""
    x=np.asarray(annual_means,dtype=float);n=np.asarray(counts,dtype=float);g=len(n)
    if x.shape[-2:]!=(4,g) or not 2<=g<=8 or not np.isfinite(x).all() or not np.isfinite(n).all() or np.any(n<=0):raise ValueError('Complete annual groups required')
    mu=(x*n).sum(axis=-1)/n.sum();sse=((x-mu[...,None])**2*n).sum(axis=-1)
    se=np.sqrt(sse/((g-1)*n.sum()))
    valid=np.isfinite(se)&(se>0)
    safe=np.where(valid,se,1.);t=mu/safe
    p=np.asarray([student_survival(float(v),g-1) for v in t.flat]).reshape(t.shape)
    p=np.where(valid,p,1.);width=critical(g-1)*safe
    lo=np.where(valid,mu-width,-np.inf);hi=np.where(valid,mu+width,np.inf)
    weighted=x*n/n.sum();draws=np.einsum('sg,...eg->...es',sign_matrix(g),weighted)
    sign_p=(draws>=mu[...,None]-1e-14).mean(axis=-1)
    # All compared geometries have <=5 groups: exact95 two-sided inversion unbounded.
    if g>5:raise ValueError('Frozen comparison supports at most five confirmation groups')
    return {METHODS[0]:{'mean':mu,'p':p,'low':lo,'high':hi,'valid':valid},
            METHODS[1]:{'mean':mu,'p':sign_p,'low':np.full(mu.shape,-np.inf),'high':np.full(mu.shape,np.inf),'valid':np.ones(mu.shape,dtype=bool)}}


def synthetic(rng,geometry,world,noise,structure,reps):
    counts=[g['sessions'] for w in geometry['confirmation_geometry'] for g in w['annual_groups']];total=sum(counts)
    daily=rng.normal(size=(reps,4,total))
    if structure=='fully_correlated':daily=np.repeat(daily[:,:1,:],4,axis=1)
    elif structure=='mixed_common':daily=(daily+rng.normal(size=(reps,1,total)))/math.sqrt(2)
    elif structure!='independent':raise ValueError('Undeclared effect dependence')
    scale=noise/math.sqrt(252)
    if world in ('ar05','persistent098'):
        rho=.5 if world=='ar05' else .98
        daily*=math.sqrt((1-rho)/(1+rho))
        for j in range(1,total):daily[:,:,j]+=rho*daily[:,:,j-1]
    elif world=='heavy_tail':
        independent=rng.standard_t(3,size=(reps,4,total))/math.sqrt(3)
        if structure=='fully_correlated':independent=np.repeat(independent[:,:1,:],4,axis=1)
        elif structure=='mixed_common':independent=(independent+rng.standard_t(3,size=(reps,1,total))/math.sqrt(3))/math.sqrt(2)
        daily=independent
    elif world=='overlap21':
        cumulative=np.cumsum(daily,axis=2);daily=(cumulative-np.concatenate([np.zeros((reps,4,21)),cumulative[:,:,:-21]],axis=2))/math.sqrt(21)
    elif world=='skewed':
        # Squaring joint normals preserves effect dependence; centering preserves zero expectation.
        daily=(daily**2-1)/math.sqrt(2)
    daily*=scale
    cursor=0;means=[]
    for index,count in enumerate(counts):
        portion=daily[:,:,cursor:cursor+count];mean=252*portion.mean(axis=2)
        if world in ('annual_reporting_scaled','annual_reporting_constant'):
            z=rng.normal(size=(reps,4))
            if structure=='fully_correlated':z=np.repeat(z[:,:1],4,axis=1)
            elif structure=='mixed_common':z=(z+rng.normal(size=(reps,1)))/math.sqrt(2)
            amplitude=noise*(math.sqrt(252/count) if world.endswith('scaled') else 1)
            mean=(mean+z*amplitude)/math.sqrt(2)
        elif world=='rebalance_gaussian':
            # Independent calendar-month Gaussian shocks; annual weighted variance proportional1/n.
            z=rng.normal(size=(reps,4))
            if structure=='fully_correlated':z=np.repeat(z[:,:1],4,axis=1)
            elif structure=='mixed_common':z=(z+rng.normal(size=(reps,1)))/math.sqrt(2)
            mean=(mean+z*noise*math.sqrt(252/count))/math.sqrt(2)
        elif world=='heterogeneous_years':mean*=([.5,1,2,.75,1.5][index])
        means.append(mean);cursor+=count
    values=np.stack(means,axis=2)
    if world=='common_crossyear':values+=rng.normal(size=(reps,1,1))*noise
    elif world=='regime_shift':
        shift=np.linspace(-noise,noise,len(counts));shift-=np.average(shift,weights=counts);values+=shift
    allowed={'iid','ar05','persistent098','annual_reporting_scaled','annual_reporting_constant','rebalance_gaussian','heterogeneous_years','skewed','heavy_tail','overlap21','regime_shift','common_crossyear'}
    if world not in allowed:raise ValueError('Undeclared synthetic world')
    return values,counts


def summarize(result,effect,offsets,reps):
    mu=result['mean'];lo=result['low'][:,0];hi=result['high'][:,0];p=result['p'][:,0]
    rejection=p<=.05
    support=rejection&(lo>0)&(mu[:,0]>=.02)&np.all(mu[:,1:]>0,axis=1)&np.all(result['valid'],axis=1)
    covered=(lo<=effect)&(hi>=effect)&result['valid'][:,0]
    finite=np.isfinite(lo)&np.isfinite(hi)
    def rate(hit):
        count=int(np.count_nonzero(hit));return {'hits':count,'total':reps,'fraction':count/reps,'wilson95':wilson(count,reps)}
    return {'primary_rejection':rate(rejection),'family_rejection':rate(rejection),'full_support':rate(support),
            'coverage':rate(covered),'finite_interval_fraction':float(np.mean(finite)),
            'mean_interval_width':float(np.mean(hi-lo)) if finite.all() else None,
            'unbounded_interval_replications':int(np.count_nonzero(~finite)),
            'failed_replications':int(np.count_nonzero(~np.all(result['valid'],axis=1)))}


def calibrate(protocol,geometries):
    if protocol['seed']!=3003004 or protocol['replicates']!=600 or protocol['methods']!=list(METHODS):raise ValueError('Frozen protocol changed')
    rng=np.random.default_rng(protocol['seed']);rows=[];power=[];reps=protocol['replicates'];offsets=np.asarray(protocol['synthetic_stress_offsets'])
    for geometry in geometries:
        for world in protocol['worlds']:
            for structure in protocol['joint_structures']:
                values,counts=synthetic(rng,geometry,world,.025,structure,reps)
                for effect in [0.,.02,.05,.10,.15,.20,-.05]:
                    tested=evaluate(values+effect-offsets[None,:,None],counts)
                    for method,result in tested.items():
                        rows.append(dict(summarize(result,effect,offsets,reps),geometry=geometry['id'],world=world,structure=structure,method=method,
                                         annual_effect=effect,annual_tracking_error=.025,role='CERTIFICATION' if world in protocol['student_certification_worlds' if method==METHODS[0] else 'sign_certification_worlds'] else 'STRESS_DIAGNOSTIC'))
            print('Synthetic calibration',geometry['id'],world,'complete',flush=True)
        for noise in protocol['noise_sensitivity']:
            for structure in protocol['joint_structures']:
                values,counts=synthetic(rng,geometry,'iid',noise,structure,reps)
                for effect in protocol['positive_effect_grid']:
                    for method,result in evaluate(values+effect-offsets[None,:,None],counts).items():
                        power.append(dict(summarize(result,effect,offsets,reps),geometry=geometry['id'],method=method,structure=structure,
                                          annual_tracking_error=noise,annual_effect=effect))
    verdicts=[]
    for geometry in geometries:
        for method in METHODS:
            subset=[r for r in rows if r['geometry']==geometry['id'] and r['method']==method and r['role']=='CERTIFICATION']
            nulls=[r for r in subset if r['annual_effect']==0]
            useful=[r for r in subset if r['annual_effect']==.05]
            verdicts.append({'geometry':geometry['id'],'method':method,
                'null_gate':all(r['primary_rejection']['wilson95'][1]<=.10 for r in nulls),
                'coverage_gate':all(r['coverage']['wilson95'][0]>=.90 for r in subset),
                'bounded_interval':all(r['finite_interval_fraction']==1 for r in subset),
                'useful_power':all(r['full_support']['wilson95'][0]>=.80 for r in useful),
                'real_assumptions':'UNESTABLISHED','real_certification':False})
    return {'version':'phase3er_calibration_v003','protocol_sha256':digest(protocol),'rows':rows,'power_sensitivity':power,'candidate_verdicts':verdicts,
            'real_performance_inputs':0,'replicates_per_world':reps,'no_methods_or_worlds_omitted':True}
