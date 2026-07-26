# Trust and Reliance

The project distinguishes an internal estimate of AI helpfulness from the
supervisor's observable reliance behavior.

## Machine-side trust estimate

Trust is represented by a Beta-Bernoulli model. After each episode, AI utility
is compared with baseline utility:

- if AI utility is greater, increment \(\alpha\);
- if baseline utility is greater, increment \(\beta\);
- if the utilities tie, leave the posterior unchanged.

The posterior mean is the trust score:

\[
T = \frac{\alpha}{\alpha + \beta}
\]

The model estimates whether the AI is likely to improve performance relative
to the baseline. It is not intended as a complete psychological model of human
trust.

## Observable reliance

The simulated supervisor makes reliance visible through two outcomes:

- **acceptance** executes the AI plan;
- **override** executes the baseline plan.

The controller computes a smoothed override rate:

\[
\hat{o} = \frac{n_\text{override} + a_0}
{n_\text{accept} + n_\text{override} + a_0 + b_0}
\]

Smoothing avoids extreme behavior signals at the beginning of a run when few
observations are available.

## Supervisor policies

| Policy | Modeled behavior |
|---|---|
| `undertrust` | Rejects AI recommendations too often |
| `calibrated` | Conditions reliance more appropriately on confidence and trust |
| `overtrust` | Accepts AI recommendations too often |

Each policy converts confidence, trust, and recommendation strength into an
acceptance probability. These policies are experimental instruments, not
validated human-subject models.

## Calibration versus performance

Reliance calibration and task performance are related but distinct outcomes.
Increasing AI acceptance under undertrust is behaviorally corrective only when
the AI is useful in that scenario. Similarly, reducing acceptance under
overtrust can improve utility when the baseline avoids unreliable AI plans.
