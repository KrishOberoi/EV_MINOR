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

The running report is maintained in `REPORT.md`.

The Step 1 script writes:

- `results/csv/single_cell_spm_timeseries.csv`
- `results/plots/single_cell_spm_states.png`
- `results/plots/single_cell_spm_voltage.png`

The model is intentionally small and transparent. It is the baseline that later pack, balancing, degradation, and hierarchical-computation experiments will extend.
