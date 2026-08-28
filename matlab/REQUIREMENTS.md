# MATLAB requirement and output traceability

This matrix separates contract-level verification from MATLAB runtime acceptance.

| Requirement | MATLAB entry point | Inputs | Changed public outputs | Concrete check | Observed status |
|---|---|---|---|---|---|
| Independently verify series-pack and balancing invariants | `validate_saved_results.m` | `four_cell_pack_trajectories.csv`, `four_cell_pack_summary.csv`, `four_cell_pack_cell_summary.csv`, `balancing_comparison_timeseries.csv`, `balancing_comparison_metrics.csv` | Console pass/fail result | MATLAB runtime assertions plus `experiments/validate_matlab_contract.py` source/output contract check | Contract passed; MATLAB runtime blocked locally |
| Recreate pack and controller figures | `plot_saved_results.m` | Pack trajectory and balancing metric CSVs | `matlab_python_pack_baseline.png`, `matlab_controller_metrics.png` | MATLAB output-name contract plus nonempty-output check after execution | Contract passed; MATLAB runtime blocked locally |
| Run a MATLAB-native reduced-order pack sanity simulation | `run_reduced_pack_simulation.m` | Hard-coded four-cell configuration matching the Python baseline | `matlab_reduced_pack_trajectories.csv`, `matlab_reduced_pack_summary.csv`, `matlab_reduced_pack.png` | MATLAB source contract plus post-run CSV/invariant checks when MATLAB is available | Contract passed; MATLAB runtime blocked locally |

## Contract-level result

The portable checker confirms that all three MATLAB entry points exist, expose the documented function names, reference the expected inputs, and contain every documented output name. This is useful integration evidence but is not a substitute for executing MATLAB.

## Runtime status

The actual MATLAB batch command was attempted on 2026-08-28. Neither `matlab` nor `octave` is installed in the current environment. Therefore, no MATLAB-generated numerical value or figure is claimed as executed. Run the documented commands on MATLAB Online or a licensed MATLAB installation to close the runtime portion of this matrix.
