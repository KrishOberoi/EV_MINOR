# Alignment with Submitted Minor-Project Report

Reference document: `EV_Battery_Minor_Report_Final.docx`

## Overall assessment

The current work is aligned with the report's title, research gap, model-selection discussion, and all three stated objectives. The implementation is still at the foundation stage. We have demonstrated the electrochemical-state motivation, but we have not yet implemented the balancing controller, degradation coupling, or hierarchical computation architecture.

The submitted document is primarily a midterm literature-review report. Its project schedule and project-details sections do not define a detailed software implementation. Therefore, the current staged Python/PyBaMM workflow is an implementation plan derived from the stated objectives and research gaps.

## Requirement matrix

| Report requirement | Current evidence | Status | Remaining work |
|---|---|---|---|
| Use a physics-based or reduced-order electrochemical model | Isothermal PyBaMM SPM with Chen2020 parameters | Aligned | Explain SPM selection versus DFN/SPMe in the final methodology |
| Use surface concentration and internal overpotential | Extracted average/surface particle concentration, gradients, and reaction overpotentials | Partially complete | Feed these states into an observer and balancing decision |
| Show cells with similar voltage but different internal state | Experiment 1 and controlled Experiment 1B | Demonstrated | Repeat over multiple histories for stronger statistics |
| Demonstrate different usable energy | Full-state continuation under common 5 A discharge | Demonstrated with limitation | Separate SOC effects from diffusion-history effects in later tests |
| Build electrochemical-state-informed active balancing | No controller yet | Not started | Implement voltage, SOC, and electrochemical balancing baselines |
| Couple SEI growth and capacity fade to balancing | No degradation model or cost function yet | Not started | Add SEI model, health state, and degradation penalty |
| Scale from 4–16 cells to 96s-class architecture | Only two independent cells currently | Not started | Build heterogeneous 4S pack, then architecture abstraction for 16 and 96 cells |
| Use event-triggered model updates | Not implemented | Not started | Compare periodic and event-triggered observer updates |
| Quantify computational budget | No runtime/update-count study yet | Not started | Report update counts and host runtime. Do not claim automotive-MCU testing |

## Strongest alignment so far

The report's first objective says that cells can appear identical in terminal voltage while having different internal lithium distribution profiles and usable energy reserves. The current simulations directly support this motivation:

- Uncontrolled history comparison: 1.848 mV voltage difference and 16.94 percentage-point SOC difference.
- Controlled history comparison: 0.568 mV voltage difference and 0.556 percentage-point SOC difference, while the positive-particle gradient differed by 480.77 mol m^-3.
- Full-state energy continuation: 7.044 Wh versus 10.112 Wh under a common 5 A discharge, with the important caveat that the first pair also had a large SOC difference.

## Important interpretation boundary

The current scripts use internal variables directly from the simulated PyBaMM solution. They are model truth outputs, not estimates reconstructed from measured voltage and current. The report's wording refers to an SPM or simplified-P2D observer, so the next implementation must add an explicit reduced-order observer or clearly label the current results as oracle-state demonstrations.

## MATLAB decision

The report does not require MATLAB. Python/PyBaMM is suitable for the electrochemical reference model and is more efficient for this project because it already provides SPM, DFN, particle-state, and degradation functionality. MATLAB can be added later for control-oriented plots, CSV verification, or Simulink demonstration if the supervisor requires it. A second full electrochemical implementation in MATLAB is not necessary for alignment.

## Next implementation order

1. Build a heterogeneous 4-series pack using four SPM-based cell simulations.
2. Add a conventional voltage-balancing baseline.
3. Add an SOC-balancing baseline.
4. Add the explicit reduced electrochemical observer and electrochemical-state score.
5. Compare balancing outcomes using SOC spread, voltage spread, balancing energy, and stress indicators.
6. Add SEI/capacity-loss state and degradation-aware cost.
7. Add hierarchical module/pack abstractions and event-triggered updates.
8. Evaluate 4, 16, 48, and 96-cell computational scaling on the host computer, while describing 32-bit automotive hardware as a representative budget rather than claiming hardware validation.
