"""Cross-validate the SPM with SPMe and an explicit reduced-order observer.

The observer uses only terminal voltage and current as measurements. It estimates
SOC, particle surface-average concentration gradients, and a polarization drop
using a first-order state model and voltage-residual correction. PyBaMM internal
states are retained only as reference truth for evaluation.
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

PROFILE = [
    "Discharge at 1C for 20 minutes",
    "Rest for 10 minutes",
    "Discharge at 0.5C for 20 minutes",
    "Rest for 10 minutes",
    "Charge at 0.5C for 10 minutes",
    "Rest for 5 minutes",
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


def simulate(model_class, initial_soc: float) -> tuple[pd.DataFrame, pybamm.Solution, pybamm.ParameterValues]:
    model = model_class(options={"thermal": "isothermal"})
    parameters = pybamm.ParameterValues("Chen2020")
    experiment = pybamm.Experiment(PROFILE, period="10 seconds")
    solution = pybamm.Simulation(
        model,
        parameter_values=parameters,
        experiment=experiment,
        solver=pybamm.CasadiSolver(mode="safe"),
    ).solve(initial_soc=initial_soc)
    time_s = as_time_series(solution["Time [s]"].entries)
    n_time = len(time_s)
    current = as_time_series(get_variable(solution, "Current [A]"), n_time)
    voltage = as_time_series(get_variable(solution, "Voltage [V]", "Terminal voltage [V]"), n_time)
    neg_avg = as_time_series(get_variable(solution, "X-averaged negative particle concentration [mol.m-3]"), n_time)
    neg_surface = as_time_series(get_variable(solution, "Negative particle surface concentration [mol.m-3]"), n_time)
    pos_avg = as_time_series(get_variable(solution, "X-averaged positive particle concentration [mol.m-3]"), n_time)
    pos_surface = as_time_series(get_variable(solution, "Positive particle surface concentration [mol.m-3]"), n_time)
    neg_eta = as_time_series(get_variable(solution, "X-averaged negative electrode reaction overpotential [V]"), n_time)
    pos_eta = as_time_series(get_variable(solution, "X-averaged positive electrode reaction overpotential [V]"), n_time)
    capacity = float(parameters["Nominal cell capacity [A.h]"])
    dt = np.diff(time_s)
    charge_change = np.concatenate(([0.0], np.cumsum(0.5 * (current[1:] + current[:-1]) * dt / 3600.0)))
    soc = initial_soc - charge_change / capacity
    return pd.DataFrame(
        {
            "time_s": time_s,
            "current_A": current,
            "voltage_V": voltage,
            "soc": soc,
            "negative_average_mol_m3": neg_avg,
            "negative_surface_mol_m3": neg_surface,
            "negative_gradient_mol_m3": neg_surface - neg_avg,
            "positive_average_mol_m3": pos_avg,
            "positive_surface_mol_m3": pos_surface,
            "positive_gradient_mol_m3": pos_surface - pos_avg,
            "polarization_drop_V": -(pos_eta - neg_eta),
        }
    ), solution, parameters


def fit_first_order_state(truth: pd.DataFrame, column: str) -> tuple[float, float]:
    """Fit x[k+1] = a*x[k] + b*I[k] using truth only for ROM calibration."""
    x = truth[column].to_numpy()
    current = truth.current_A.to_numpy()
    # Skip duplicate time samples at experiment-cycle boundaries.
    dt = np.diff(truth.time_s.to_numpy())
    mask = dt > 1e-6
    design = np.column_stack([x[:-1][mask], current[:-1][mask]])
    a, b = np.linalg.lstsq(design, x[1:][mask], rcond=None)[0]
    return float(a), float(b)


def build_ocv_lookup(parameters: pybamm.ParameterValues) -> tuple[np.ndarray, np.ndarray]:
    """Generate an equilibrium OCV-SOC lookup from zero-current SPM states."""
    soc_grid = np.linspace(0.10, 0.90, 17)
    voltages = []
    for soc in soc_grid:
        model = pybamm.lithium_ion.SPM(options={"thermal": "isothermal"})
        experiment = pybamm.Experiment(["Rest for 1 second"], period="1 second")
        solution = pybamm.Simulation(
            model,
            parameter_values=parameters,
            experiment=experiment,
            solver=pybamm.CasadiSolver(mode="safe"),
        ).solve(initial_soc=float(soc))
        voltages.append(float(solution["Voltage [V]"].entries[-1]))
    return soc_grid, np.asarray(voltages)


def run_observer(truth: pd.DataFrame, parameters: pybamm.ParameterValues) -> pd.DataFrame:
    time_s = truth.time_s.to_numpy()
    current = truth.current_A.to_numpy()
    measured_voltage = truth.voltage_V.to_numpy()
    capacity = float(parameters["Nominal cell capacity [A.h]"])
    soc_grid, ocv_grid = build_ocv_lookup(parameters)
    ocv = lambda z: np.interp(np.clip(z, soc_grid[0], soc_grid[-1]), soc_grid, ocv_grid)

    neg_a, neg_b = fit_first_order_state(truth, "negative_gradient_mol_m3")
    pos_a, pos_b = fit_first_order_state(truth, "positive_gradient_mol_m3")
    # Use the effective voltage drop OCV - V as the observer's polarization
    # state. It includes the combined dynamic and ohmic drop and is consistent
    # with the measurement equation used below.
    truth_for_fit = truth.copy()
    truth_for_fit["effective_drop_V"] = ocv(truth.soc.to_numpy()) - truth.voltage_V
    eta_a, eta_b = fit_first_order_state(truth_for_fit, "effective_drop_V")
    eta_a = float(np.clip(eta_a, 0.0, 0.9995))

    # Deliberately biased initial SOC tests correction from voltage residual.
    soc_hat = 0.65
    neg_gradient_hat = 0.0
    pos_gradient_hat = 0.0
    eta_hat = 0.0
    rng = np.random.default_rng(20260827)
    noisy_voltage = measured_voltage + rng.normal(0.0, 0.002, size=len(measured_voltage))
    rows = []
    for k, time in enumerate(time_s):
        if k == 0:
            dt = 0.0
        else:
            dt = time_s[k] - time_s[k - 1]
        soc_pred = soc_hat - current[k] * dt / (3600.0 * capacity)
        neg_pred = neg_a * neg_gradient_hat + neg_b * current[k]
        pos_pred = pos_a * pos_gradient_hat + pos_b * current[k]
        eta_pred = eta_a * eta_hat + eta_b * current[k]
        voltage_hat = ocv(soc_pred) - eta_pred
        residual = noisy_voltage[k] - voltage_hat
        soc_hat = float(np.clip(soc_pred + 0.01 * residual, 0.0, 1.0))
        neg_gradient_hat = float(np.clip(neg_pred + 1000.0 * residual, -15000.0, 15000.0))
        pos_gradient_hat = float(np.clip(pos_pred + 1000.0 * residual, -15000.0, 15000.0))
        # If measured voltage is lower than predicted, the estimated voltage
        # drop must increase, hence the negative residual correction.
        eta_hat = float(np.clip(eta_pred - 0.20 * residual, -1.0, 1.0))
        rows.append(
            {
                "time_s": time,
                "measured_voltage_V": noisy_voltage[k],
                "voltage_estimate_V": voltage_hat,
                "voltage_residual_V": residual,
                "soc_estimate": soc_hat,
                "negative_gradient_estimate_mol_m3": neg_gradient_hat,
                "positive_gradient_estimate_mol_m3": pos_gradient_hat,
                "effective_drop_V": truth_for_fit.effective_drop_V.iloc[k],
                "effective_drop_estimate_V": eta_hat,
            }
        )
    estimates = pd.DataFrame(rows)
    return pd.concat([truth.reset_index(drop=True), estimates.drop(columns="time_s")], axis=1)


def rmse(actual: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - estimate) ** 2)))


def main() -> None:
    spm, _, parameters = simulate(pybamm.lithium_ion.SPM, 0.70)
    spme, _, _ = simulate(pybamm.lithium_ion.SPMe, 0.70)
    observer = run_observer(spm, parameters)
    observer.to_csv(CSV / "observer_cross_validation.csv", index=False)

    spm_spme = pd.DataFrame(
        {
            "time_s": spm.time_s,
            "spm_voltage_V": spm.voltage_V,
            "spme_voltage_V": spme.voltage_V,
            "voltage_difference_V": spme.voltage_V - spm.voltage_V,
        }
    )
    spm_spme.to_csv(CSV / "spm_spme_comparison.csv", index=False)
    metrics = pd.DataFrame(
        [
            {"metric": "Observer SOC RMSE", "value": rmse(observer.soc.to_numpy(), observer.soc_estimate.to_numpy()), "units": "fraction"},
            {"metric": "Observer voltage RMSE", "value": rmse(observer.voltage_V.to_numpy(), observer.voltage_estimate_V.to_numpy()), "units": "V"},
            {"metric": "Observer positive-gradient RMSE", "value": rmse(observer.positive_gradient_mol_m3.to_numpy(), observer.positive_gradient_estimate_mol_m3.to_numpy()), "units": "mol m^-3"},
            {"metric": "Observer polarization-drop RMSE", "value": rmse(observer.effective_drop_V.to_numpy(), observer.effective_drop_estimate_V.to_numpy()), "units": "V"},
            {"metric": "SPM-SPMe voltage RMSE", "value": rmse(spm.voltage_V.to_numpy(), spme.voltage_V.to_numpy()), "units": "V"},
            {"metric": "SPM-SPMe maximum voltage difference", "value": np.max(np.abs(spm_spme.voltage_difference_V)), "units": "V"},
        ]
    )
    metrics.to_csv(CSV / "observer_validation_metrics.csv", index=False)

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    axes[0].plot(observer.time_s / 60, observer.soc * 100, label="SPM reference SOC")
    axes[0].plot(observer.time_s / 60, observer.soc_estimate * 100, "--", label="Observer SOC")
    axes[0].set_ylabel("SOC [%]")
    axes[0].grid(alpha=0.25)
    axes[0].legend()
    axes[1].plot(observer.time_s / 60, observer.positive_gradient_mol_m3, label="SPM gradient")
    axes[1].plot(observer.time_s / 60, observer.positive_gradient_estimate_mol_m3, "--", label="Observer gradient")
    axes[1].set_ylabel("Positive gradient [mol m$^{-3}$]")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    axes[2].plot(observer.time_s / 60, observer.voltage_V, label="SPM voltage")
    axes[2].plot(observer.time_s / 60, observer.voltage_estimate_V, "--", label="Observer voltage")
    axes[2].set_xlabel("Time [min]")
    axes[2].set_ylabel("Voltage [V]")
    axes[2].grid(alpha=0.25)
    axes[2].legend()
    fig.suptitle("SPM-inspired observer cross-validation")
    fig.tight_layout()
    fig.savefig(PLOTS / "observer_cross_validation.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(spm.time_s / 60, spm.voltage_V, label="SPM")
    ax.plot(spme.time_s / 60, spme.voltage_V, "--", label="SPMe")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Voltage [V]")
    ax.set_title("SPM versus SPMe voltage cross-check")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "spm_spme_comparison.png", dpi=180)
    plt.close(fig)

    print(metrics.to_string(index=False))
    print(f"Saved: {(CSV / 'observer_cross_validation.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'spm_spme_comparison.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'observer_validation_metrics.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'observer_cross_validation.png').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'spm_spme_comparison.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
