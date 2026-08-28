"""Acceptance-oriented checks for all completed research stages.

This script reads the generated public artifacts and checks each completed
requirement with a concrete assertion. It is intentionally separate from the
simulation scripts so that the report's claims are verified after execution.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "csv"
PLOTS = ROOT / "results" / "plots"


def assert_finite(frame: pd.DataFrame, label: str) -> None:
    assert not frame.empty, f"{label} is empty"
    assert frame.notna().all().all(), f"{label} contains missing values"
    numeric = frame.select_dtypes(include=[np.number])
    assert np.isfinite(numeric.to_numpy()).all(), f"{label} contains non-finite values"


def main() -> None:
    required_csv = [
        "single_cell_spm_timeseries.csv",
        "experiment_1_voltage_match.csv",
        "experiment_1_usable_energy.csv",
        "experiment_1_matched_state_discharges.csv",
        "experiment_1b_equal_soc_voltage_match.csv",
        "four_cell_pack_trajectories.csv",
        "four_cell_pack_summary.csv",
        "four_cell_pack_cell_summary.csv",
        "balancing_comparison_timeseries.csv",
        "balancing_comparison_metrics.csv",
        "observer_cross_validation.csv",
        "observer_validation_metrics.csv",
        "spm_spme_comparison.csv",
    ]
    required_plots = [
        "single_cell_spm_states.png",
        "single_cell_spm_voltage.png",
        "experiment_1_same_voltage_different_state.png",
        "experiment_1_usable_energy.png",
        "experiment_1b_equal_soc_history.png",
        "four_cell_pack_baseline.png",
        "balancing_comparison.png",
        "observer_cross_validation.png",
        "spm_spme_comparison.png",
        "balancing_robustness_ablation.png",
    ]
    for name in required_csv:
        assert (CSV / name).is_file(), f"Missing required CSV: {name}"
    for name in required_plots:
        path = PLOTS / name
        assert path.is_file() and path.stat().st_size > 0, f"Missing/empty plot: {name}"

    single = pd.read_csv(CSV / "single_cell_spm_timeseries.csv")
    assert_finite(single, "single-cell SPM output")
    assert len(single) == 456, "Step 1 did not produce the expected 456 samples"
    assert single.time_s.iloc[-1] == 4500.0, "Step 1 time horizon changed unexpectedly"
    assert single.voltage_V.between(3.4, 4.1).all(), "Step 1 voltage left expected range"
    assert single.soc.max() - single.soc.min() > 0.4, "Step 1 SOC excursion is too small"
    assert single.positive_surface_minus_average_mol_m3.abs().max() > 1000, "Step 1 did not expose a positive-particle gradient"
    print("Step 1 PASS: 456 finite samples, 75-minute horizon, dynamic voltage/SOC, and nonzero internal gradient.")

    match = pd.read_csv(CSV / "experiment_1_voltage_match.csv").iloc[0]
    energy = pd.read_csv(CSV / "experiment_1_usable_energy.csv")
    discharges = pd.read_csv(CSV / "experiment_1_matched_state_discharges.csv")
    assert_finite(pd.DataFrame([match]), "Experiment 1 voltage match")
    assert_finite(energy, "Experiment 1 energy output")
    assert_finite(discharges, "Experiment 1 discharge trajectories")
    assert 0 < match.voltage_difference_mV <= 2, "Experiment 1 voltage threshold failed"
    assert match.soc_difference_percentage_points > 1, "Experiment 1 did not separate SOC"
    assert abs(match.cell_a_positive_gradient_mol_m3 - match.cell_b_positive_gradient_mol_m3) > 100, "Experiment 1 did not separate internal gradient"
    assert len(energy) == 2 and (energy.usable_energy_Wh > 0).all(), "Experiment 1 energy output invalid"
    assert abs(energy.usable_energy_Wh.iloc[0] - energy.usable_energy_Wh.iloc[1]) > 1, "Experiment 1 energy difference is too small"
    for cell, series in discharges.groupby("cell"):
        series = series.sort_values("time_s")
        assert len(series) > 2 and np.all(np.diff(series.time_s) > 0), f"Energy time grid invalid for {cell}"
        assert np.allclose(series.current_A, 5.0), f"Common energy load invalid for {cell}"
        recomputed = np.trapz(series.voltage_V, series.time_s) * 5.0 / 3600.0
        reported = energy.loc[energy.cell == cell, "usable_energy_Wh"].iloc[0]
        assert abs(recomputed - reported) < 1e-9, f"Energy integration mismatch for {cell}"
        assert abs(series.voltage_V.iloc[-1] - 2.5) < 0.02, f"Cutoff voltage invalid for {cell}"
    print(f"Experiment 1 PASS: {match.voltage_difference_mV:.3f} mV voltage gap, {match.soc_difference_percentage_points:.2f} pp SOC gap, and {abs(energy.usable_energy_Wh.iloc[0] - energy.usable_energy_Wh.iloc[1]):.3f} Wh energy gap.")

    controlled = pd.read_csv(CSV / "experiment_1b_equal_soc_voltage_match.csv").iloc[0]
    assert_finite(pd.DataFrame([controlled]), "controlled history match")
    assert 0 < controlled.voltage_difference_mV <= 2, "Controlled history voltage threshold failed"
    assert controlled.soc_difference_percentage_points <= 1, "Controlled history SOC threshold failed"
    assert abs(controlled.cell_a_positive_gradient_mol_m3 - controlled.cell_b_positive_gradient_mol_m3) > 100, "Controlled history did not retain internal-state separation"
    print(f"Controlled Experiment 1B PASS: {controlled.voltage_difference_mV:.3f} mV voltage gap, {controlled.soc_difference_percentage_points:.3f} pp SOC gap, and measurable gradient separation.")

    pack = pd.read_csv(CSV / "four_cell_pack_trajectories.csv")
    pack_summary = pd.read_csv(CSV / "four_cell_pack_summary.csv")
    cell_summary = pd.read_csv(CSV / "four_cell_pack_cell_summary.csv")
    for frame, label in [(pack, "pack trajectories"), (pack_summary, "pack summary"), (cell_summary, "cell summary")]:
        assert_finite(frame, label)
    assert pack.cell.nunique() == 4, "Pack does not contain four cells"
    current_spread = pack.groupby("time_s").current_A.agg(lambda values: values.max() - values.min())
    assert current_spread.max() < 1e-9, "Series cells do not share a common current"
    assert pack_summary.cell_voltage_spread_V.max() > 0.05, "Pack voltage mismatch is not observable"
    assert pack_summary.cell_soc_spread.iloc[-1] > 0.05, "Pack SOC mismatch is not observable"
    weakest = cell_summary[cell_summary.cell == "Cell 3"].iloc[0]
    assert weakest.capacity_ah == cell_summary.capacity_ah.min(), "Weakest-cell capacity configuration changed"
    assert weakest.contact_resistance_ohm == cell_summary.contact_resistance_ohm.max(), "Weakest-cell resistance configuration changed"
    print(f"4-cell pack PASS: {pack.cell.nunique()} cells, common-current invariant, {1000 * pack_summary.cell_voltage_spread_V.max():.2f} mV peak spread, and {100 * pack_summary.cell_soc_spread.iloc[-1]:.2f} pp final SOC spread.")

    balancing = pd.read_csv(CSV / "balancing_comparison_timeseries.csv")
    metrics = pd.read_csv(CSV / "balancing_comparison_metrics.csv")
    assert_finite(balancing, "balancing trajectories")
    assert_finite(metrics, "balancing metrics")
    expected = {"Uncontrolled", "Voltage", "SOC", "Electrochemical"}
    assert set(metrics.controller) == expected, "Balancing controller set changed"
    transfer_error = balancing.groupby(["controller", "time_s"]).balancing_current_A.sum().abs().max()
    assert transfer_error < 1e-9, "Ideal balancing transfer is not conservative"
    uncontrolled = metrics.loc[metrics.controller == "Uncontrolled", "final_soc_spread_percentage_points"].iloc[0]
    active = metrics[metrics.controller != "Uncontrolled"]
    assert (active.final_soc_spread_percentage_points < uncontrolled).all(), "Active controllers did not reduce final SOC spread"
    assert (metrics.balancing_energy_Wh >= 0).all(), "Balancing energy became negative"
    print(f"Balancing PASS: {len(expected)} controllers, zero-net transfer, and all active controllers below {uncontrolled:.3f} pp uncontrolled final SOC spread.")

    ablation = pd.read_csv(CSV / "balancing_robustness_ablation_metrics.csv")
    assert_finite(ablation, "balancing robustness and ablation metrics")
    assert set(ablation.scenario) == {"baseline", "soc_shift", "capacity_resistance"}, "Ablation scenario set changed"
    expected_labels = {
        "Uncontrolled",
        "SOC",
        "Electrochemical",
        "Electrochemical_no_gradient",
        "Electrochemical_no_overpotential",
        "Electrochemical_SOC_only",
    }
    assert set(ablation.controller_label) == expected_labels, "Ablation controller set changed"
    for scenario, data in ablation.groupby("scenario"):
        reference_spread = data.loc[data.controller_label == "Uncontrolled", "final_soc_spread_percentage_points"].iloc[0]
        active = data[data.controller_label != "Uncontrolled"]
        assert (active.final_soc_spread_percentage_points < reference_spread).all(), f"Ablation failed to improve {scenario}"
    full = ablation[ablation.controller_label == "Electrochemical"].set_index("scenario").final_soc_spread_percentage_points
    no_gradient = ablation[ablation.controller_label == "Electrochemical_no_gradient"].set_index("scenario").final_soc_spread_percentage_points
    no_eta = ablation[ablation.controller_label == "Electrochemical_no_overpotential"].set_index("scenario").final_soc_spread_percentage_points
    assert ((full - no_gradient).abs() > 1e-9).any() or ((full - no_eta).abs() > 1e-9).any(), "Score ablations had no observable effect"
    print("Ablation PASS: three heterogeneity scenarios, six controller labels, and observable score-term effects.")

    observer = pd.read_csv(CSV / "observer_cross_validation.csv")
    observer_metrics = pd.read_csv(CSV / "observer_validation_metrics.csv")
    family = pd.read_csv(CSV / "spm_spme_comparison.csv")
    for frame, label in [(observer, "observer output"), (observer_metrics, "observer metrics"), (family, "SPM/SPMe comparison")]:
        assert_finite(frame, label)
    assert observer.soc_estimate.between(0, 1).all(), "Observer SOC left physical bounds"
    soc_rmse = observer_metrics.loc[observer_metrics.metric == "Observer SOC RMSE", "value"].iloc[0]
    voltage_rmse = observer_metrics.loc[observer_metrics.metric == "Observer voltage RMSE", "value"].iloc[0]
    assert soc_rmse < 0.05 and voltage_rmse < 0.03, "Observer baseline error exceeded acceptance limits"
    assert family.voltage_difference_V.abs().max() > 0, "SPM/SPMe comparison is empty or identical"
    print(f"Observer/model-family PASS: SOC RMSE {100 * soc_rmse:.3f} pp, voltage RMSE {1000 * voltage_rmse:.2f} mV, and finite SPM/SPMe comparison.")

    print("All completed research-stage acceptance checks passed.")


if __name__ == "__main__":
    main()
