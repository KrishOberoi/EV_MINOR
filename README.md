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

The script writes:

- `results/csv/single_cell_spm_timeseries.csv`
- `results/plots/single_cell_spm_states.png`
- `results/plots/single_cell_spm_voltage.png`

The model is intentionally small and transparent. It is the baseline that later pack, balancing, degradation, and hierarchical-computation experiments will extend.
