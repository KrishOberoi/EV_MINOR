"""Independent integrity checks for the pack and balancing result files.

This script intentionally recomputes invariants from CSV outputs rather than
calling the simulation functions, reducing the chance that a shared bug in the
simulation and metric code goes undetected.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "csv"
TOL = 1e-9


def main() -> None:
    trajectories = pd.read_csv(CSV / "four_cell_pack_trajectories.csv")
    pack = pd.read_csv(CSV / "four_cell_pack_summary.csv")
    cells = pd.read_csv(CSV / "four_cell_pack_cell_summary.csv")
    balancing = pd.read_csv(CSV / "balancing_comparison_timeseries.csv")
    metrics = pd.read_csv(CSV / "balancing_comparison_metrics.csv")

    for name, data in {
        "pack trajectories": trajectories,
        "pack summary": pack,
        "cell summary": cells,
        "balancing trajectories": balancing,
        "balancing metrics": metrics,
    }.items():
        assert data.notna().all().all(), f"Missing value in {name}"
        assert np.isfinite(data.select_dtypes(include=[np.number])).all().all(), f"Non-finite value in {name}"

    current_pivot = trajectories.pivot(index="time_s", columns="cell", values="current_A")
    assert (current_pivot.max(axis=1) - current_pivot.min(axis=1)).max() < TOL

    voltage_pivot = trajectories.pivot(index="time_s", columns="cell", values="voltage_V")
    reconstructed_pack_voltage = voltage_pivot.sum(axis=1).to_numpy()
    assert np.max(np.abs(reconstructed_pack_voltage - pack.pack_voltage_V.to_numpy())) < TOL

    capacity = cells.set_index("cell").capacity_ah.to_dict()
    for controller, data in balancing.groupby("controller"):
        by_time = data.groupby("time_s")
        balance_sum = by_time.balancing_current_A.sum()
        assert balance_sum.abs().max() < TOL, f"Non-conservative transfer in {controller}"
        cell_current_error = data.cell_current_A - data.pack_current_A - data.balancing_current_A
        assert cell_current_error.abs().max() < TOL, f"Current decomposition error in {controller}"

        for cell, series in data.groupby("cell"):
            series = series.sort_values("time_s").reset_index(drop=True)
            reconstructed_soc = [series.soc.iloc[0]]
            for k in range(len(series) - 1):
                dt = series.time_s.iloc[k + 1] - series.time_s.iloc[k]
                reconstructed_soc.append(
                    reconstructed_soc[-1]
                    - series.cell_current_A.iloc[k] * dt / (3600.0 * capacity[cell])
                )
            assert np.max(np.abs(np.asarray(reconstructed_soc) - series.soc.to_numpy())) < 1e-8

        voltage_spread = by_time.voltage_V.max() - by_time.voltage_V.min()
        soc_spread = by_time.soc.max() - by_time.soc.min()
        row = metrics[metrics.controller == controller].iloc[0]
        assert abs(voltage_spread.iloc[-1] * 1000 - row.final_voltage_spread_mV) < 1e-8
        assert abs(soc_spread.iloc[-1] * 100 - row.final_soc_spread_percentage_points) < 1e-8
        assert row.balancing_energy_Wh >= -TOL

    initial = balancing[balancing.time_s == balancing.time_s.min()]
    initial_spread = initial.groupby("controller").soc.agg(lambda x: x.max() - x.min())
    assert initial_spread.nunique() == 1
    print("All independent pack and controller invariants passed.")
    print(f"Checked {len(trajectories)} pack rows and {len(balancing)} controller rows.")
    print("Verified common series current, pack-voltage summation, zero-net transfer, current decomposition, SOC propagation, and metric reconstruction.")


if __name__ == "__main__":
    main()
