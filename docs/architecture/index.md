# System Architecture

The system is a pipeline of small, interpretable components. Experiment
orchestration coordinates them but does not merge their responsibilities.

```mermaid
sequenceDiagram
    participant R as Experiment runner
    participant E as Environment
    participant P as Planners
    participant O as Outcome simulator
    participant T as Trust model
    participant A as Autonomy controller
    participant S as Supervisor

    loop Each episode
        R->>E: Generate incidents and assets
        E-->>R: Episode
        R->>P: Create baseline and AI plans
        P-->>R: Plans
        R->>O: Evaluate comparable outcomes
        O-->>R: Plan utilities
        R->>T: Compare AI and baseline utility
        T-->>R: Updated trust
        R->>A: Confidence + trust + override history
        A-->>R: Recommendation strength
        R->>S: AI plan and recommendation
        S-->>R: Accept or override
        R->>R: Record executed utility and metrics
    end
```

## Data flow

```mermaid
flowchart TD
    CFG[SimulationConfig and JSON overrides] --> GEN[Episode generator]
    FEMA[FEMA calibration distributions] --> GEN
    GEN --> EP[Episode]
    EP --> BASE[Baseline planner]
    EP --> AI[AI planner]
    BASE --> EVAL[Outcome evaluation]
    AI --> EVAL
    AI --> CONF[Confidence estimation]
    EVAL --> TRUST[Beta trust update]
    CONF --> CTRL[Autonomy controller]
    TRUST --> CTRL
    HISTORY[Acceptance and override history] --> CTRL
    CTRL --> POLICY[Supervisor policy]
    POLICY --> EXEC[Executed utility]
    EXEC --> OUT[Text, CSV, metadata, figures]
```

## Design properties

- **Modularity:** generation, planning, evaluation, trust, autonomy, and
  supervision can be tested independently.
- **Interpretability:** planners use greedy heuristics and the controller uses a
  transparent weighted score.
- **Reproducibility:** explicit seeds and resolved configuration values are
  written with multi-seed output.
- **Comparability:** paired conditions reuse seed structure to reduce
  uncontrolled variation.

Continue to [Components](components.md) for module-level responsibilities.
