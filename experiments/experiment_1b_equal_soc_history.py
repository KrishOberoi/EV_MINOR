"""Controlled history experiment with equal initial SOC and equal net charge.

This experiment addresses the main limitation of Experiment 1: its strongest
voltage-matched pair also had a large SOC separation. Here both cells start at
60% SOC and receive the same total discharge, but the high- and low-rate pulses
are ordered differently.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_1_same_voltage import CSV, PLOTS, ROOT, simulate_cell


def find_controlled_match(cell_a: pd.DataFrame, cell_b: pd.DataFrame) -> pd.DataFrame:
    voltage_delta = cell_a.voltage_V.to_numpy()[:, None] - cell_b.voltage_V.to_numpy()[None, :]
    soc_delta = cell_a.soc.to_numpy()[:, None] - cell_b.soc.to_numpy()[None, :]
    eligible = (
        (np.abs(voltage_delta) <= 0.002)
        & (np.abs(soc_delta) <= 0.01)
        & (cell_a.time_s.to_numpy()[:, None] >= 120.0)
        & (cell_b.time_s.to_numpy()[None, :] >= 120.0)
    )
    indices = np.argwhere(eligible)
    if len(indices) == 0:
        raise RuntimeError("No pair met both the 2 mV voltage and 1 percentage-point SOC thresholds")

    scores = []
    for i, j in indices:
        positive_gradient_gap = abs(
            cell_a.positive_gradient_mol_m3.iloc[i]
            - cell_b.positive_gradient_mol_m3.iloc[j]
        )
        negative_gradient_gap = abs(
            cell_a.negative_gradient_mol_m3.iloc[i]
            - cell_b.negative_gradient_mol_m3.iloc[j]
        )
        overpotential_gap = abs(
            cell_a.total_overpotential_V.iloc[i]
            - cell_b.total_overpotential_V.iloc[j]
        )
        scores.append(
            positive_gradient_gap
            + negative_gradient_gap
            + 10000.0 * overpotential_gap
        )
    i, j = indices[int(np.argmax(scores))]

    return pd.DataFrame(
        [
            {
                "cell_a_index": int(i),
                "cell_b_index": int(j),
                "cell_a_time_s": cell_a.time_s.iloc[i],
                "cell_b_time_s": cell_b.time_s.iloc[j],
                "cell_a_voltage_V": cell_a.voltage_V.iloc[i],
                "cell_b_voltage_V": cell_b.voltage_V.iloc[j],
                "voltage_difference_mV": abs(cell_a.voltage_V.iloc[i] - cell_b.voltage_V.iloc[j]) * 1000,
                "cell_a_soc": cell_a.soc.iloc[i],
                "cell_b_soc": cell_b.soc.iloc[j],
                "soc_difference_percentage_points": abs(cell_a.soc.iloc[i] - cell_b.soc.iloc[j]) * 100,
                "cell_a_negative_gradient_mol_m3": cell_a.negative_gradient_mol_m3.iloc[i],
                "cell_b_negative_gradient_mol_m3": cell_b.negative_gradient_mol_m3.iloc[j],
                "cell_a_positive_gradient_mol_m3": cell_a.positive_gradient_mol_m3.iloc[i],
                "cell_b_positive_gradient_mol_m3": cell_b.positive_gradient_mol_m3.iloc[j],
                "cell_a_total_overpotential_V": cell_a.total_overpotential_V.iloc[i],
                "cell_b_total_overpotential_V": cell_b.total_overpotential_V.iloc[j],
            }
        ]
    )


def main() -> None:
    cell_a, _, _ = simulate_cell(
        "A",
        0.60,
        [
            "Discharge at 1C for 5 minutes",
            "Rest for 1 minute",
            "Discharge at 1C for 5 minutes",
            "Rest for 10 minutes",
            "Discharge at 0.5C for 10 minutes",
            "Rest for 5 minutes",
        ],
    )
    cell_b, _, _ = simulate_cell(
        "B",
        0.60,
        [
            "Discharge at 0.5C for 10 minutes",
            "Rest for 1 minute",
            "Discharge at 1C for 5 minutes",
            "Rest for 10 minutes",
            "Discharge at 0.5C for 10 minutes",
            "Rest for 5 minutes",
        ],
    )
    combined = pd.concat([cell_a, cell_b], ignore_index=True)
    combined.to_csv(CSV / "experiment_1b_equal_soc_histories.csv", index=False)
    match = find_controlled_match(cell_a, cell_b)
    match.to_csv(CSV / "experiment_1b_equal_soc_voltage_match.csv", index=False)

    row = match.iloc[0]
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    axes[0].plot(cell_a.time_s / 60, cell_a.voltage_V, label="Cell A", linewidth=2)
    axes[0].plot(cell_b.time_s / 60, cell_b.voltage_V, label="Cell B", linewidth=2)
    axes[0].scatter(
        [row.cell_a_time_s / 60, row.cell_b_time_s / 60],
        [row.cell_a_voltage_V, row.cell_b_voltage_V],
        color="black",
        zorder=5,
    )
    axes[0].set_ylabel("Voltage [V]")
    axes[0].set_title("Controlled history experiment: nearly equal SOC and voltage")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(cell_a.time_s / 60, cell_a.soc * 100, label="Cell A SOC")
    axes[1].plot(cell_b.time_s / 60, cell_b.soc * 100, label="Cell B SOC")
    axes[1].scatter(
        [row.cell_a_time_s / 60, row.cell_b_time_s / 60],
        [row.cell_a_soc * 100, row.cell_b_soc * 100],
        color="black",
        zorder=5,
    )
    axes[1].set_ylabel("SOC [%]")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    axes[2].plot(
        cell_a.time_s / 60,
        cell_a.positive_gradient_mol_m3,
        label="Cell A positive gradient",
    )
    axes[2].plot(
        cell_b.time_s / 60,
        cell_b.positive_gradient_mol_m3,
        label="Cell B positive gradient",
    )
    axes[2].scatter(
        [row.cell_a_time_s / 60, row.cell_b_time_s / 60],
        [row.cell_a_positive_gradient_mol_m3, row.cell_b_positive_gradient_mol_m3],
        color="black",
        zorder=5,
    )
    axes[2].set_xlabel("Local time [min]")
    axes[2].set_ylabel("Surface - average [mol m$^{-3}$]")
    axes[2].grid(alpha=0.25)
    axes[2].legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "experiment_1b_equal_soc_history.png", dpi=180)
    plt.close(fig)

    print("Controlled same-SOC experiment completed.")
    print(f"Voltage difference: {row.voltage_difference_mV:.3f} mV")
    print(f"SOC difference: {row.soc_difference_percentage_points:.3f} percentage points")
    print(
        "Positive gradient A/B: "
        f"{row.cell_a_positive_gradient_mol_m3:.2f} / "
        f"{row.cell_b_positive_gradient_mol_m3:.2f} mol m^-3"
    )
    print(f"Saved: {(CSV / 'experiment_1b_equal_soc_histories.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'experiment_1b_equal_soc_voltage_match.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'experiment_1b_equal_soc_history.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
