# Findings and Interpretation

Current Monte Carlo experiments suggest that behavior-aware adaptive autonomy
changes simulated supervisor reliance in the intended direction:

- undertrust conditions tend to receive stronger intervention;
- overtrust conditions tend to receive weaker intervention;
- calibrated conditions remain comparatively stable.

Utility effects are scenario-dependent. Overtrust correction can improve
utility by reducing excessive AI reliance. Undertrust correction is more
sensitive to AI reliability and task difficulty because increasing reliance on
an imperfect planner does not necessarily improve outcomes.

The emerging research claim is:

> Adaptive autonomy can robustly regulate reliance behavior, but performance
> gains depend on AI reliability and scenario conditions.

## Reading the measures

Acceptance deltas indicate how adaptation changes reliance. Utility deltas
indicate how that behavior affects performance. Recommendation distributions
show the controller's mechanism, while final trust and trust variance describe
its estimate of relative AI helpfulness.

No one measure is sufficient by itself. A sound interpretation connects:

1. controller output;
2. supervisor reliance;
3. executed utility;
4. scenario conditions.

## Limitations

1. Supervisor behavior is simulated rather than human-subject based.
2. Priority is modeled rather than derived from FEMA data.
3. Success probabilities use Beta distributions rather than learned outcome
   labels.
4. Both planners are interpretable heuristics, not globally optimized solvers.
5. Trust is a machine-side estimate of helpfulness, not a full psychological
   model.
6. FEMA data grounds incident types and durations but not operational success.

These limits are intentional for controlled mechanism evaluation, but they
bound claims about real human-machine teams.

## Future work

- broader task-density and uncertainty sensitivity analysis;
- human-subject validation of supervisor behavior models;
- learned or optimized planning strategies;
- alternative trust updates based on executed outcomes;
- dynamic supervisor policies;
- expanded geospatial or multimodal response data;
- statistical testing and effect-size reporting;
- cross-configuration sensitivity summaries.

## Reporting guidance

Publications should include the study mode, scenario, resolved configuration,
number of episodes and seeds, seed range, supervisor policies, autonomy modes,
and output metadata. Results are simulation-based evidence and should not be
presented as human-subject validation.
