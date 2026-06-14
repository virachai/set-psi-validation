def derive_actual_regime(ato_price, atc_price, volatility_index, threshold_mean):
    """
    Derives actual regime based on the logic defined in
    docs/research_reports/001-actual-regime-derivation-logic-v01.md
    """
    return_pct = (atc_price - ato_price) / ato_price

    if return_pct > 0.005 and volatility_index < threshold_mean:
        return "Bullish"
    elif return_pct < -0.02 and volatility_index > (threshold_mean * 2):
        return "Crisis"
    elif return_pct < -0.005 and volatility_index > threshold_mean:
        return "Risk-Off"
    elif return_pct < -0.005 and volatility_index < threshold_mean:
        return "Bearish"
    elif abs(return_pct) <= 0.005 and volatility_index < threshold_mean:
        return "Sideways"
    else:
        return "Unclassified"


def compare_regimes(predicted, actual):
    """
    Compares predicted regime with actual regime.
    """
    return "Match" if predicted == actual else "Mismatch"


def main():
    # Example logic execution
    # In a real scenario, this would load from a JSON file
    sample_data = {
        "ato_price": 100.0,
        "atc_price": 101.0,
        "volatility_index": 0.01,
        "threshold_mean": 0.02,
        "predicted_regime": "Bullish",
    }

    actual = derive_actual_regime(
        sample_data["ato_price"],
        sample_data["atc_price"],
        sample_data["volatility_index"],
        sample_data["threshold_mean"],
    )

    comparison = compare_regimes(sample_data["predicted_regime"], actual)

    print(f"Predicted: {sample_data['predicted_regime']}")
    print(f"Actual: {actual}")
    print(f"Result: {comparison}")


if __name__ == "__main__":
    main()
