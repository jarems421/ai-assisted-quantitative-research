"""Frozen monthly paired inference comparison; synthetic inputs only."""
import math
import numpy as np
from src.research.analysis import holm
from src.research.phase3d.inference import wilson
from src.research.spec import digest

METHODS=('monthly_hac12','monthly_studentized_circular12')


def hac_se(series):
    """Intercept HAC12, pooled mean, no covariance across funding boundaries."""
    x=np.asarray(series,dtype=float)
    if x.shape[-2:]!=(2,36) or not np.isfinite(x).all(): raise ValueError('Two complete36-month windows required')
    n=72; centered=x-x.mean(axis=(-2,-1),keepdims=True)
    meat=(centered**2).sum(axis=(-2,-1))
    for lag in range(1,13):
        meat += 2*(1-lag/13)*(centered[...,lag:]*centered[...,:-lag]).sum(axis=(-2,-1))
    variance=meat/(n*(n-1))
    return np.sqrt(np.maximum(variance,0))


def evaluate(values, *, draws=1999,seed=3003003):
    x=np.asarray(values,dtype=float)
    if x.shape!=(4,2,36) or not np.isfinite(x).all(): raise ValueError('Four paired effects with two fixed windows required')
    if draws!=1999: raise ValueError('Frozen bootstrap draws changed')
    means=x.mean(axis=(-2,-1)); se=hac_se(x)
    if np.any(se<=0): raise ValueError('Zero/invalid standard error')
    observed=means/se
    normal_p=[.5*math.erfc(float(t)/math.sqrt(2)) for t in observed]
    rng=np.random.default_rng(seed); null=x-means[:,None,None]
    # One index tape for all effect pairs preserves joint dependence.
    starts=rng.integers(0,36,size=(draws,2,3))
    indices=((starts[...,None]+np.arange(12))%36).reshape(draws,2,36)
    sampled=np.stack([null[:,window,:][:,indices[:,window,:]] for window in (0,1)],axis=2)
    # [effect, draw, funding window, month]
    boot_mean=sampled.mean(axis=(-2,-1)); boot_se=hac_se(sampled)
    valid=np.isfinite(boot_se)&(boot_se>0)
    if not valid.all(): raise ValueError('Invalid studentized resample; no replication deletion')
    boot_t=boot_mean/boot_se
    bootstrap_p=(1+(boot_t>=observed[:,None]).sum(axis=1))/(draws+1)
    q=np.quantile(boot_t,[.025,.975],axis=1)
    output={}
    for method,p,ci in [(METHODS[0],normal_p,np.stack([means-1.959963984540054*se,means+1.959963984540054*se],axis=1)),
                         (METHODS[1],bootstrap_p,np.stack([means-q[1]*se,means-q[0]*se],axis=1))]:
        output[method]={'p':list(map(float,p)),'ci':ci.tolist(),'mean':means.tolist(),'se':se.tolist(),
                        'effective_n_diagnostic':np.minimum(72,np.var(x,axis=(-2,-1),ddof=1)/(se**2)).tolist()}
    return output


def synthetic(rng,name):
    daily=rng.normal(0,.01,size=(4,2,756))
    if name in ('ar05','persistent095'):
        rho=.5 if name=='ar05' else .95
        for j in range(1,756): daily[:,:,j]+=rho*daily[:,:,j-1]
    elif name=='annual_common': daily+=np.repeat(rng.normal(0,.004,(4,2,3)),252,axis=2)
    elif name=='heteroskedastic': daily[:,1,:]*=3
    elif name=='skewed': daily=(rng.exponential(1,(4,2,756))-1)*.01
    elif name=='heavy_tail': daily=rng.standard_t(3,(4,2,756))*.01/math.sqrt(3)
    elif name=='overlap':
        daily=np.apply_along_axis(lambda x:np.convolve(x,np.ones(21)/21,mode='full')[:756],2,daily)
    elif name=='rebalance_shock': daily+=np.repeat(rng.normal(0,.004,(4,2,36)),21,axis=2)
    elif name=='regime_shift': daily[:,0,:]-=.003; daily[:,1,:]+=.003
    elif not name.startswith(('positive','negative')) and name!='iid': raise ValueError('Undeclared world')
    effect=0.
    if name.startswith('positive'): effect=int(name[-2:])/100/252
    elif name=='negative10': effect=-.10/252
    daily+=effect
    return daily.reshape(4,2,36,21).mean(axis=3),effect


def calibrate(protocol):
    if protocol['candidate_order']!=list(METHODS) or protocol['seed']!=3003003 or protocol['replicates']!=200:
        raise ValueError('Frozen candidate family changed')
    rng=np.random.default_rng(protocol['seed']); rows=[]
    for world in protocol['worlds']:
        counts={(m,j):{'raw':0,'family':0,'primary':0,'covered':0,'failures':0,'width':[],'neff':[]} for m in METHODS for j in protocol['joint_structures']}
        for rep in range(protocol['replicates']):
            independent,true=synthetic(rng,world)
            structures={'independent':independent,'fully_correlated':np.repeat(independent[:1],4,axis=0),
                        'mixed_common':.5*independent+.5*independent[:1]}
            for structure,values in structures.items():
                try: tested=evaluate(values,seed=protocol['seed']+rep)
                except ValueError: tested={}
                for method in METHODS:
                    row=counts[(method,structure)]; result=tested.get(method)
                    if result is None: row['failures']+=1; continue
                    family=holm(dict(zip(protocol['effects'],result['p'])),alpha=.05)
                    row['raw']+=result['p'][0]<=.05; row['family']+=any(r['reject'] for r in family.values()); row['primary']+=family['base']['reject']
                    low,high=result['ci'][0]; row['covered']+=low<=true<=high
                    row['width'].append((high-low)*252); row['neff'].append(result['effective_n_diagnostic'][0])
        for (method,structure),r in counts.items():
            n=protocol['replicates']
            rows.append({'world':world,'method':method,'structure':structure,'replicates':n,
                **{k:{'fraction':r[k]/n,'wilson95':wilson(r[k],n)} for k in ('raw','family','primary','covered')},
                'failed_replications':r['failures'],'median_annual_interval_width':float(np.median(r['width'])) if r['width'] else None,
                'median_effective_months_diagnostic':float(np.median(r['neff'])) if r['neff'] else None})
        print('Synthetic world complete:',world,flush=True)
    verdicts={}
    for method in METHODS:
        relevant=[r for r in rows if r['method']==method]
        nulls=[r for r in relevant if not r['world'].startswith(('positive','negative'))]
        coverage=[r for r in relevant if r['world']!='regime_shift']
        size=all(max(r['raw']['wilson95'][1],r['family']['wilson95'][1])<=.10 for r in nulls)
        cover=all(r['covered']['wilson95'][0]>=.90 for r in coverage)
        power10=all(r['primary']['wilson95'][0]>=.50 for r in relevant if r['world']=='positive10')
        power02=all(r['primary']['wilson95'][0]>=.50 for r in relevant if r['world']=='positive02')
        verdicts[method]={'size_gate':size,'coverage_gate':cover,'power10_screen':power10,'power_at_materiality':power02,
                          'statistical_assumptions_real':'UNESTABLISHED','selected':False}
    return {'version':'monthly_calibration_v002','protocol_sha256':digest(protocol),'rows':rows,'candidate_verdicts':verdicts,
            'selected_method':None,'real_strategy_inputs':0,
            'limitations':'Finite sample synthetic evidence, not certification of a real population or weak-dependence assumptions; failures retained'}
