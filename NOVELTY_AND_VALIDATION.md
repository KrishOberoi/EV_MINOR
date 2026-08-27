# Novelty and Cross-Verification Plan

## Honest novelty assessment

The project is not novel merely because it uses active cell balancing, SOC balancing, model predictive ideas, or degradation-aware balancing. These topics already have substantial prior art.

Relevant prior work identified during the literature check includes:

1. **Fraccaroli et al., “To Balance or to Not? Battery Aging-Aware Active Cell Balancing for Electric Vehicles,” arXiv:2401.03124 (2024).** This work formulates wear-leveling-aware active balancing, includes aging impact, and studies when balancing should be triggered.
   - https://arxiv.org/abs/2401.03124
2. **Shreasth et al., Scientific Reports (2025), “A novel active lithium-ion cell balancing method based on charging and discharging state of power in electric vehicles.”** This work compares voltage/SOC strategies with a State-of-Power strategy, uses UKF estimation, MATLAB/Simulink, a four-cell experiment, and a 96-series architecture.
   - https://doi.org/10.1038/s41598-025-96581-8
3. **“A fast active balancing strategy based on model predictive control for lithium-ion battery packs,” Energy (2023).** This demonstrates that optimization/MPC-based active balancing is already established.
   - https://www.sciencedirect.com/science/article/pii/S0360544223014226

Therefore, the project must not claim that active balancing, SOC-aware balancing, MPC, or aging-aware balancing is individually new.

## Defensible project contribution

The current defensible contribution is a reproducible simulation study that integrates several elements and makes their trade-offs explicit:

- SPM particle surface/average concentration and overpotential signals used as balancing information.
- A controlled same-SOC, different-history experiment that isolates electrochemical memory more clearly than a simple SOC-mismatch example.
- A comparison of voltage, SOC, and electrochemical-state balancing on the same heterogeneous four-cell pack.
- A proposed path from cell-level electrochemical signals to degradation-aware and event-triggered hierarchical computation.
- Open scripts, generated data, plots, assumptions, and limitations in a staged Git history.

This should be presented as an **integrated, reproducible minor-project framework** unless a deeper systematic literature review demonstrates a narrower algorithmic gap.

## Candidate novelty claim, pending verification

A potentially defensible narrow contribution is:

> An SPM-informed balancing score that combines SOC error, particle surface-average concentration gradient, and reaction overpotential, evaluated together with degradation cost and event-triggered hierarchical computation under a common reproducible benchmark.

This is a candidate contribution, not yet a verified novelty claim. It must be compared directly against SPM/ROM balancing, SoP-based balancing, wear-leveling-aware balancing, and MPC literature.

## Cross-verification protocol

### A. Numerical invariants

Every run should verify:

- Series cells receive the same external pack current.
- The ideal balancing current satisfies `sum(u_i) = 0` at every time step.
- Pack voltage equals the sum of cell voltages.
- SOC update agrees with signed coulomb counting.
- Balancing energy is nonnegative and uses the stated efficiency convention.
- No state or safety limit is silently violated.
- CSV outputs contain no missing or non-finite values.

### B. Model cross-checks

1. Compare SPM mass conservation against integrated electrode flux.
2. Run SPM and SPMe on selected profiles and report voltage error and state differences.
3. Run a low-order independent RC/gradient model and compare qualitative ordering of the controllers.
4. Repeat profiles at different time steps to check numerical convergence.

### C. Controller cross-checks

Use exactly the same initial states, pack current, cell parameters, balancing-current limits, and stopping criteria for:

- No balancing
- Voltage balancing
- SOC balancing
- Electrochemical-state balancing
- Later degradation-aware balancing

Report final and peak SOC spread, voltage spread, usable energy, balancing energy, number of events, stress, and capacity loss.

### D. Robustness and ablation

Repeat across multiple initial SOC distributions, capacity deviations, resistance deviations, pulse rates, rest times, and electrochemical-score weights. Include ablations that remove the gradient or overpotential term. A result that only appears for one hand-selected scenario should be treated as illustrative, not general.

### E. Literature comparison

The final report should compare the proposed framework against the criteria used in prior work:

- Balancing criterion: voltage, SOC, SoP, electrochemical state, or degradation cost.
- Model: ECM, SPM/ROM, DFN/P2D, or empirical.
- Estimator: coulomb counting, EKF, UKF, or direct model state.
- Balancing architecture: passive, cell-to-cell, cell-to-pack, or pack-to-cell.
- Objective: imbalance, usable capacity, energy loss, aging, computation, or a combination.
- Validation: simulation only, independent model, hardware, or real pack.


## Verification results added on 2026-08-27

- Independent pack/controller invariant checks passed after correcting a PyBaMM cycle-boundary timestep issue.
- The explicit observer was tested with a 5 percentage-point initial SOC bias and 2 mV seeded voltage noise.
- Observer SOC RMSE was 3.185 percentage points and observer voltage RMSE was 14.24 mV.
- SPM versus SPMe voltage RMSE was 34.02 mV and maximum difference was 56.74 mV.
- The observer coefficients were calibrated on the same reference trajectory, so this is a baseline cross-check rather than held-out validation. Held-out profiles remain required.

The project is aligned with a real research gap, but its novelty is currently in the **integration, controlled evaluation, and reproducibility** rather than a proven entirely new balancing principle. We will narrow or revise the claim if literature or cross-validation shows that the same score and architecture already exist.
