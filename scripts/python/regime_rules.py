"""Canonical Market Regime Rules & Derivation Logic for SET PSI Validation.

Defines the authoritative rules for classifying market regimes from intraday
price and volatility metrics, ensuring consistent definitions across the Truth Layer.

Governance: Compliant with RFC 014 (Lean Architecture & Data Truth Layer Enforcement).
"""

VALID_REGIMES = [
    "Bullish",
    "Bearish",
    "Sideways",
    "Risk-Off",
    "Crisis",
    "Unclassified",
]

# Regime derivation thresholds (mirrored across validation & capture layers)
BULLISH_MIN_RETURN = 0.005
CRISIS_RETURN = -0.02
DOWN_MOVE_MAX_RETURN = -0.005
SIDEWAYS_BAND = 0.005
DEFAULT_THRESHOLD_MEAN = 0.02


def derive_actual_regime(
    ato_price: float,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float = DEFAULT_THRESHOLD_MEAN,
) -> str:
    """Derive the actual market regime based on intraday return and volatility.

    Logic defined in docs/02_research_reports/001-actual-regime-derivation-logic-v01.md
    and docs/010-regime-taxonomy-v01.json.
    """
    if ato_price <= 0:
        return "Unclassified"

    return_pct = (atc_price - ato_price) / ato_price

    if return_pct > BULLISH_MIN_RETURN and volatility_index < threshold_mean:
        return "Bullish"
    if return_pct < CRISIS_RETURN and volatility_index >= (threshold_mean * 2):
        return "Crisis"
    if return_pct < DOWN_MOVE_MAX_RETURN:
        return "Risk-Off" if volatility_index > threshold_mean else "Bearish"
    if abs(return_pct) <= SIDEWAYS_BAND and volatility_index < threshold_mean:
        return "Sideways"
    return "Unclassified"


def compare_regimes(predicted: str, actual: str) -> bool:
    """Return True if the prediction matches the actual outcome.

    "Unclassified" never counts as a correct match, even against an
    "Unclassified" actual regime — it means one or both sides failed to
    produce a real classification, not that ambiguity was correctly forecast.
    """
    if predicted == "Unclassified" or actual == "Unclassified":
        return False
    return predicted == actual


def compute_deviation_score(predicted: str, actual: str) -> float:
    """Compute a deviation score between predicted and actual regimes.

    0.0 = perfect match.
    1.0 = mismatch (including any "Unclassified" involved — see compare_regimes).
    """
    return 0.0 if compare_regimes(predicted, actual) else 1.0
