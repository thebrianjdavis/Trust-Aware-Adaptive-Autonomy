# Study Design

The framework supports standard comparisons and component ablations in both
single-seed and multi-seed modes.

## Standard study

The standard study compares:

1. `fixed`, which always uses normal recommendation strength;
2. `adaptive`, which uses confidence, trust, and behavior.

Each autonomy condition is evaluated with undertrust, calibrated, and
overtrust supervisor modes.

## Ablation study

The ablation study compares:

1. `fixed`;
2. `confidence_trust`;
3. `behavior_only`;
4. `adaptive`.

This design tests whether supervisor behavior feedback is necessary for
reliance calibration and whether its effect differs by supervisor mode.

## Evaluation measures

The experiment runner records:

- AI wins, baseline wins, and ties;
- AI acceptances and overrides;
- weak, normal, and strong recommendations;
- executed utility;
- AI confidence;
- override rate and intervention score;
- final trust and trust variance.

Multi-seed aggregation reports means, standard deviations, standard errors, and
95% confidence intervals. Paired delta files compare adaptive modes with the
fixed condition by seed and supervisor mode.

## Experimental unit

An episode is one generated planning problem followed by a supervisor decision
and outcome execution. A seed-level result summarizes many episodes for one
supervisor and autonomy condition. A multi-seed batch is the primary unit for
aggregate analysis.

!!! warning "Evidence scope"

    These are simulation studies with modeled supervisor policies. They support
    mechanism evaluation but do not substitute for human-subject validation.
