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

### Usable-energy continuation result

The two matched points were continued from their preserved full PyBaMM state vectors under the same 5 A discharge until the model voltage cutoff of 2.5 V.

| Quantity | Cell A | Cell B | Difference |
|---|---:|---:|---:|
| Usable discharge energy | 7.044 Wh | 10.112 Wh | **3.068 Wh** |
| Discharge duration | 25.71 min | 35.97 min | 10.26 min |
| Final voltage | 2.500 V | 2.500 V | common cutoff |

At the start of the common discharge, the applied load immediately produced different voltage responses: approximately 3.610 V for Cell A and 3.719 V for Cell B. This reflects the fact that the cells had different internal states even though their pre-discharge terminal voltages were within 2 mV.

### Interpretation and limitation

The energy difference is a useful engineering consequence of the voltage-matched state difference, but it must not be attributed solely to concentration gradients. The selected pair also differed by 16.94 percentage points in SOC, so SOC separation is a major contributor to the 3.068 Wh energy difference. A follow-up controlled experiment should hold SOC nearly equal while varying recent current history, or compare several matched pairs, to isolate the contribution of diffusion gradients and overpotential.

### Updated conclusion

The complete Experiment 1 evidence is now:

1. Two cells can have terminal voltages within 2 mV while their electrochemical state estimates differ substantially.
2. When the same load is applied, their immediate voltage response, time to cutoff, and usable discharge energy can differ substantially.
3. Full-state continuation is necessary for this test. Reinitializing only from SOC would discard the concentration profile and would not be a valid test of electrochemical memory.

### Updated project-specific novel finding

Under the stated Chen2020 SPM assumptions and selected histories, a 1.848 mV pre-load voltage difference corresponded to a 3.068 Wh difference in subsequent usable energy under a common 5 A discharge. Because SOC was also different, this is a project-specific demonstration of the limitation of voltage-only classification, not an isolated measurement of diffusion-gradient effects.

## Updated experiment log

| Date | Experiment | Result | Decision |
|---|---|---|---|
| 2026-08-26 | Single-cell SPM baseline | Successful, 456 points, no missing CSV values | Proceed to two-cell history comparison |
| 2026-08-27 | Experiment 1 voltage-state comparison | 1.848 mV voltage difference with 16.94 percentage-point SOC difference | Proceed to full-state usable-energy comparison |
| 2026-08-27 | Experiment 1 full-state energy continuation | 3.068 Wh usable-energy difference under a common 5 A discharge | Proceed to controlled same-SOC history comparison or 4-cell pack model |
