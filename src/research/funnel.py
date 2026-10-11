"""The predeclared cheap-to-expensive research plan; no automatic escalation."""
TIERS = (
    (1, 'DRAFT', 'hypothesis/data audit', 'No performance search; establish point-in-time evidence'),
    (2, 'DEVELOPMENT', 'cheap screen', 'Prefer daily non-options; events only when the frozen hypothesis requires them'),
    (3, 'DEVELOPMENT', 'parameter stability', 'Bounded declared sweep; neighbours, plateaus and rank stability, not maximum return'),
    (4, 'VALIDATION', 'frozen evaluation', 'Candidate and explicit benchmarks; no retuning'),
    (5, 'WALK_FORWARD', 'chronological folds', 'Training/inner evaluation inside Development; never reuse the historical lockbox'),
    (6, 'ROBUSTNESS', 'stress gauntlet', 'Cost, delay, parameters, universe, cadence, regimes and paired resampling'),
    (7, 'TEST_AUTHORIZED', 'historical lockbox', 'Owner interactive authorization and complete reviewed evidence required'),
    (8, 'PAPER_AUTHORIZED', 'forward paper', 'Separate authorization; no live path'),
)


def plan(spec):
    return [{'tier':n,'stage':stage,'purpose':purpose,'policy':policy} for n,stage,purpose,policy in TIERS]
