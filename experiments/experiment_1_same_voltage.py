"""Experiment 1: same terminal voltage, different internal electrochemical state.

Two nominally identical SPM cells are given different initial SOCs and current
histories. The script searches their trajectories for a cross-time pair whose
terminal voltages differ by at most 2 mV, then compares internal model states.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pybamm

ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "results" / "plots"
CSV = ROOT / "results" / "csv"
PLOTS.mkdir(parents=True, exist_ok=True)
CSV.mkdir(parents=True, exist_ok=True)


def get_variable(solution: pybamm.Solution, *names: str):
    for name in names:
        try:
            return solution[name].entries
        except (KeyError, ValueError):
            continue
    raise KeyError("No requested variable is available: " + ", ".join(names))


def as_time_series(values, n_time: Optional[int] = None) -> np.ndarray:
    """Return one scalar per time point, averaging any particle coordinate."""
    array = np.asarray(values)
    if array.ndim == 1:
        return array
    if n_time is not None and array.shape[-1] == n_time:
        return array.reshape(-1, n_time).mean(axis=0)
    return array.reshape(-1)


def simulate_cell(label: str, initial_soc: float, steps: list[str]) -> pd.DataFrame:
    model = pybamm.lithium_ion.SPM(options={"thermal": "isothermal"})
    parameters = pybamm.ParameterValues("Chen2020")
    experiment = pybamm.Experiment(steps, period="10 seconds")
    simulation = pybamm.Simulation(
        model,
        parameter_values=parameters,
        experiment=experiment,
        solver=pybamm.CasadiSolver(mode="safe"),
    )
    solution = simulation.solve(initial_soc=initial_soc)

    time_s = as_time_series(solution["Time [s]"].entries)
    n_time = len(time_s)
    current = as_time_series(get_variable(solution, "Current [A]"), n_time)
    voltage = as_time_series(
        get_variable(solution, "Voltage [V]", "Terminal voltage [V]"), n_time
    )
    negative_average = as_time_series(
        get_variable(
            solution,
            "X-averaged negative particle concentration [mol.m-3]",
            "Average negative particle concentration [mol.m-3]",
        ),
        n_time,
    )
    negative_surface = as_time_series(
        get_variable(
            solution,
            "Negative particle surface concentration [mol.m-3]",
            "X-averaged negative particle surface concentration [mol.m-3]",
        ),
        n_time,
    )
    positive_average = as_time_series(
        get_variable(
            solution,
            "X-averaged positive particle concentration [mol.m-3]",
            "Average positive particle concentration [mol.m-3]",
        ),
        n_time,
    )
    positive_surface = as_time_series(
        get_variable(
            solution,
            "Positive particle surface concentration [mol.m-3]",
            "X-averaged positive particle surface concentration [mol.m-3]",
        ),
        n_time,
    )
    negative_eta = as_time_series(
        get_variable(
            solution,
            "X-averaged negative electrode reaction overpotential [V]",
            "X-averaged negative electrode overpotential [V]",
        ),
        n_time,
    )
    positive_eta = as_time_series(
        get_variable(
            solution,
            "X-averaged positive electrode reaction overpotential [V]",
            "X-averaged positive electrode overpotential [V]",
        ),
        n_time,
    )

    capacity_ah = float(parameters["Nominal cell capacity [A.h]"])
    delta_t = np.diff(time_s)
    signed_capacity_change = np.concatenate(
        ([0.0], np.cumsum(0.5 * (current[1:] + current[:-1]) * delta_t / 3600.0))
    )
    soc = initial_soc - signed_capacity_change / capacity_ah

    return pd.DataFrame(
        {
            "cell": label,
            "time_s": time_s,
            "current_A": current,
            "voltage_V": voltage,
            "soc": soc,
            "negative_average_mol_m3": negative_average,
            "negative_surface_mol_m3": negative_surface,
            "negative_gradient_mol_m3": negative_surface - negative_average,
            "positive_average_mol_m3": positive_average,
            "positive_surface_mol_m3": positive_surface,
            "positive_gradient_mol_m3": positive_surface - positive_average,
            "negative_overpotential_V": negative_eta,
            "positive_overpotential_V": positive_eta,
            "total_overpotential_V": positive_eta - negative_eta,
        }
    )


def find_voltage_match(cell_a: pd.DataFrame, cell_b: pd.DataFrame) -> pd.DataFrame:
    """Find the clearest voltage match after both cells have experienced load."""
    voltage_difference = cell_a.voltage_V.to_numpy()[:, None] - cell_b.voltage_V.to_numpy()[None, :]
    eligible = (
        (np.abs(voltage_difference) <= 0.002)
        & (cell_a.time_s.to_numpy()[:, None] >= 300.0)
        & (cell_b.time_s.to_numpy()[None, :] >= 300.0)
    )
    indices = np.argwhere(eligible)
    if len(indices) == 0:
        best = np.unravel_index(np.abs(voltage_difference).argmin(), voltage_difference.shape)
        raise RuntimeError(
            "No voltage match within 2 mV. Closest difference was "
            f"{abs(voltage_difference[best]) * 1000:.3f} mV."
        )

    # Prefer a match with a visible SOC separation, while using electrochemical
    # state separation as a tie-breaker. This makes the result useful for the
    # report rather than selecting an uninformative nearly identical state.
    scores = []
    for i, j in indices:
        soc_gap = abs(cell_a.soc.iloc[i] - cell_b.soc.iloc[j])
        neg_gap = abs(cell_a.negative_gradient_mol_m3.iloc[i] - cell_b.negative_gradient_mol_m3.iloc[j])
        pos_gap = abs(cell_a.positive_gradient_mol_m3.iloc[i] - cell_b.positive_gradient_mol_m3.iloc[j])
        eta_gap = abs(cell_a.total_overpotential_V.iloc[i] - cell_b.total_overpotential_V.iloc[j])
        score = soc_gap + 1e-6 * (neg_gap + pos_gap) + eta_gap
        scores.append(score)
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


def plot_results(cell_a: pd.DataFrame, cell_b: pd.DataFrame, match: pd.DataFrame) -> None:
    a = match.iloc[0]
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)

    axes[0].plot(cell_a.time_s / 60, cell_a.voltage_V, label="Cell A", linewidth=2)
    axes[0].plot(cell_b.time_s / 60, cell_b.voltage_V, label="Cell B", linewidth=2)
    axes[0].scatter([a.cell_a_time_s / 60, a.cell_b_time_s / 60], [a.cell_a_voltage_V, a.cell_b_voltage_V], color="black", zorder=5)
    axes[0].set_ylabel("Voltage [V]")
    axes[0].set_title("Experiment 1: voltage-matched cells with different histories")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(cell_a.time_s / 60, cell_a.soc * 100, label="Cell A SOC")
    axes[1].plot(cell_b.time_s / 60, cell_b.soc * 100, label="Cell B SOC")
    axes[1].scatter([a.cell_a_time_s / 60, a.cell_b_time_s / 60], [a.cell_a_soc * 100, a.cell_b_soc * 100], color="black", zorder=5)
    axes[1].set_ylabel("SOC [%]")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    axes[2].plot(cell_a.time_s / 60, cell_a.positive_gradient_mol_m3, label="Cell A positive gradient")
    axes[2].plot(cell_b.time_s / 60, cell_b.positive_gradient_mol_m3, label="Cell B positive gradient")
    axes[2].scatter([a.cell_a_time_s / 60, a.cell_b_time_s / 60], [a.cell_a_positive_gradient_mol_m3, a.cell_b_positive_gradient_mol_m3], color="black", zorder=5)
    axes[2].set_xlabel("Local time [min]")
    axes[2].set_ylabel("Surface - average [mol m$^{-3}$]")
    axes[2].grid(alpha=0.25)
    axes[2].legend()

    fig.tight_layout()
    fig.savefig(PLOTS / "experiment_1_same_voltage_different_state.png", dpi=180)
    plt.close(fig)


def main() -> None:
    pybamm.set_logging_level("WARNING")
    cell_a = simulate_cell(
        "A",
        0.60,
        [
            "Discharge at 1C for 10 minutes",
            "Rest for 5 minutes",
            "Charge at 0.5C for 5 minutes",
            "Rest for 5 minutes",
            "Discharge at 0.5C for 10 minutes",
            "Rest for 10 minutes",
        ],
    )
    cell_b = simulate_cell(
        "B",
        0.65,
        [
            "Discharge at 0.5C for 10 minutes",
            "Rest for 5 minutes",
            "Discharge at 1C for 5 minutes",
            "Rest for 2 minutes",
            "Discharge at 0.5C for 10 minutes",
            "Rest for 13 minutes",
        ],
    )
    combined = pd.concat([cell_a, cell_b], ignore_index=True)
    combined.to_csv(CSV / "experiment_1_cell_histories.csv", index=False)
    match = find_voltage_match(cell_a, cell_b)
    match.to_csv(CSV / "experiment_1_voltage_match.csv", index=False)
    plot_results(cell_a, cell_b, match)

    row = match.iloc[0]
    print("Experiment 1 completed.")
    print(f"Voltage difference: {row.voltage_difference_mV:.3f} mV")
    print(f"Cell A: {row.cell_a_voltage_V:.4f} V, {row.cell_a_soc * 100:.2f}% SOC at {row.cell_a_time_s / 60:.2f} min")
    print(f"Cell B: {row.cell_b_voltage_V:.4f} V, {row.cell_b_soc * 100:.2f}% SOC at {row.cell_b_time_s / 60:.2f} min")
    print(f"SOC separation: {row.soc_difference_percentage_points:.2f} percentage points")
    print(f"Positive gradient A/B: {row.cell_a_positive_gradient_mol_m3:.2f} / {row.cell_b_positive_gradient_mol_m3:.2f} mol m^-3")
    print(f"Saved: {(CSV / 'experiment_1_cell_histories.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'experiment_1_voltage_match.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'experiment_1_same_voltage_different_state.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
