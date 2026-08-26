# Project Report: Mathematical Modelling of Lithium-Ion Battery Packs

## Project scope

The project investigates electrochemical-state- and degradation-informed active cell balancing using reduced-order models and hierarchical computation. The implementation is intentionally staged so that each objective produces independently demonstrable evidence.

## Status

- **Step 1 complete:** single-cell isothermal Single Particle Model (SPM) baseline in PyBaMM.
- **Step 2 next:** two cells with different current histories and a search for nearly equal terminal voltage with different internal states.
- 4-cell balancing, degradation-aware control, and scalability analysis are not implemented yet.

## Step 1 method

A PyBaMM SPM with the Chen2020 lithium-ion parameter set was simulated. The current profile was:

1. Discharge at 1C for 20 minutes
2. Rest for 10 minutes
3. Discharge at 0.5C for 20 minutes
4. Rest for 10 minutes
5. Charge at 0.5C for 10 minutes
6. Rest for 5 minutes

The output period was 10 seconds. The cell began at 80% SOC. SOC in the mixed discharge/charge profile is calculated using signed coulomb counting, so discharge decreases SOC and charge increases SOC.

## Quantities recorded

- Terminal voltage and current
- SOC
- Average and surface lithium concentration in each representative electrode particle
- Surface-minus-average concentration gradients
- Negative and positive electrode reaction overpotentials

## Observations

- The simulation completed with 456 time points over 75 minutes.
- Voltage ranged from 3.503 V to 3.945 V.
- SOC reached a minimum of 30.0% during the discharge sequence and recovered to 38.3% after the charge step.
- Concentration gradients were approximately -910.7 to 455.3 mol m^-3 in the negative particle and -3183.1 to 7400.8 mol m^-3 in the positive particle.
- The gradients were close to zero at the initial state and became nonzero during current operation. This confirms that surface lithium concentration is not always equal to average particle lithium concentration.
- The total electrode reaction overpotential varied from approximately -97.2 mV to 58.6 mV.

## Conclusions so far

1. The SPM provides internal electrochemical variables that are unavailable from terminal voltage alone.
2. Current transients create concentration gradients and overpotentials, so terminal voltage should be interpreted as a dynamic response rather than a complete measurement of cell state.
3. The SPM is a practical baseline for this project because it exposes the states needed for later electrochemical balancing while remaining much less computationally expensive than a DFN/P2D model.
4. These results are model-based baseline evidence. They are not yet observer estimates from noisy voltage/current measurements.

## Project-specific novel finding

The first measurable finding for this project is the explicit separation of average particle lithium concentration from surface concentration in the simulation. This gives a concrete state variable for testing whether voltage-based balancing can falsely classify cells as balanced. It should be described as a project result, not as a claim that the underlying electrochemical phenomenon is newly discovered.

## Reproducibility

```bash
cd ~/EV_MINOR
source .venv/bin/activate
python experiments/single_cell_spm.py
```

Generated evidence:

- `results/csv/single_cell_spm_timeseries.csv`
- `results/plots/single_cell_spm_states.png`
- `results/plots/single_cell_spm_voltage.png`

## Experiment log

| Date | Experiment | Result | Decision |
|---|---|---|---|
| 2026-08-26 | Single-cell SPM baseline | Successful, 456 points, no missing CSV values | Proceed to two-cell history comparison |

## Experiment 1: same voltage, different internal state

### Method

Two nominally identical Chen2020 SPM cells were simulated independently with different initial SOCs and different current histories. The analysis searched all cross-time pairs after 5 minutes of operation and selected a pair with terminal-voltage difference no greater than 2 mV while maximizing separation in SOC and internal state indicators.

- **Cell A:** initial SOC 60%; 1C discharge, rest, 0.5C charge, rest, 0.5C discharge, rest.
- **Cell B:** initial SOC 65%; 0.5C discharge, rest, 1C discharge, rest, 0.5C discharge, rest.

The comparison is cross-time rather than same-clock-time. This is deliberate: it asks whether two cells can arrive at an almost identical measured voltage through different histories.

### Measured result

| Quantity | Cell A | Cell B | Difference |
|---|---:|---:|---:|
| Terminal voltage | 3.756962 V | 3.755114 V | **1.848 mV** |
| SOC | 43.89% | 60.83% | **16.94 percentage points** |
| Negative surface-average gradient | 286.45 mol m^-3 | -454.21 mol m^-3 | 740.66 mol m^-3 |
| Positive surface-average gradient | 928.42 mol m^-3 | 2539.09 mol m^-3 | 1610.67 mol m^-3 |
| Total overpotential | 55.57 mV | -55.28 mV | 110.85 mV |

The selected points occurred at 15.67 minutes for Cell A and 5.00 minutes for Cell B. Both trajectories had already experienced load before the comparison.

### Observation

A voltage-only balancing rule would treat these cells as balanced because their voltage difference is below the 2 mV threshold. The model states show that they are not equivalent: their SOC differs by nearly 17 percentage points, their particle concentration gradients differ, and their total overpotentials have opposite signs.

### Conclusion

Experiment 1 supports the central motivation for electrochemical-state-informed balancing: terminal voltage is not a sufficient standalone indicator of internal cell state during dynamic operation. The SPM exposes differences that would be invisible to a voltage threshold controller.

### Project-specific novel finding

For the chosen histories, the simulation produced a voltage-matched pair with a 1.848 mV voltage difference but a 16.94 percentage-point SOC difference and a 110.85 mV overpotential difference. This is a strong project result demonstrating hidden state separation. It is a simulation finding under the Chen2020 SPM assumptions, not a claim of general experimental validation or fundamental scientific novelty.

### Remaining part of Experiment 1

The next addition is a fair usable-energy comparison. The matched electrochemical states should be continued from their full internal state vectors under the same discharge current until a common voltage cutoff. Using only the matched SOC values would erase the concentration-gradient information, so the continuation must preserve the complete PyBaMM state.

## Updated experiment log

| Date | Experiment | Result | Decision |
|---|---|---|---|
| 2026-08-26 | Single-cell SPM baseline | Successful, 456 points, no missing CSV values | Proceed to two-cell history comparison |
| 2026-08-26 | Experiment 1 voltage-state comparison | 1.848 mV voltage difference with 16.94 percentage-point SOC difference | Proceed to full-state usable-energy comparison |
