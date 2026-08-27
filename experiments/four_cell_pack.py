"""Build and simulate a heterogeneous four-cell series pack.

Each cell is solved with an SPM, but all four cells receive the same absolute
series current. Capacity, contact resistance, and initial SOC are varied to
represent cell-to-cell manufacturing and ageing differences.
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


CELL_CONFIG = [
    {"cell": "Cell 1", "initial_soc": 0.80, "capacity_ah": 5.00, "contact_resistance_ohm": 0.012},
    {"cell": "Cell 2", "initial_soc": 0.76, "capacity_ah": 4.90, "contact_resistance_ohm": 0.015},
    {"cell": "Cell 3", "initial_soc": 0.72, "capacity_ah": 4.70, "contact_resistance_ohm": 0.022},
    {"cell": "Cell 4", "initial_soc": 0.78, "capacity_ah": 4.95, "contact_resistance_ohm": 0.010},
]


def get_variable(solution: pybamm.Solution, *names: str):
    for name in names:
        try:
            return solution[name].entries
        except (KeyError, ValueError):
            continue
    raise KeyError("No requested variable is available: " + ", ".join(names))


def as_time_series(values, n_time: Optional[int] = None) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim == 1:
        return array
    if n_time is not None and array.shape[-1] == n_time:
        return array.reshape(-1, n_time).mean(axis=0)
    return array.reshape(-1)


def simulate_cell(config: dict) -> tuple[pd.DataFrame, pybamm.ParameterValues]:
    model = pybamm.lithium_ion.SPM(options={"thermal": "isothermal"})
    parameters = pybamm.ParameterValues("Chen2020")
    parameters.update(
        {
            "Nominal cell capacity [A.h]": config["capacity_ah"],
            "Contact resistance [Ohm]": config["contact_resistance_ohm"],
        }
    )
    experiment = pybamm.Experiment(
        [
            "Discharge at 2.5 A for 20 minutes",
            "Rest for 10 minutes",
            "Discharge at 1.25 A for 20 minutes",
            "Rest for 10 minutes",
        ],
        period="10 seconds",
    )
    simulation = pybamm.Simulation(
        model,
        parameter_values=parameters,
        experiment=experiment,
        solver=pybamm.CasadiSolver(mode="safe"),
    )
    solution = simulation.solve(initial_soc=config["initial_soc"])
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
    delta_t = np.diff(time_s)
    signed_capacity_change = np.concatenate(
        ([0.0], np.cumsum(0.5 * (current[1:] + current[:-1]) * delta_t / 3600.0))
    )
    soc = config["initial_soc"] - signed_capacity_change / config["capacity_ah"]
    data = pd.DataFrame(
        {
            "cell": config["cell"],
            "time_s": time_s,
            "current_A": current,
            "voltage_V": voltage,
            "soc": soc,
            "capacity_ah": config["capacity_ah"],
            "contact_resistance_ohm": config["contact_resistance_ohm"],
            "negative_gradient_mol_m3": negative_surface - negative_average,
            "positive_gradient_mol_m3": positive_surface - positive_average,
            "negative_overpotential_V": negative_eta,
            "positive_overpotential_V": positive_eta,
            "total_overpotential_V": positive_eta - negative_eta,
        }
    )
    return data, parameters


def main() -> None:
    pybamm.set_logging_level("WARNING")
    trajectories = []
    for config in CELL_CONFIG:
        data, _ = simulate_cell(config)
        trajectories.append(data)
    cells = pd.concat(trajectories, ignore_index=True)
    cells.to_csv(CSV / "four_cell_pack_trajectories.csv", index=False)

    pivot_voltage = cells.pivot(index="time_s", columns="cell", values="voltage_V")
    pivot_soc = cells.pivot(index="time_s", columns="cell", values="soc")
    pack = pd.DataFrame(
        {
            "time_s": pivot_voltage.index,
            "pack_voltage_V": pivot_voltage.sum(axis=1),
            "minimum_cell_voltage_V": pivot_voltage.min(axis=1),
            "maximum_cell_voltage_V": pivot_voltage.max(axis=1),
            "cell_voltage_spread_V": pivot_voltage.max(axis=1) - pivot_voltage.min(axis=1),
            "minimum_cell_soc": pivot_soc.min(axis=1),
            "maximum_cell_soc": pivot_soc.max(axis=1),
            "cell_soc_spread": pivot_soc.max(axis=1) - pivot_soc.min(axis=1),
        }
    )
    pack.to_csv(CSV / "four_cell_pack_summary.csv", index=False)

    summary = (
        cells.groupby("cell")
        .agg(
            initial_soc=("soc", "first"),
            final_soc=("soc", "last"),
            initial_voltage_V=("voltage_V", "first"),
            final_voltage_V=("voltage_V", "last"),
            capacity_ah=("capacity_ah", "first"),
            contact_resistance_ohm=("contact_resistance_ohm", "first"),
            max_abs_positive_gradient_mol_m3=("positive_gradient_mol_m3", lambda x: x.abs().max()),
            max_abs_total_overpotential_V=("total_overpotential_V", lambda x: x.abs().max()),
        )
        .reset_index()
    )
    summary.to_csv(CSV / "four_cell_pack_cell_summary.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    for cell, data in cells.groupby("cell"):
        axes[0, 0].plot(data.time_s / 60, data.voltage_V, label=cell)
        axes[0, 1].plot(data.time_s / 60, data.soc * 100, label=cell)
        axes[1, 0].plot(data.time_s / 60, data.positive_gradient_mol_m3, label=cell)
    axes[1, 1].plot(pack.time_s / 60, pack.pack_voltage_V, color="black", linewidth=2, label="Pack voltage")
    axes[1, 1].fill_between(
        pack.time_s / 60,
        pack.minimum_cell_voltage_V,
        pack.maximum_cell_voltage_V,
        alpha=0.2,
        label="Cell voltage envelope",
    )
    axes[0, 0].set_ylabel("Cell voltage [V]")
    axes[0, 1].set_ylabel("SOC [%]")
    axes[1, 0].set_ylabel("Positive gradient [mol m$^{-3}$]")
    axes[1, 1].set_ylabel("Pack voltage [V]")
    for row in axes:
        for ax in row:
            ax.grid(alpha=0.25)
            ax.legend(loc="best")
            ax.set_xlabel("Time [min]")
    fig.suptitle("Heterogeneous 4-series SPM pack before balancing")
    fig.tight_layout()
    fig.savefig(PLOTS / "four_cell_pack_baseline.png", dpi=180)
    plt.close(fig)

    print("Four-cell series pack completed.")
    print(f"Peak cell voltage spread: {pack.cell_voltage_spread_V.max() * 1000:.2f} mV")
    print(f"Final cell SOC spread: {pack.cell_soc_spread.iloc[-1] * 100:.2f} percentage points")
    print(f"Final pack voltage: {pack.pack_voltage_V.iloc[-1]:.3f} V")
    print(f"Saved: {(CSV / 'four_cell_pack_trajectories.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'four_cell_pack_summary.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'four_cell_pack_cell_summary.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'four_cell_pack_baseline.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
