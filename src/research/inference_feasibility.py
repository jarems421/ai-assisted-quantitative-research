"""Pre-acquisition inference resolution and declared-power guards; no returns."""
import math


def inference_design_gate(design):
    alpha=design['alpha']; family=design['family_size']; units=design['sample_units']; minimum=design['minimum_units']
    if (type(alpha) not in (int,float) or not 0<alpha<1 or type(family) is not int or family<1
            or type(units) is not int or type(minimum) is not int or minimum<1 or units<1):
        raise ValueError('Invalid predeclared inference design')
    method=design['method']
    if method=='exact_sign':
        groups=design['clusters']
        if type(groups) is not int or not 1<=groups<=1024: raise ValueError('Invalid sign resolution')
        min_p=2.**(-groups)
    elif method=='bootstrap':
        draws=design['draws']
        if type(draws) is not int or draws<1: raise ValueError('Invalid bootstrap resolution')
        min_p=1/(draws+1)
    elif method=='asymptotic': min_p=0.
    else: raise ValueError('Undeclared inference resolution class')
    threshold=alpha/family
    lower=design.get('power_lower'); required=design['power_required']
    if not 0<required<=1 or lower is not None and (not math.isfinite(lower) or not 0<=lower<=1):
        raise ValueError('Invalid power evidence')
    resolution=min_p<=threshold and units>=minimum
    power=lower is not None and lower>=required
    return {'INFERENCE_RESOLUTION_FEASIBLE':resolution,'POWER_GATE_FEASIBLE':power,
            'minimum_p':min_p,'first_holm_threshold':threshold,'sample_units':units,
            'power_lower':lower,'status':'FEASIBLE_DESIGN_NOT_STATISTICAL_CERTIFICATE' if resolution and power else 'BLOCKED'}


def require_inference_design(design):
    result=inference_design_gate(design)
    if result['status']=='BLOCKED': raise ValueError('Inferential decision rule impossible or declared power unsupported')
    return result
