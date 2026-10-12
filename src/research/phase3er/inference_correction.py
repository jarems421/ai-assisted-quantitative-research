"""One analytical generator correction; all frozen inference choices unchanged."""
import math
from unittest.mock import patch
from . import inference as frozen

ORIGINAL_SYNTHETIC=frozen.synthetic


def synthetic(rng,geometry,world,noise,structure,reps):
    # Frozen AR innovation factor sqrt((1-rho)/(1+rho)) did not preserve
    # the declared long-run noise: LRV=innovation_variance/(1-rho)^2.
    # Multiplication by sqrt(1-rho^2) makes the total factor exactly1-rho.
    if world in ('ar05','persistent098'):
        rho=.5 if world=='ar05' else .98
        noise*=math.sqrt(1-rho*rho)
    return ORIGINAL_SYNTHETIC(rng,geometry,world,noise,structure,reps)


def calibrate(protocol,geometries):
    # Explicit single-worker generator substitution; on-disk frozen code and
    # original result remain immutable. Every estimator/gate and RNG draw is reused.
    with patch.object(frozen,'synthetic',synthetic):
        result=frozen.calibrate(protocol,geometries)
    return dict(result,implementation_correction='AR_LONG_RUN_NOISE_NORMALIZATION_001',
                correction_changes='Analytical innovation factor only; no methods, dates, seeds, scenarios or thresholds changed')
