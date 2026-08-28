"""Check the MATLAB source/output contract without claiming MATLAB execution.

This is a portable contract check. It verifies file names, function entry points,
expected inputs, and documented outputs. MATLAB runtime assertions remain the
actual acceptance check when a MATLAB installation is available.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATLAB = ROOT / "matlab"

CONTRACTS = {
    "validate_saved_results.m": {
        "entry": "function validate_saved_results()",
        "required": [
            "four_cell_pack_trajectories.csv",
            "four_cell_pack_summary.csv",
            "four_cell_pack_cell_summary.csv",
            "balancing_comparison_timeseries.csv",
            "balancing_comparison_metrics.csv",
            "pack_voltage_V",
            "balancing_current_A",
            "cell_current_A",
            "reconstructedSoc",
        ],
    },
    "plot_saved_results.m": {
        "entry": "function plot_saved_results()",
        "required": [
            "four_cell_pack_trajectories.csv",
            "balancing_comparison_metrics.csv",
            "matlab_python_pack_baseline.png",
            "matlab_controller_metrics.png",
        ],
    },
    "run_reduced_pack_simulation.m": {
        "entry": "function run_reduced_pack_simulation()",
        "required": [
            "matlab_reduced_pack_trajectories.csv",
            "matlab_reduced_pack_summary.csv",
            "matlab_reduced_pack.png",
            "four-cell",
            "capacityAh",
            "R0",
            "initialSoc",
        ],
    },
}


def main() -> None:
    for filename, contract in CONTRACTS.items():
        path = MATLAB / filename
        assert path.is_file(), f"Missing MATLAB entry point: {filename}"
        source = path.read_text()
        assert contract["entry"] in source, f"Missing function entry point in {filename}"
        for token in contract["required"]:
            assert token in source, f"Missing contract token {token!r} in {filename}"

    readme = (MATLAB / "README.md").read_text()
    requirements = (MATLAB / "REQUIREMENTS.md").read_text()
    for filename in CONTRACTS:
        function_name = filename[:-2]
        assert function_name in readme and filename in requirements, f"Undocumented MATLAB script: {filename}"
    assert "MATLAB runtime blocked locally" in requirements
    assert "not yet executed here" in readme

    print("MATLAB contract PASS: 3 entry points, documented inputs, outputs, and runtime limitation verified.")
    print("MATLAB runtime acceptance remains blocked because no MATLAB or Octave executable is installed locally.")


if __name__ == "__main__":
    main()
