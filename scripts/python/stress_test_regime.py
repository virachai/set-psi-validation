"""Stress test for the PSI regime derivation logic.

Generates synthetic market data to verify regime classification behavior.
"""

from capture_market import derive_actual_regime

DEFAULT_THRESHOLD_MEAN = 0.02


def run_stress_test() -> None:
    """Run the synthetic regime scenarios and print pass/fail per case."""
    test_cases = [
        ("Bullish Scenario", 1000, 1010, 0.002, "Bullish"),
        ("Crisis Scenario", 1000, 950, 0.04, "Crisis"),
        ("Risk-Off Scenario", 1000, 990, 0.03, "Risk-Off"),
        ("Bearish Scenario", 1000, 990, 0.002, "Bearish"),
        ("Sideways Scenario", 1000, 1000, 0.001, "Sideways"),
    ]

    print(f"{'Test Case':<20} | {'Expected':<10} | {'Actual':<10} | {'Result'}")
    print("-" * 60)

    for name, ato, atc, vol, expected in test_cases:
        actual = derive_actual_regime(ato, atc, vol, DEFAULT_THRESHOLD_MEAN)
        status = "PASS" if actual == expected else "FAIL"
        print(f"{name:<20} | {expected:<10} | {actual:<10} | {status}")


if __name__ == "__main__":
    run_stress_test()
