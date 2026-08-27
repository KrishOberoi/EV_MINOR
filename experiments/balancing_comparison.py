"""Compare baseline and active balancing strategies on the 4-cell pack.

The PyBaMM SPM pack is used to generate reference trajectories. A lightweight
control-oriented perturbation model then applies additional balancing currents
u_i while preserving the same series pack current and cell heterogeneity. This
keeps the controller experiment fast and makes its assumptions explicit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from four_cell_pack import CELL_CONFIG, CSV, PLOTS, ROOT, simulate_cell

BALANCING_CURRENT_A = 0.25
DT_S = 10.0
CONTROLLERS = ["Uncontrolled", "Voltage", "SOC", "Electrochemical"]


def build_reference_pack() -> pd.DataFrame:
    trajectories = []
    for config in CELL_CONFIG:
        trajectory, _ = simulate_cell(config)
        trajectories.append(trajectory)
    return pd.concat(trajectories, ignore_index=True)


def choose_pair(scores: np.ndarray, threshold: float) -> Optional[tuple[int, int]]:
    donor = int(np.argmax(scores))
    receiver = int(np.argmin(scores))
    if scores[donor] - scores[receiver] <= threshold:
        return None
    return donor, receiver


def run_controller(reference: pd.DataFrame, controller: str) -> pd.DataFrame:
    cells = [config["cell"] for config in CELL_CONFIG]
    base = {
        cell: reference[reference.cell == cell].sort_values("time_s").reset_index(drop=True)
        for cell in cells
    }
    time_s = base[cells[0]].time_s.to_numpy()
    n_steps = len(time_s)
    state_soc = np.array([base[cell].soc.iloc[0] for cell in cells], dtype=float)
    extra_positive_gradient = np.zeros(len(cells))
    extra_eta = np.zeros(len(cells))
    records = []
    balance_energy_wh = 0.0
    balance_events = 0
    total_updates = 0

    # Fixed engineering scales keep the electrochemical score interpretable and
    # prevent the small overpotential signal from overwhelming SOC. These are
    # controller tuning constants, not fitted claims about a production BMS.
    gradient_scale = 2000.0
    eta_scale = 0.10
    soc_scale = 0.02

    for k, time in enumerate(time_s):
        base_current = np.array([base[cell].current_A.iloc[k] for cell in cells])
        base_voltage = np.array([base[cell].voltage_V.iloc[k] for cell in cells])
        base_soc = np.array([base[cell].soc.iloc[k] for cell in cells])
        base_gradient = np.array(
            [base[cell].positive_gradient_mol_m3.iloc[k] for cell in cells]
        )
        base_eta = np.array(
            [base[cell].total_overpotential_V.iloc[k] for cell in cells]
        )
        voltage = base_voltage + (state_soc - base_soc) * 1.0 - extra_eta
        gradient = base_gradient + extra_positive_gradient
        eta = base_eta + extra_eta

        if controller == "Voltage":
            pair = choose_pair(voltage, 0.005)
        elif controller == "SOC":
            pair = choose_pair(state_soc, 0.005)
        elif controller == "Electrochemical":
            score = (
                (state_soc - state_soc.mean()) / soc_scale
                + 0.2 * (gradient - gradient.mean()) / gradient_scale
                + 0.1 * (eta - eta.mean()) / eta_scale
            )
            pair = choose_pair(score, 0.10)
        else:
            pair = None

        balancing_current = np.zeros(len(cells))
        if pair is not None:
            donor, receiver = pair
            # Positive current is discharge. The high-state donor is discharged
            # and the low-state receiver is charged. The ideal transfer sums to 0.
            balancing_current[donor] = BALANCING_CURRENT_A
            balancing_current[receiver] = -BALANCING_CURRENT_A
            balance_events += 1
        total_updates += 1
        cell_current = base_current + balancing_current
        balance_energy_wh += np.sum(np.abs(balancing_current) * voltage) * DT_S / 3600.0

        for i, cell in enumerate(cells):
            records.append(
                {
                    "controller": controller,
                    "cell": cell,
                    "time_s": time,
                    "pack_current_A": base_current[i],
                    "balancing_current_A": balancing_current[i],
                    "cell_current_A": cell_current[i],
                    "voltage_V": voltage[i],
                    "soc": state_soc[i],
                    "positive_gradient_mol_m3": gradient[i],
                    "total_overpotential_V": eta[i],
                }
            )

        # Propagate the controlled state to the next sample. The gradient
        # perturbation is intentionally first-order, making its computational
        # cost representative of a reduced-order controller model.
        if k < n_steps - 1:
            for i, config in enumerate(CELL_CONFIG):
                state_soc[i] -= cell_current[i] * DT_S / (3600.0 * config["capacity_ah"])
            extra_positive_gradient += DT_S * (
                -extra_positive_gradient / 180.0 + 25.0 * balancing_current
            )
            extra_eta += DT_S * (
                -extra_eta / 80.0 + 0.0005 * balancing_current
            )

    result = pd.DataFrame(records)
    result.attrs["balance_energy_wh"] = balance_energy_wh
    result.attrs["balance_events"] = balance_events
    result.attrs["total_updates"] = total_updates
    return result


def calculate_metrics(result: pd.DataFrame) -> dict:
    grouped = result.groupby("time_s")
    voltage_spread = grouped.voltage_V.max() - grouped.voltage_V.min()
    soc_spread = grouped.soc.max() - grouped.soc.min()
    stress = result.total_overpotential_V.abs() + result.positive_gradient_mol_m3.abs() / 10000.0
    return {
        "controller": result.controller.iloc[0],
        "initial_soc_spread_percentage_points": soc_spread.iloc[0] * 100,
        "final_soc_spread_percentage_points": soc_spread.iloc[-1] * 100,
        "peak_soc_spread_percentage_points": soc_spread.max() * 100,
        "initial_voltage_spread_mV": voltage_spread.iloc[0] * 1000,
        "final_voltage_spread_mV": voltage_spread.iloc[-1] * 1000,
        "peak_voltage_spread_mV": voltage_spread.max() * 1000,
        "balancing_energy_Wh": result.attrs.get("balance_energy_wh", 0.0),
        "balancing_events": result.attrs.get("balance_events", 0),
        "observer_controller_updates": result.attrs.get("total_updates", 0),
        "peak_electrochemical_stress_index": stress.max(),
    }


def plot_results(all_results: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    for controller, data in all_results.groupby("controller"):
        summary = data.groupby("time_s").agg(
            voltage_spread_V=("voltage_V", lambda x: x.max() - x.min()),
            soc_spread=("soc", lambda x: x.max() - x.min()),
            balance_current_A=("balancing_current_A", lambda x: x.abs().sum()),
        )
        axes[0, 0].plot(summary.index / 60, summary.soc_spread * 100, label=controller)
        axes[0, 1].plot(summary.index / 60, summary.voltage_spread_V * 1000, label=controller)
        axes[1, 0].plot(summary.index / 60, summary.balance_current_A, label=controller)
    final_soc = (
        all_results.sort_values("time_s")
        .groupby(["controller", "cell"])
        .last()
        .reset_index()
        .pivot(index="cell", columns="controller", values="soc")
        * 100
    )
    final_soc.plot(kind="bar", ax=axes[1, 1])
    axes[0, 0].set_ylabel("SOC spread [percentage points]")
    axes[0, 1].set_ylabel("Voltage spread [mV]")
    axes[1, 0].set_ylabel("|Balancing current| sum [A]")
    axes[1, 1].set_ylabel("Final SOC [%]")
    axes[1, 1].set_xlabel("Cell")
    for row in axes:
        for ax in row:
            ax.grid(alpha=0.25)
            ax.legend(loc="best")
            if ax != axes[1, 1]:
                ax.set_xlabel("Time [min]")
    fig.suptitle("4-cell active-balancing controller comparison")
    fig.tight_layout()
    fig.savefig(PLOTS / "balancing_comparison.png", dpi=180)
    plt.close(fig)


def main() -> None:
    reference = build_reference_pack()
    all_results = []
    metrics = []
    for controller in CONTROLLERS:
        result = run_controller(reference, controller)
        all_results.append(result)
        metrics.append(calculate_metrics(result))
    all_results = pd.concat(all_results, ignore_index=True)
    all_results.to_csv(CSV / "balancing_comparison_timeseries.csv", index=False)
    pd.DataFrame(metrics).to_csv(CSV / "balancing_comparison_metrics.csv", index=False)
    plot_results(all_results)
    print(pd.DataFrame(metrics).to_string(index=False))
    print(f"Saved: {(CSV / 'balancing_comparison_timeseries.csv').relative_to(ROOT)}")
    print(f"Saved: {(CSV / 'balancing_comparison_metrics.csv').relative_to(ROOT)}")
    print(f"Saved: {(PLOTS / 'balancing_comparison.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
