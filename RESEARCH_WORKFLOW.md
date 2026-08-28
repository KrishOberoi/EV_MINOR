# Research Workflow

This repository is maintained as a staged research project rather than as a disposable collection of scripts.

## Versioning policy

- Each completed experiment is committed separately.
- Existing scripts, CSV files, plots, and report entries are retained unless a correction is explicitly documented.
- Corrections receive their own commit and do not erase the earlier history.
- Every experiment should be reproducible from a command in `README.md`.

## Evidence policy

For each experiment, record:

1. Research question or hypothesis
2. Model assumptions and parameter set
3. Controlled and varied quantities
4. Measured metrics
5. Observations
6. Conclusions supported by the data
7. Limitations and possible confounding factors
8. The next experiment needed to reduce uncertainty

## Interpretation policy

The project distinguishes between:

- **Model outputs:** internal variables directly available from the PyBaMM solution.
- **Observer estimates:** internal states reconstructed from voltage, current, and temperature measurements.
- **Engineering demonstrations:** simulation results showing why a controller may be useful.
- **Scientific novelty claims:** claims that require comparison with published work or experimental validation.

The current voltage-matched experiments are model-based engineering demonstrations. They support the project motivation but are not presented as experimental validation or as proof of fundamental scientific novelty.

The model-source boundary is maintained in `MODEL_SOURCES.md`. PyBaMM reference states, observer estimates, reduced-order controller outputs, and MATLAB sanity-model outputs must remain separately labelled in research tables and conclusions.

## Current research sequence

| Stage | Question | Evidence status |
|---|---|---|
| Single-cell SPM | Can the selected model expose electrochemical internal states? | Complete |
| Voltage-matched histories | Can similar voltage hide different internal states? | Complete |
| Full-state energy continuation | Does the hidden state produce different usable energy under common load? | Complete, with SOC confounding documented |
| Controlled same-SOC histories | Does history still change internal state when SOC is nearly equal? | Complete, supporting evidence |
| Heterogeneous 4S pack | Does cell mismatch create pack-level voltage and SOC spread? | Complete, pre-balancing baseline |
| Balancing comparison | Which controller reduces imbalance most effectively? | Complete baseline, further repeated scenarios required |
| Acceptance verification | Do the completed public workflows satisfy their explicit result requirements after a fresh run? | Complete: requirement-traced checker and edge/integration checks passed |
| Robustness and score ablation | Do electrochemical score terms change controller outcomes across heterogeneity scenarios? | Complete baseline study: terms have observable but non-universal effects |
| MATLAB cross-check lane | Can saved invariants and pack-level trends be checked in a second environment? | Scripts added, execution pending MATLAB availability |
| Degradation-aware balancing | Can balancing reduce ageing cost as well as imbalance? | Planned |
| Hierarchical computation | Can the approach scale with event-triggered updates? | Planned |

## Researcher responsibilities for the remaining work

Before accepting a claimed controller improvement, we will ensure that:

- All controllers see the same initial pack and current profile.
- Balancing energy and converter efficiency are accounted for consistently.
- Baseline and proposed controllers use clearly stated information sets.
- Results are compared over repeated scenarios rather than one favorable run where practical.
- Simulation limitations are stated explicitly in the report.
