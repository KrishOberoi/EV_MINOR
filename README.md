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



- `results/csv/single_cell_spm_timeseries.csv`
- `results/plots/single_cell_spm_states.png`
- `results/plots/single_cell_spm_voltage.png`

The model is intentionally small and transparent. It is the baseline that later pack, balancing, degradation, and hierarchical-computation experiments will extend.
