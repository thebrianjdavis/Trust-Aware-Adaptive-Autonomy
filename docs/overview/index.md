# Project Overview

This project studies **trust-aware adaptive autonomy** in human-machine teaming
(HMT) resource allocation under uncertainty. It is a research prototype for
testing whether an autonomy system can correct reliance behavior while
preserving or improving team performance.

## Motivation

Human-machine teams can fail when trust is miscalibrated. A supervisor who
undertrusts an AI may ignore useful recommendations. A supervisor who
overtrusts it may accept poor recommendations too readily. In both cases, the
problem is not only whether the AI can produce a plan, but whether the team
relies on that plan appropriately.

The controller in this repository changes the **strength of the AI
recommendation**, rather than only changing the plan:

- stronger intervention when behavior suggests undertrust;
- weaker intervention when behavior suggests overtrust;
- minimally disruptive intervention when behavior is calibrated.

The long-term research direction is to identify when trust-aware autonomy
improves team behavior, when it improves task performance, and when those two
objectives diverge.

## Episode lifecycle

Each experiment repeats the following process:

1. Generate a disaster-response-inspired scenario.
2. Create a supervisor-oriented comparison plan with the baseline planner.
3. Create an uncertainty-aware plan with the AI planner.
4. Evaluate both plans under stochastic task outcomes.
5. Update a Bayesian estimate of AI helpfulness.
6. Compute an intervention score from confidence, trust, and behavior.
7. Map the score to weak, normal, or strong recommendation strength.
8. Let a simulated supervisor accept or override the AI plan.
9. Record utility, reliance behavior, recommendation strength, and trust.

The key distinction is that the AI does both planning and reliance regulation.
The two mechanisms remain separate in the implementation so their effects can
be studied independently.

## Scope

The framework supports:

- single-seed demonstrations;
- multi-seed Monte Carlo experiments;
- component ablation studies;
- scenario sensitivity analysis;
- aggregate and single-run visualizations;
- reproducibility metadata for each batch.

It does not claim to model human trust comprehensively. The current supervisor
policies are simulated, and the trust state is a machine-side estimate of
relative AI helpfulness.
