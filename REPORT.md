# Project Report: Mathematical Modelling of Lithium-Ion Battery Packs

## Project scope

The project investigates electrochemical-state- and degradation-informed active cell balancing using reduced-order models and hierarchical computation. The implementation is intentionally staged so that each objective produces independently demonstrable evidence.

## Status

- **Single-cell and hidden-state experiments complete:** isothermal SPM baselines in PyBaMM, including uncontrolled and controlled same-SOC history comparisons.
- **4-cell baseline and first controller comparison complete:** heterogeneous pack, voltage/SOC/electrochemical-state controller baselines, and independent invariant checks are available.
- **Observer cross-check complete at prototype level:** an SPM-inspired voltage/current observer and SPM-versus-SPMe comparison are documented.
- **Next:** held-out observer testing, degradation-aware balancing, and hierarchical/event-triggered computation.

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

## Controlled Experiment 1B: same SOC, different history

### Motivation

The first energy comparison demonstrated a practical consequence but the selected cells differed substantially in SOC. To separate SOC imbalance from electrochemical memory, both cells were initialized at 60% SOC and given the same total discharge. Only the ordering of the high- and low-rate current segments was changed.

### Result

The analysis searched for a pair satisfying both a voltage difference below 2 mV and an SOC difference below 1 percentage point.

| Quantity | Cell A | Cell B | Difference |
|---|---:|---:|---:|
| Terminal voltage | 3.593880 V | 3.594447 V | **0.568 mV** |
| SOC | 50.278% | 49.722% | **0.556 percentage points** |
| Negative surface-average gradient | -720.73 mol m^-3 | -751.40 mol m^-3 | 30.67 mol m^-3 |
| Positive surface-average gradient | 4691.40 mol m^-3 | 4210.64 mol m^-3 | **480.77 mol m^-3** |
| Total overpotential | -91.43 mV | -91.47 mV | 0.04 mV |

The matched points occurred at 6.83 minutes for Cell A and 12.17 minutes for Cell B. The cells had identical model parameters and equal initial SOC, but their current histories were ordered differently.

### Observation

Even after controlling SOC to within 0.556 percentage points and voltage to 0.568 mV, the positive-particle surface-average concentration gradients remained different by approximately 481 mol m^-3. This shows that recent current history can leave a measurable internal diffusion state difference that is not represented by voltage or SOC alone.

### Conclusion

This controlled result strengthens the case for including electrochemical state variables in a balancing decision. It is a cleaner demonstration than the original pair because SOC is approximately equal. The difference is smaller than in the unconstrained experiment, so the report should present it as supporting evidence rather than claiming that voltage is always inadequate by a fixed amount.

### Limitation

The result comes from one pair of current-history orderings and one SPM parameter set. A stronger study should repeat the search over multiple pulse amplitudes, rest times, and initial SOC values, then report distributions rather than one selected pair.

## Four-cell heterogeneous pack baseline

### Method

A four-series pack was assembled from four independent isothermal Chen2020 SPM simulations. Because series-connected cells carry the same physical current, every cell was driven by the same absolute current profile rather than a cell-specific C-rate:

1. Discharge at 2.5 A for 20 minutes
2. Rest for 10 minutes
3. Discharge at 1.25 A for 20 minutes
4. Rest for 10 minutes

The cells were intentionally heterogeneous:

| Cell | Initial SOC | Capacity | Contact resistance |
|---|---:|---:|---:|
| Cell 1 | 80% | 5.00 Ah | 12 mOhm |
| Cell 2 | 76% | 4.90 Ah | 15 mOhm |
| Cell 3 | 72% | 4.70 Ah | 22 mOhm |
| Cell 4 | 78% | 4.95 Ah | 10 mOhm |

Cell 3 represents the weakest or most aged cell in this baseline configuration.

### Baseline result before balancing

- Peak cell-voltage spread: **90.71 mV** at 12.5 minutes.
- Final cell-SOC spread: **9.60 percentage points**.
- Final pack voltage: **15.079 V**.
- Final cell voltages ranged from 3.727 V to 3.803 V.
- Cell 3 finished with the lowest SOC, lowest voltage, and highest contact resistance.

### Observation

The series pack is constrained by the weakest cell. Without balancing, the initial SOC and parameter mismatch accumulates into a voltage and SOC spread during the common-current drive cycle. This gives us a quantitative pre-balancing baseline against which voltage-, SOC-, and electrochemical-state balancing can be compared.

### Modelling limitation

This is a pack-level aggregation of independently solved SPM cells, not yet a power-electronics simulation. The pack current is common to all cells, while balancing currents and converter losses will be added in the next controller stage. Thermal coupling, tab-level effects, and series-parallel topology are intentionally outside this baseline.

## First balancing-controller comparison

### Method

The four-cell baseline was used as a common reference trajectory. Three controllers were compared with an uncontrolled case:

- **Uncontrolled:** no balancing current.
- **Voltage:** transfer 0.25 A from the highest-voltage cell to the lowest-voltage cell when the voltage range exceeded 5 mV.
- **SOC:** transfer 0.25 A from the highest-SOC cell to the lowest-SOC cell when the SOC range exceeded 0.5 percentage points.
- **Electrochemical:** select donor and receiver using a normalized score combining SOC, positive-particle surface-average gradient, and total overpotential.

The controller layer applied additional currents `u_i` such that the ideal transfer satisfied `sum(u_i) = 0`. The same pack current, initial conditions, and cell parameters were used for every controller.

### Results

| Controller | Final SOC spread [percentage points] | Final voltage spread [mV] | Balancing energy [Wh] | Events |
|---|---:|---:|---:|---:|
| Uncontrolled | 9.596 | 75.538 | 0.000 | 0 |
| Voltage | 2.734 | **4.369** | 1.521 | 290 |
| SOC | **0.769** | 23.866 | 1.897 | 364 |
| Electrochemical | 0.927 | 27.288 | 1.897 | 364 |

### Observations

- All active controllers reduced the final SOC spread relative to the 9.596 percentage-point uncontrolled case.
- Voltage control produced the smallest final voltage spread, which is expected because voltage was its direct feedback variable.
- SOC control produced the smallest final SOC spread.
- The electrochemical controller produced a final SOC spread close to the SOC controller while using nearly the same ideal balancing-energy budget in this first tuning.

### Interpretation and limitation

This is a control-oriented reduced-order comparison, not yet a closed-loop re-solve of the full PyBaMM PDE state after every balancing-current action. The PyBaMM pack trajectories provide the reference electrochemical signals, while a first-order perturbation model propagates the effect of `u_i` on SOC, gradient, and overpotential. Therefore, the table demonstrates controller architecture and metric definitions, but it should not yet be presented as definitive proof that the electrochemical controller is superior. The next refinement is to drive the controller with observer estimates and cross-check its balancing actions against full-state PyBaMM stepping.

### Research conclusion

The initial comparison shows the expected multi-objective trade-off: voltage control is best at suppressing voltage spread, SOC control is best at equalizing SOC, and the electrochemical controller provides a physically informed compromise. This supports the report's objective of comparing balancing decisions using more than a single terminal-voltage threshold.

## Research novelty and cross-verification position

### Course methodology reference

The project uses the public syllabus of Gregory Plett's University of Colorado Boulder Coursera specialization, especially *Battery Pack Balancing and Power Estimation*, as a methodological reference for balancing setpoints, balancing triggers, active-balancing architecture, remaining-energy calculation, and MATLAB/Octave pack simulation. The reference is recorded in `COURSE_ALIGNMENT.md`.

The course establishes the baseline BMS concepts but does not by itself define our research contribution. Our independent layer is the integration of PyBaMM internal electrochemical signals, a custom observer/controller prototype, repeated scenario testing, and planned degradation/computation extensions. Course materials or templates must not be presented as our original algorithm.

### Literature check

The project does not claim that active balancing, SOC-based balancing, MPC, or degradation-aware balancing is individually novel. Prior work already covers optimization-based active balancing, aging-aware or wear-leveling-aware balancing, and State-of-Power-based balancing. In particular, Fraccaroli et al. study aging-aware active balancing and balancing triggers, while Shreasth et al. (Scientific Reports, 2025) study a SoP-based strategy using a four-cell experiment, UKF estimation, MATLAB/Simulink, and a 96-series architecture.

### Defensible contribution

The defensible contribution is an integrated and reproducible simulation framework that combines SPM particle-state signals, controlled same-SOC history experiments, heterogeneous four-cell balancing comparisons, and a planned degradation-aware and event-triggered hierarchy. This is an integration and evaluation contribution unless a deeper literature review establishes a narrower algorithmic difference.

### Cross-verification completed

An independent verification script, `experiments/verify_pack_invariants.py`, recomputes checks from the saved CSV files rather than calling the simulation functions. It verified:

- Common external current through the series cells.
- Pack voltage equal to the sum of cell voltages.
- Zero net ideal balancing current at every time point.
- Correct decomposition `cell current = pack current + balancing current`.
- SOC propagation from the applied cell current and capacity.
- Reconstruction of the reported final SOC and voltage spread metrics.
- Non-missing and finite output data.

### Remaining verification

The controller comparison currently uses a control-oriented perturbation layer calibrated against PyBaMM reference trajectories. Although a prototype observer has now been evaluated separately, it is not yet the feedback source for the balancing controller. The controller must next be cross-checked against full-state PyBaMM stepping with observer-driven feedback. Timestep sensitivity, controller ablations, and repeated parameter scenarios are also required before making a general performance or novelty claim.

## Observer and model-family cross-validation

### Observer method

An explicit SPM-inspired observer was added in `experiments/observer_cross_validation.py`. It uses only terminal voltage and current as online measurements. Its state consists of SOC, negative and positive particle surface-average concentration gradients, and an effective voltage-drop state. Prediction uses coulomb counting and first-order state propagation. A voltage residual then corrects the predicted states.

The observer was initialized with a deliberately biased SOC of 65% while the SPM reference started at 70%. A 2 mV Gaussian voltage noise sequence was applied using a fixed random seed.

### Observer result

| Metric | Result |
|---|---:|
| SOC RMSE | 0.03185 fraction, or 3.185 percentage points |
| Voltage RMSE | 14.24 mV |
| Positive-gradient RMSE | 273.37 mol m^-3 |
| Effective voltage-drop RMSE | 24.92 mV |

The observer remains bounded between 17.62% and 64.98% SOC in this test and provides a usable first observer baseline. Its concentration estimate is less accurate than its SOC estimate, which is expected because terminal voltage does not uniquely identify the full particle concentration profile.

### SPM versus SPMe result

The same current profile and initial SOC were simulated with both PyBaMM SPM and SPMe models:

- Voltage RMSE: **34.02 mV**.
- Maximum voltage difference: **56.74 mV**.

This quantifies the approximation introduced by selecting SPM instead of SPMe for the rapid project study. It also reinforces that the SPM results should not be described as universally valid at all C-rates.

### Validation limitation

The first-order observer coefficients were calibrated from the SPM reference trajectory before testing. This is a useful prototype and a transparent baseline, but it is not a fully independent validation. The next observer version should use coefficients identified from separate training profiles and be tested on unseen profiles. A formally derived EKF or UKF should be treated as future work rather than claimed here.

## Acceptance verification of completed stages

The documented public Python workflows were executed again from the repository root on 2026-08-28. All seven commands completed successfully: the single-cell SPM, both hidden-state experiments, the four-cell pack, the balancing comparison, the observer/model-family cross-check, and the independent invariant checker.

The requirement-traced checker `experiments/validate_research_results.py` then passed all completed-stage assertions:

| Stage | Concrete observed check |
|---|---|
| Step 1 SPM | 456 finite samples over 75 minutes, dynamic voltage/SOC, and nonzero positive-particle gradient |
| Experiment 1 | 1.848 mV voltage gap, 16.94 percentage-point SOC gap, and 3.068 Wh energy gap |
| Controlled history | 0.568 mV voltage gap, 0.556 percentage-point SOC gap, and retained gradient separation |
| 4-cell pack | Four cells, common-current invariant, 90.71 mV peak spread, and 9.60 percentage-point final SOC spread |
| Balancing | Four controllers, zero-net transfer, nonnegative energy, and lower final SOC spread for every active controller than uncontrolled |
| Observer/SPM-SPMe | 3.185 percentage-point SOC RMSE, 14.24 mV voltage RMSE, bounded observer SOC, and finite model-family comparison |

Additional integration and edge checks passed: dependency check, imports, Python compilation, local Markdown links, deterministic single-cell rerun, strict timestamps, no duplicate boundaries, signed charge SOC increase, rectangular pack/controller grids, required artifact existence, and CSV finiteness. The acceptance checker initially exposed an incorrect Step 1 column name; this was corrected and the complete checker then passed. This correction is recorded as a positive feedback-loop result rather than hidden.

MATLAB acceptance was attempted through its documented batch interface, but neither MATLAB nor Octave is installed in the current environment. MATLAB runtime results therefore remain externally blocked and are not claimed in this report.

## Robustness and electrochemical-score ablation

To test whether the proposed electrochemical score is more than a hand-selected single-case result, `experiments/robustness_ablation.py` was run on three pack configurations: the baseline pack, a shifted-SOC pack, and a pack with stronger capacity and resistance mismatch. The full score was compared with versions that removed the gradient term, removed the overpotential term, or retained SOC only.

| Scenario | Uncontrolled final SOC spread [pp] | Full score [pp] | No gradient [pp] | No overpotential [pp] |
|---|---:|---:|---:|---:|
| Baseline | 9.596 | 0.927 | **0.769** | 0.883 |
| Capacity/resistance mismatch | 11.090 | 2.166 | **2.111** | **2.111** |
| SOC shift | 15.596 | **5.277** | **5.277** | **5.277** |

### Observation

All active variants reduced final SOC spread relative to their uncontrolled scenario, but the full SOC/gradient/overpotential score was not the best variant in these tests. The no-gradient variant performed better in the baseline and capacity/resistance cases, while all variants tied in the SOC-shift case.

### Research conclusion

The ablation does **not** verify a universal performance advantage for the combined electrochemical score. It does show that the added terms can change decisions and outcomes, which justifies keeping them as research variables. The defensible claim remains an integrated evaluation framework, not a proven superior algorithm. Weight calibration, held-out profiles, degradation cost, and closed-loop PyBaMM validation are still required.

## MATLAB cross-validation lane

MATLAB was added as a supplementary analysis environment rather than as a duplicate full electrochemical solver. The Python/PyBaMM SPM remains the reference implementation because it directly provides the particle concentration and electrochemical variables required by the research objectives.

The complete model-source definition is maintained in [`MODEL_SOURCES.md`](MODEL_SOURCES.md). In summary, PyBaMM provides electrochemical reference trajectories; custom Python implements orchestration, observer, controller, metrics, and verification; MATLAB provides a supplementary CSV cross-check and a separate 1-RC sanity simulation.

The `matlab/` directory contains three scripts:

1. `validate_saved_results.m` independently recomputes pack and controller invariants from the committed CSV files.
2. `plot_saved_results.m` recreates pack and controller figures from the saved outputs.
3. `run_reduced_pack_simulation.m` runs a transparent four-cell Thevenin 1-RC model with the same initial heterogeneity and current profile as the Python pack baseline.

The portable preflight `experiments/validate_matlab_contract.py` verifies all three MATLAB entry points, their documented input files, their changed output names, and the runtime limitation text. This contract check passed. It is source and integration evidence only, not MATLAB numerical execution.

The reduced-order MATLAB model is a control-oriented sanity simulation, not an independent SPM, DFN, or degradation validation. Its values must therefore be reported separately from the PyBaMM values. MATLAB is not installed in the current development environment, so these scripts are prepared for execution on a MATLAB-equipped machine and are currently marked as pending execution. The first MATLAB run should check qualitative ordering and conservation before any parameter calibration or quantitative cross-model comparison is attempted.


| Date | Experiment | Result | Decision |
|---|---|---|---|
| 2026-08-26 | Single-cell SPM baseline | Successful, 456 points, no missing CSV values | Proceed to two-cell history comparison |
| 2026-08-27 | Experiment 1 voltage-state comparison | 1.848 mV voltage difference with 16.94 percentage-point SOC difference | Proceed to full-state usable-energy comparison |
| 2026-08-27 | Experiment 1 full-state energy continuation | 3.068 Wh usable-energy difference under a common 5 A discharge | Proceed to controlled same-SOC history comparison |
| 2026-08-27 | Experiment 1b controlled same-SOC history comparison | 0.568 mV voltage difference and 0.556 percentage-point SOC difference with a 480.77 mol m^-3 positive-particle gradient difference | Proceed to 4-cell heterogeneous pack and balancing controllers |
| 2026-08-27 | Four-cell heterogeneous pack baseline | 90.71 mV peak voltage spread and 9.60 percentage-point final SOC spread before balancing | Implement baseline balancing controllers |
| 2026-08-27 | First balancing-controller comparison | Voltage control reached 4.369 mV final voltage spread; SOC control reached 0.769 percentage-point final SOC spread; electrochemical control reached 0.927 percentage-point final SOC spread | Refine controller with explicit observer and full-state feedback |
| 2026-08-27 | Independent pack/controller invariant verification | Common current, pack-voltage summation, zero-net transfer, current decomposition, SOC propagation, and metric reconstruction all passed | Proceed to full-state observer cross-check |
| 2026-08-27 | SPM-inspired observer and SPM/SPMe cross-check | Observer SOC RMSE 3.185 percentage points; SPM-SPMe voltage RMSE 34.02 mV; all outputs finite | Use held-out profiles and improve observer before final controller claims |
| 2026-08-27 | MATLAB cross-validation lane | Added independent CSV checks, plotting, and a transparent 1-RC pack sanity model; MATLAB execution pending local availability | Run on MATLAB-equipped machine and keep model-source labels separate |
