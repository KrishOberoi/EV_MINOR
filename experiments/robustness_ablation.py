"""Repeat balancing comparisons across scenarios and electrochemical-score ablations.

This experiment tests whether the electrochemical score is robust to pack
heterogeneity and whether its gradient/overpotential terms change outcomes.
It remains a control-oriented study because the underlying balancing layer is
not yet a closed-loop PyBaMM PDE solve.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from balancing_comparison import (
    CELL_CONFIG,
    PLOTS,
    ROOT,
    build_reference_pack,
    calculate_metrics,
    run_controller,
)

CSV = ROOT / "results" / "csv"
CSV.mkdir(parents=True, exist_ok=True)

SCENARIOS = {
    "baseline": CELL_CONFIG,
    "soc_shift": [
        {**config, "initial_soc": soc}
        for config, soc in zip(CELL_CONFIG, [0.84, 0.78, 0.70, 0.76])
    ],
    "capacity_resistance": [
        {**config, "capacity_ah": capacity, "contact_resistance_ohm": resistance}
        for config, capacity, resistance in zip(
            CELL_CONFIG,
            [5.00, 4.75, 4.45, 5.05],
            [0.008, 0.018, 0.030, 0.011],
        )
    ],
}

CONTROLLER_SPECS = {
    "Uncontrolled": (0.0, 0.0),
    "SOC": (0.0, 0.0),
    "Electrochemical": (0.2, 0.1),
    "Electrochemical_no_gradient": (0.0, 0.1),
    "Electrochemical_no_overpotential": (0.2, 0.0),
    "Electrochemical_SOC_only": (0.0, 0.0),
}


def main() -> None:
    rows = []
    for scenario, cell_config in SCENARIOS.items():
        reference = build_reference_pack(cell_config)
        for controller, (gradient_weight, eta_weight) in CONTROLLER_SPECS.items():
            if controller == "Electrochemical_SOC_only":
                controller_name = "Electrochemical"
            else:
                controller_name = controller
            result = run_controller(
                reference,
                controller_name,
                cell_config=cell_config,
                gradient_weight=gradient_weight,
                eta_weight=eta_weight,
            )
            metric = calculate_metrics(result)
            metric.update(
                {
                    "scenario": scenario,
                    "gradient_weight": gradient_weight,
                    "eta_weight": eta_weight,
                    "controller_label": controller,
                }
            )
            rows.append(metric)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(CSV / "balancing_robustness_ablation_metrics.csv", index=False)

    # Plot final SOC spread and peak stress separately from the primary result.
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    metrics.pivot(index="scenario", columns="controller_label", values="final_soc_spread_percentage_points").plot(
        kind="bar", ax=axes[0]
    )
    axes[0].set_ylabel("Final SOC spread [percentage points]")
    axes[0].set_title("Robustness and score ablation")
    metrics.pivot(index="scenario", columns="controller_label", values="peak_electrochemical_stress_index").plot(
        kind="bar", ax=axes[1]
    )
    axes[1].set_ylabel("Peak electrochemical stress index")
    axes[1].set_title("Stress response")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(PLOTS / "balancing_robustness_ablation.png", dpi=180)
    plt.close(fig)

    print("Balancing robustness and ablation experiment completed.")
    for scenario, data in metrics.groupby("scenario"):
        baseline = data.loc[data.controller_label == "Uncontrolled", "final_soc_spread_percentage_points"].iloc[0]
        full = data.loc[data.controller_label == "Electrochemical", "final_soc_spread_percentage_points"].iloc[0]
        no_gradient = data.loc[data.controller_label == "Electrochemical_no_gradient", "final_soc_spread_percentage_points"].iloc[0]
        no_eta = data.loc[data.controller_label == "Electrochemical_no_overpotential", "final_soc_spread_percentage_points"].iloc[0]
        print(
            f"{scenario}: uncontrolled={baseline:.3f} pp, full={full:.3f} pp, "
            f"no-gradient={no_gradient:.3f} pp, no-overpotential={no_eta:.3f} pp"
        )
    print(f"Saved: {(CSV / 'balancing_robustness_ablation_metrics.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'balancing_robustness_ablation.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
