"""
Stress Test for PSI Regime Derivation
Generates synthetic market data to verify regime classification logic.
"""

from capture_market import derive_actual_regime


def run_stress_test():
    test_cases = [
        {"name": "Bullish Scenario", "ato": 1000, "atc": 1010, "vol": 0.002, "expected": "Bullish"},
        {"name": "Crisis Scenario", "ato": 1000, "atc": 950, "vol": 0.04, "expected": "Crisis"},
        {"name": "Risk-Off Scenario", "ato": 1000, "atc": 990, "vol": 0.03, "expected": "Risk-Off"},
        {"name": "Bearish Scenario", "ato": 1000, "atc": 990, "vol": 0.002, "expected": "Bearish"},
        {
            "name": "Sideways Scenario",
            "ato": 1000,
            "atc": 1000,
            "vol": 0.001,
            "expected": "Sideways",
        },
    ]

    print(f"{'Test Case':<20} | {'Expected':<10} | {'Actual':<10} | {'Result'}")
    print("-" * 60)

    for case in test_cases:
        actual = derive_actual_regime(case["ato"], case["atc"], case["vol"], 0.02)
        status = "PASS" if actual == case["expected"] else "FAIL"
        print(f"{case['name']:<20} | {case['expected']:<10} | {actual:<10} | {status}")


if __name__ == "__main__":
    run_stress_test()
