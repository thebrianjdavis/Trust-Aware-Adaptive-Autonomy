# Adaptive Autonomy

The adaptive controller combines three normalized signals:

- AI plan confidence \(C\);
- machine-side trust estimate \(T\);
- centered supervisor behavior signal \(B\).

The full intervention score is

\[
I = w_c C + w_t T + w_o B
\]

and is clamped to \([0, 1]\).

## Behavior signal

The supervisor's smoothed override rate is centered around a configurable
target. High override rates indicate undertrust-like behavior and produce a
positive signal. Low override rates indicate overtrust-like behavior and
produce a negative signal.

## Recommendation strength

The score is mapped to an interpretable label:

| Score range | Recommendation |
|---|---|
| Below the weak threshold | `weak` |
| Between thresholds | `normal` |
| Above the strong threshold | `strong` |

Recommendation strength modifies the supervisor policy's probability of
accepting the AI plan. It does not change the plan or force an outcome.

## Controller modes

The ablation design exposes four modes:

| Mode | Active signals |
|---|---|
| `fixed` | No adaptation; always uses normal strength |
| `confidence_trust` | Confidence and trust |
| `behavior_only` | Supervisor override behavior |
| `adaptive` | Confidence, trust, and behavior |

These modes support a direct test of whether behavioral feedback contributes
information beyond estimates of AI quality.

!!! note "Interpretability"

    The planner, trust update, controller score, recommendation mapping, and
    supervisor decision are separate modules. This separation makes each
    intermediate quantity inspectable in experiment output.
