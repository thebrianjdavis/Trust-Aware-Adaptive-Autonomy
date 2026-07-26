# Components

## Environment

`src/environment/` contains the core dataclasses and episode generator. An
episode contains incidents, response assets, task windows, durations,
priorities, success probabilities, and capability requirements.

## Planners

The baseline planner sorts incidents by priority and uses a first-fit feasible
assignment strategy.

The AI planner ranks incidents by expected utility density:

\[
\operatorname{score}_i =
\frac{\operatorname{priority}_i \, p_i}{\operatorname{duration}_i}
\]

It also considers compatible-asset scarcity and latest finish time. Both
planners are deliberately interpretable rather than globally optimal.

## Outcome simulator

Plan assignments are evaluated under stochastic outcomes. Utility is the sum
of priorities for successfully completed assignments:

\[
U = \sum_i \operatorname{priority}_i \mathbb{1}(Y_i = 1)
\]

Assignment-sensitive adjustments account for capability compatibility and
schedule quality before sampling outcomes.

## Confidence estimator

The confidence estimator aggregates assignment-level signals into a bounded
plan confidence score. It is separate from realized utility: confidence is
available before outcomes, while utility is observed afterward.

## Trust model

The Beta trust model records whether the AI plan outperformed the baseline and
exposes the posterior mean and variance.

## Adaptive autonomy controller

The controller converts confidence, trust, and supervisor behavior into an
intervention score and a recommendation-strength label. Ablation modes allow
signals to be enabled independently.

## Supervisor policies

Undertrust, calibrated, and overtrust policies map the current signals and
recommendation strength to an acceptance probability.

## Experiment runner

The runner composes all components across episodes and returns an
`ExperimentRunSummary`. The command-line entry point adds batch execution,
configuration overrides, tabular aggregation, metadata, and visualization.
