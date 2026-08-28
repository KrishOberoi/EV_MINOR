# Mathematical Modelling of Lithium-Ion Battery Packs

Step 1 implements a single-cell Single Particle Model (SPM) simulation in PyBaMM.

## Setup

```bash
cd ~/EV_MINOR
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python experiments/single_cell_spm.py
```

```bash
python experiments/experiment_1_same_voltage.py
```

Experiment 1 simulates two cells with different histories, finds a pair within a 2 mV voltage threshold, preserves their full electrochemical states, and compares their usable discharge energy under a common load.

```bash
python experiments/experiment_1b_equal_soc_history.py
```

This controlled experiment keeps initial SOC and total discharge equal while changing pulse order, helping isolate electrochemical memory from SOC imbalance.

```bash
python experiments/four_cell_pack.py
```

This builds a four-series heterogeneous pack with a common series current and records the pre-balancing voltage and SOC spread.

```bash
python experiments/balancing_comparison.py
```

This compares uncontrolled, voltage-based, SOC-based, and electrochemical-state balancing using a control-oriented reduced-order perturbation layer calibrated against the PyBaMM pack reference.

See [`MODEL_SOURCES.md`](MODEL_SOURCES.md) for the exact division between PyBaMM, custom Python, and MATLAB. In particular, the present controller comparison is a reduced-order prototype rather than a closed-loop PyBaMM PDE simulation.

## MATLAB cross-check lane

MATLAB is supplementary rather than a duplicate electrochemical implementation. The Python/PyBaMM SPM remains the reference model. MATLAB provides independent CSV invariant checks, plots, and a transparent 4-cell Thevenin 1-RC sanity simulation.

MATLAB is not installed in the current development environment, so these commands are prepared but not yet executed here:

```matlab
cd matlab
validate_saved_results
plot_saved_results
run_reduced_pack_simulation
```

See [`matlab/README.md`](matlab/README.md) for the model boundary and reporting rules. Do not combine the MATLAB reduced-order numbers with PyBaMM SPM numbers without labelling the model source.

```bash
python experiments/observer_cross_validation.py
```

This validates the explicit SPM-inspired voltage/current observer against PyBaMM SPM truth and compares SPM voltage against SPMe on the same profile.



- `results/csv/single_cell_spm_timeseries.csv`
- `results/plots/single_cell_spm_states.png`
- `results/plots/single_cell_spm_voltage.png`

```bash
python experiments/verify_pack_invariants.py
```

This independently checks the saved pack and balancing CSV files for conservation, current decomposition, SOC propagation, and metric consistency.

The model is intentionally small and transparent. It is the baseline that later degradation and hierarchical-computation experiments will extend.
