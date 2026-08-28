# Model-source architecture

This document defines which tool produces each result in the project. It prevents the electrochemical reference model, custom controller logic, and MATLAB sanity checks from being described as one implementation.

## Data flow

```text
Current profile and cell parameters
                |
                v
       Python + PyBaMM SPM/SPMe
       electrochemical reference
                |
                +--> voltage, SOC, particle concentration,
                |    gradients, overpotentials
                |
                +--> saved CSV truth trajectories
                              |
                 +------------+-------------+
                 |                          |
                 v                          v
       Custom Python observer         Custom Python controller
       voltage/current estimates       comparison layer
                 |                          |
                 +------------+-------------+
                              v
                    metrics and research plots
                              |
                              v
                 MATLAB verification and plots
                 MATLAB 1-RC sanity simulation
```

## Responsibility matrix

| Layer | Tool | What it does | Evidence status |
|---|---|---|---|
| Electrochemical reference | Python + PyBaMM | Solves SPM and selected SPMe trajectories and exposes particle states | Executed |
| Experiment orchestration | Custom Python | Defines current profiles, histories, state matching, energy continuation, and CSV export | Executed |
| 4-cell pack baseline | Python + PyBaMM | Runs four independent SPM cells with a common series current and heterogeneous parameters | Executed |
| Balancing comparison | Custom Python | Applies ideal balancing currents through a first-order control-oriented perturbation layer calibrated against the pack reference | Executed, prototype only |
| Observer | Custom Python | Estimates SOC, gradient-related states, and effective voltage drop from voltage/current using a reduced-order correction model | Executed, prototype only |
| Verification | Custom Python | Recomputes conservation, current, SOC, and metric invariants from saved CSV files | Executed and passed |
| MATLAB cross-check | MATLAB | Reads saved CSV files, independently checks invariants, and recreates figures | Scripts added, runtime pending |
| MATLAB sanity model | MATLAB | Simulates a transparent heterogeneous 4-cell Thevenin 1-RC pack | Script added, runtime pending |

## Critical interpretation boundaries

1. **PyBaMM outputs are model truth, not measurements.** Particle concentration and overpotential values taken directly from a PyBaMM solution are available for evaluating the observer and for demonstrating hidden-state behaviour.
2. **The observer is custom Python.** It uses terminal voltage and current as its measurement inputs, while PyBaMM states are retained as reference truth for error calculation.
3. **The current balancing comparison is not a closed-loop PyBaMM solve.** PyBaMM generates the common reference trajectories. A control-oriented first-order perturbation layer propagates the additional balancing-current effect. It demonstrates the controller architecture and metrics, but it is not yet definitive full-PDE controller validation.
4. **MATLAB is not a second electrochemical truth model.** The MATLAB 1-RC script is deliberately lower order and has separate output names. Its values must not be merged with PyBaMM SPM values without model-source labels.
5. **Degradation is not implemented yet.** No current result should be described as SEI-aware or capacity-fade-aware balancing.

## Mentor-safe description

> PyBaMM supplies the physics-based electrochemical reference trajectories. Custom Python code implements the experiments, reduced observer, balancing logic, metrics, and independent verification. MATLAB has been added as a supplementary cross-check and lower-order pack-simulation environment, not as a duplicate SPM or DFN solver.
