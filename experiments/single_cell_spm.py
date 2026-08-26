"""Run the Step 1 single-cell SPM experiment.

This script deliberately keeps the model and post-processing explicit. It produces
an immediately usable baseline for the later heterogeneous-pack experiments.
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
    """Return the first variable available in the current PyBaMM solution."""
    for name in names:
        try:
            return solution[name].entries
        except (KeyError, ValueError):
            continue
    available = ", ".join(names)
    raise KeyError(f"None of these PyBaMM variables were available: {available}")


def as_vector(values, n_time: Optional[int] = None) -> np.ndarray:
    """Convert a PyBaMM output to one value per time point.

    Particle concentration variables can retain a radial dimension even in the
    SPM. When present, average that dimension rather than flattening it into the
    time axis.
    """
    array = np.asarray(values)
    if array.ndim == 1:
        return array
    if n_time is not None and array.shape[-1] == n_time:
        return array.reshape(-1, n_time).mean(axis=0)
    return array.reshape(-1)


def main() -> None:
    pybamm.set_logging_level("WARNING")

    # The SPM resolves lithium diffusion in representative negative and positive
    # electrode particles, while omitting the full spatial electrolyte dynamics.
    model = pybamm.lithium_ion.SPM(options={"thermal": "isothermal"})
    parameter_values = pybamm.ParameterValues("Chen2020")

    # A short, reproducible current profile. Positive current is discharge.
    experiment = pybamm.Experiment(
        [
            "Discharge at 1C for 20 minutes",
            "Rest for 10 minutes",
            "Discharge at 0.5C for 20 minutes",
            "Rest for 10 minutes",
            "Charge at 0.5C for 10 minutes",
            "Rest for 5 minutes",
        ],
        period="10 seconds",
    )

    simulation = pybamm.Simulation(
        model,
        parameter_values=parameter_values,
        experiment=experiment,
        solver=pybamm.CasadiSolver(mode="safe"),
    )
    initial_soc = 0.80
    solution = simulation.solve(initial_soc=initial_soc)

    time_s = as_vector(solution["Time [s]"].entries)
    nominal_capacity = float(parameter_values["Nominal cell capacity [A.h]"])
    discharge_capacity = as_vector(
        get_variable(solution, "Discharge capacity [A.h]"), len(time_s)
    )

    voltage = as_vector(
        get_variable(solution, "Voltage [V]", "Terminal voltage [V]"), len(time_s)
    )
    current = as_vector(get_variable(solution, "Current [A]"), len(time_s))

    # The PyBaMM discharge-capacity variable is cumulative and does not undo
    # capacity during a later charge step. For this mixed current profile, use
    # signed coulomb counting so SOC rises during charging as it should.
    delta_t = np.diff(time_s)
    signed_capacity_change = np.concatenate(
        ([0.0], np.cumsum(0.5 * (current[1:] + current[:-1]) * delta_t / 3600.0))
    )
    soc = initial_soc - signed_capacity_change / nominal_capacity
    neg_avg = as_vector(
        get_variable(
        solution,
        "X-averaged negative particle concentration [mol.m-3]",
        "Average negative particle concentration [mol.m-3]",
        ),
        len(time_s),
    )
    pos_avg = as_vector(
        get_variable(
        solution,
        "X-averaged positive particle concentration [mol.m-3]",
        "Average positive particle concentration [mol.m-3]",
        ),
        len(time_s),
    )
    neg_surface = as_vector(
        get_variable(
        solution,
        "Negative particle surface concentration [mol.m-3]",
        "X-averaged negative particle surface concentration [mol.m-3]",
        ),
        len(time_s),
    )
    pos_surface = as_vector(
        get_variable(
        solution,
        "Positive particle surface concentration [mol.m-3]",
        "X-averaged positive particle surface concentration [mol.m-3]",
        ),
        len(time_s),
    )
    neg_eta = as_vector(
        get_variable(
        solution,
        "X-averaged negative electrode reaction overpotential [V]",
        "X-averaged negative electrode overpotential [V]",
        ),
        len(time_s),
    )
    pos_eta = as_vector(
        get_variable(
        solution,
        "X-averaged positive electrode reaction overpotential [V]",
        "X-averaged positive electrode overpotential [V]",
        ),
        len(time_s),
    )

    # Concentration gradients are useful electrochemical-state indicators for
    # the balancing work. They distinguish average lithium from surface lithium.
    neg_gradient = neg_surface - neg_avg
    pos_gradient = pos_surface - pos_avg
    total_overpotential = pos_eta - neg_eta

    data = pd.DataFrame(
        {
            "time_s": time_s,
            "current_A": current,
            "voltage_V": voltage,
            "soc": soc,
            "negative_particle_average_mol_m3": neg_avg,
            "negative_particle_surface_mol_m3": neg_surface,
            "negative_surface_minus_average_mol_m3": neg_gradient,
            "positive_particle_average_mol_m3": pos_avg,
            "positive_particle_surface_mol_m3": pos_surface,
            "positive_surface_minus_average_mol_m3": pos_gradient,
            "negative_overpotential_V": neg_eta,
            "positive_overpotential_V": pos_eta,
            "total_overpotential_V": total_overpotential,
        }
    )
    output_csv = CSV / "single_cell_spm_timeseries.csv"
    data.to_csv(output_csv, index=False)

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    axes[0].plot(time_s / 60, voltage, color="#173f5f", linewidth=2)
    axes[0].set_ylabel("Voltage [V]")
    axes[0].grid(alpha=0.25)
    axes[0].set_title("Single-cell SPM: terminal response and electrochemical states")

    axes[1].plot(time_s / 60, soc * 100, color="#20639b", label="SOC")
    axes[1].set_ylabel("SOC [%]")
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="best")

    axes[2].plot(time_s / 60, neg_gradient, label="Negative surface - average")
    axes[2].plot(time_s / 60, pos_gradient, label="Positive surface - average")
    axes[2].set_xlabel("Time [min]")
    axes[2].set_ylabel("Concentration difference [mol m$^{-3}$]")
    axes[2].grid(alpha=0.25)
    axes[2].legend(loc="best")
    fig.tight_layout()
    fig.savefig(PLOTS / "single_cell_spm_states.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(time_s / 60, voltage, color="#173f5f", linewidth=2)
    axes[0].set_ylabel("Voltage [V]")
    axes[0].grid(alpha=0.25)
    axes[1].plot(time_s / 60, total_overpotential, color="#f6a01a", linewidth=2)
    axes[1].set_xlabel("Time [min]")
    axes[1].set_ylabel("Total overpotential [V]")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(PLOTS / "single_cell_spm_voltage.png", dpi=180)
    plt.close(fig)

    print(f"Completed single-cell SPM simulation with {len(data)} time points.")
    print(f"Time span: {time_s[0] / 60:.1f} to {time_s[-1] / 60:.1f} minutes")
    print(f"Voltage range: {voltage.min():.3f} to {voltage.max():.3f} V")
    print(f"SOC range: {soc.min() * 100:.1f} to {soc.max() * 100:.1f} %")
    print(f"Saved: {output_csv.relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'single_cell_spm_states.png').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'single_cell_spm_voltage.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
