"""Frozen, synthetic-only exact cluster-sign comparison; no real performance input."""
from itertools import product
import math
import numpy as np
from src.research.phase3c.inference import aligned, synthetic_windows
from src.research.analysis import holm
from src.research.spec import digest

METHODS=('annual_cluster_sign','funding_window_sign')
EFFECTS=('base','double_cost','delay1','delay5')


def clusters(windows, method):
    if method not in METHODS: raise ValueError('Method outside frozen family')
    parts=aligned(windows)
    if any(len(p)!=756 for p in parts): raise ValueError('Frozen two-window coverage required')
    width=252 if method==METHODS[0] else 756
    return np.concatenate([p.reshape(-1,width).mean(axis=1) for p in parts])


def signs(n): return np.array(list(product((-1.,1.),repeat=n)))


def exact_p(values, *, location=0., two_sided=False):
    values=np.asarray(values,dtype=float)-location
    if values.ndim!=1 or len(values) not in (2,6) or not np.isfinite(values).all(): raise ValueError('Invalid cluster evidence')
    observed=values.sum(); draws=signs(len(values))@values
    if two_sided: observed=abs(observed); draws=np.abs(draws)
    # Include ties with a fixed roundoff bound; no Monte Carlo zero p-values.
    return float(np.count_nonzero(draws>=observed-1e-14)/len(draws))


def confidence_set(values, alpha=.05):
    """Exact inversion for a common additive cluster location, not arbitrary mean."""
    values=np.asarray(values,dtype=float); n=len(values); matrix=signs(n)
    roots=[]
    for row in matrix:
        a=float(row@values); b=float(row.sum()); total=float(values.sum())
        if b!=n: roots.append((a-total)/(b-n))
        if b!=-n: roots.append((a+total)/(b+n))
    points=sorted(set(roots)); edges=[-math.inf,*points,math.inf]; accepted=[]
    for lo,hi in zip(edges,edges[1:]):
        probe=(lo+hi)/2 if math.isfinite(lo) and math.isfinite(hi) else (hi-max(1,abs(hi)) if not math.isfinite(lo) else lo+max(1,abs(lo)))
        if exact_p(values,location=probe,two_sided=True)>alpha:
            accepted.append({'lower':None if not math.isfinite(lo) else lo,'upper':None if not math.isfinite(hi) else hi})
    isolated=[x for x in points if exact_p(values,location=x,two_sided=True)>alpha]
    return {'accepted_intervals':accepted,'accepted_boundary_points':isolated,
            'interpretation':'Common additive location under independent sign-invariant cluster errors only'}


def test(windows,method):
    values=clusters(windows,method)
    return {'method':method,'one_sided_p':exact_p(values),'cluster_count':len(values),
            'minimum_p':1/2**len(values),'annualized_paired_mean':float(values.mean()*252),
            'confidence_set_95':confidence_set(values),'status':'SYNTHETIC_DIAGNOSTIC_NOT_CERTIFIED'}


def wilson(hits,total):
    rate=hits/total; z=1.96; denominator=1+z*z/total
    center=(rate+z*z/(2*total))/denominator
    half=z*math.sqrt(rate*(1-rate)/total+z*z/(4*total*total))/denominator
    return [center-half,center+half]


def world(rng,name):
    x=rng.normal(0,.01,1512)
    if name in ('ar1_null','persistent_null'):
        rho=.5 if name=='ar1_null' else .98
        for i in range(1,len(x)): x[i]=rho*x[i-1]+x[i]
    elif name=='annual_shock_null': x+=np.repeat(rng.normal(0,.004,6),252)
    elif name=='overlap_null': x=np.convolve(x,np.ones(21)/21,mode='full')[:1512]
    elif name=='window_shift_null': x+=np.r_[np.full(756,-.003),np.full(756,.003)]
    elif name=='heteroskedastic_null': x[756:]*=3
    elif name=='skewed_null': x=(rng.exponential(1,1512)-1)*.01
    elif name=='positive': x+=.001
    elif name=='negative': x-=.001
    elif name!='iid_null': raise ValueError('World outside frozen protocol')
    return x


def calibrate(protocol):
    if (protocol['candidate_order']!=list(METHODS) or protocol['seed']!=3003002
            or protocol['replicates_per_world']!=400): raise ValueError('Protocol changed')
    rng=np.random.default_rng(protocol['seed']); reps=protocol['replicates_per_world']; rows=[]
    for name in protocol['worlds']:
        counts={m:{'raw':0,'coverage':0,'family':{j:0 for j in protocol['joint_dependence']}} for m in METHODS}
        location=.001 if name=='positive' else -.001 if name=='negative' else 0.
        for _ in range(reps):
            vectors=[world(rng,name) for _ in range(4)]
            joint={'fully_correlated':[vectors[0]]*4,'independent':vectors,
                   'mixed_common_shock':[.5*vectors[0]+.5*v for v in vectors]}
            for method in METHODS:
                c=clusters(synthetic_windows(vectors[0]),method); hit=counts[method]
                hit['raw']+=exact_p(c)<=.05
                hit['coverage']+=exact_p(c,location=location,two_sided=True)>.05
                for structure,series in joint.items():
                    p={k:exact_p(clusters(synthetic_windows(x),method)) for k,x in zip(EFFECTS,series)}
                    hit['family'][structure]+=any(r['reject'] for r in holm(p,alpha=.05).values())
        for method in METHODS:
            hit=counts[method]; family={j:{'fraction':v/reps,'wilson95':wilson(v,reps)} for j,v in hit['family'].items()}
            rows.append({'world':name,'method':method,'replicates':reps,'raw_rejection':hit['raw']/reps,
                         'raw_wilson95':wilson(hit['raw'],reps),'family_rejection':family,
                         'location_coverage':hit['coverage']/reps,'coverage_wilson95':wilson(hit['coverage'],reps),
                         'coverage_assumptions':'Heterogeneous shift, skew, and cross-cluster dependence may violate inversion assumptions; retain as diagnostic'})
    return {'version':'phase3d_calibration_results_v001','protocol_sha256':digest(protocol),'rows':rows,
            'selected_method':None,'verdict':'BLOCKED',
            'reason':'Neither candidate can reject any of the four-effect Holm family at six/two clusters; power criterion structurally impossible. Real cluster independence/symmetry also unestablished.',
            'all_candidates_retained':True,'real_performance_inputs':0}
