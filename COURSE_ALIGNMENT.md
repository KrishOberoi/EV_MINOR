# Course reference and independent algorithm boundary

The project uses the University of Colorado Boulder / Gregory Plett Coursera specialization **Algorithms for Battery Management Systems** as a methodological reference:

<https://www.coursera.org/specializations/algorithms-for-battery-management-systems>

The most relevant course is **Battery Pack Balancing and Power Estimation**:

<https://www.coursera.org/learn/battery-pack-balancing-power-estimation?specialization=algorithms-for-battery-management-systems>

## What we take from the public course scope

The public syllabus emphasizes:

- choosing a balancing setpoint,
- choosing when to trigger balancing,
- comparing passive and active balancing architectures,
- enforcing pack and electronics limits,
- calculating remaining energy and available power,
- using Octave/MATLAB scripts for pack-level simulation,
- and motivating future physics-based BMS algorithms.

These are appropriate foundations for our baseline design and evaluation metrics.

## What is independently developed in this repository

We are not reproducing or claiming ownership of the course templates. Our implementation develops its own research layer around a PyBaMM reference:

1. The reference cell model is an isothermal PyBaMM SPM with Chen2020 parameters.
2. The hidden-state experiment tests voltage matching against particle concentration gradients and overpotential.
3. The balancing prototype uses an explicit SOC/gradient/overpotential score and an ideal conservative transfer current.
4. The observer is a custom SPM-inspired voltage/current observer, not a copied course estimator.
5. The planned degradation extension will add SEI/capacity-loss cost.
6. The planned scalable extension will add hierarchical modules and event-triggered updates.

## Algorithm design rule

The course provides established BMS concepts and a useful baseline. It does not by itself make our algorithm novel. The research claim must come from a clearly specified algorithm, controlled comparisons, ablations, repeated scenarios, and comparison with prior work.

Our current defensible claim is therefore:

> A reproducible evaluation framework that extends conventional pack-balancing setpoint and trigger logic with electrochemical-state information, while explicitly measuring the trade-off between imbalance, balancing effort, stress, degradation, and computation.

The current repeated ablation experiment shows that the full electrochemical score is **not universally superior** to its reduced forms under the present prototype model. This is an important result. It prevents us from presenting the added terms as automatically beneficial and defines the next work: calibration, held-out scenarios, degradation coupling, and a full closed-loop validation.
