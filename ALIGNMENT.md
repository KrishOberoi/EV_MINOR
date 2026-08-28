# Alignment with Submitted Minor-Project Report

Reference document: `EV_Battery_Minor_Report_Final.docx`

## Overall assessment

The current work is aligned with the report's title, research gap, model-selection discussion, and all three stated objectives. The implementation now covers the electrochemical-state motivation, a first controller comparison, and observer cross-checks. Degradation coupling and hierarchical computation remain future stages.

The submitted document is primarily a midterm literature-review report. Its project schedule and project-details sections do not define a detailed software implementation. Therefore, the current staged Python/PyBaMM workflow is an implementation plan derived from the stated objectives and research gaps.

The recommended Algorithms for Battery Management Systems specialization is a suitable methodological reference for the balancing baseline and MATLAB/Octave workflow. Its public course alignment and the boundary between course concepts and our independent algorithm are recorded in [`COURSE_ALIGNMENT.md`](COURSE_ALIGNMENT.md).

## Requirement matrix

| Report requirement | Current evidence | Status | Remaining work |
|---|---|---|---|
| Use a physics-based or reduced-order electrochemical model | Isothermal PyBaMM SPM with Chen2020 parameters | Aligned | Explain SPM selection versus DFN/SPMe in the final methodology |
| Use surface concentration and internal overpotential | Extracted average/surface particle concentration, gradients, and reaction overpotentials; prototype score consumes gradient and overpotential signals | Partially complete | Integrate observer estimates into the controller feedback path |
| Show cells with similar voltage but different internal state | Experiment 1 and controlled Experiment 1B | Demonstrated | Repeat over multiple histories for stronger statistics |
| Demonstrate different usable energy | Full-state continuation under common 5 A discharge | Demonstrated with limitation | Separate SOC effects from diffusion-history effects in later tests |
| Build electrochemical-state-informed active balancing | Four-cell comparison of uncontrolled, voltage, SOC, and electrochemical-state controllers | Partially complete | Repeat across scenarios and add ablations before making a superiority claim |
| Couple SEI growth and capacity fade to balancing | No degradation model or cost function yet | Not started | Add SEI model, health state, and degradation penalty |
| Scale from 4–16 cells to 96s-class architecture | Heterogeneous 4S baseline and documented hierarchy plan | Partially complete | Build 16/48/96-cell abstractions and event-triggered study |
| Use event-triggered model updates | Not implemented | Not started | Compare periodic and event-triggered observer updates |
| Quantify computational budget | No runtime/update-count study yet | Not started | Report update counts and host runtime. Do not claim automotive-MCU testing |

## Verification evidence map

| Report requirement or public output | Public workflow/check | Observed evidence | Boundary |
|---|---|---|---|
| Single-cell SPM internal states | `single_cell_spm.py` + `validate_research_results.py` | 456 finite samples, 75-minute profile, dynamic voltage/SOC, nonzero particle gradient | PyBaMM model truth |
| Similar voltage, different internal state | `experiment_1_same_voltage.py` + validator | 1.848 mV voltage gap with 16.94 percentage-point SOC and gradient separation | Cross-time, SOC-confounded pair |
| Same-SOC history effect | `experiment_1b_equal_soc_history.py` + validator | 0.568 mV voltage gap, 0.556 percentage-point SOC gap, retained gradient difference | One controlled SPM scenario |
| Different usable energy | `experiment_1_same_voltage.py` + energy checks | 7.044 Wh versus 10.112 Wh; recomputed trapezoidal integral and common 2.5 V cutoff passed | SOC separation contributes to the result |
| Active balancing comparison | `balancing_comparison.py` + `verify_pack_invariants.py` + validator | Four controllers, conservative transfer, nonnegative energy, all active cases below uncontrolled final SOC spread | Reduced-order prototype, not closed-loop PyBaMM |
| Observer requirement | `observer_cross_validation.py` + validator | 3.185 percentage-point SOC RMSE, 14.24 mV voltage RMSE, bounded SOC estimate | Same-profile coefficient calibration; held-out test pending |
| Novelty robustness | `robustness_ablation.py` + validator | Three scenarios and six labels; score terms have observable but non-universal effects | No universal superiority claim |
| MATLAB portability | `matlab/validate_saved_results.m`, `plot_saved_results.m`, `run_reduced_pack_simulation.m` | Scripts added and documented; local runtime attempt blocked because MATLAB/Octave unavailable | MATLAB results not claimed as executed |

## Strongest alignment so far

The report's first objective says that cells can appear identical in terminal voltage while having different internal lithium distribution profiles and usable energy reserves. The current simulations directly support this motivation:

- Uncontrolled history comparison: 1.848 mV voltage difference and 16.94 percentage-point SOC difference.
- Controlled history comparison: 0.568 mV voltage difference and 0.556 percentage-point SOC difference, while the positive-particle gradient differed by 480.77 mol m^-3.
- Full-state energy continuation: 7.044 Wh versus 10.112 Wh under a common 5 A discharge, with the important caveat that the first pair also had a large SOC difference.

## Important interpretation boundary

The pack and history experiments use internal variables directly from the simulated PyBaMM solution. They are model truth outputs, not estimates reconstructed from measured voltage and current. A prototype SPM-inspired observer now exists, but it remains a separate cross-validation experiment and is not yet the feedback source for the balancing controller. Controller results must therefore state whether they use oracle/model-truth signals or observer estimates.

The source boundary is now recorded in [`MODEL_SOURCES.md`](MODEL_SOURCES.md): PyBaMM supplies the electrochemical reference, custom Python supplies the observer and controller logic, and MATLAB is supplementary. The prototype observer exists, but it has not yet been integrated as the controller's feedback source.

## MATLAB decision

The report does not require MATLAB, and a second full electrochemical implementation would add risk without strengthening the three-day evidence. Python/PyBaMM therefore remains the electrochemical reference model. MATLAB has now been added as a supplementary lane for independent CSV invariant checks, result plotting, and a transparent control-oriented 4-cell Thevenin 1-RC sanity simulation. This supports portability to MATLAB/Simulink without presenting the reduced-order model as a second SPM or DFN validation.

## Next implementation order

1. Build a heterogeneous 4-series pack using four SPM-based cell simulations. **Complete.**
2. Add a conventional voltage-balancing baseline. **Complete.**
3. Add an SOC-balancing baseline. **Complete.**
4. Add the explicit reduced electrochemical observer and electrochemical-state score. **Baseline complete.**
5. Compare balancing outcomes using SOC spread, voltage spread, balancing energy, and stress indicators. **Baseline complete.**
6. Add SEI/capacity-loss state and degradation-aware cost.
7. Add hierarchical module/pack abstractions and event-triggered updates.
8. Evaluate 4, 16, 48, and 96-cell computational scaling on the host computer, while describing 32-bit automotive hardware as a representative budget rather than claiming hardware validation.
