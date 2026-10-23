# Site risk scoring: foundation status

**No score is calculated in this phase.** `risk_score` is JSON `null`, and the UI
shows **Not assessed**. Missing analysis must never become a zero score, a low-risk
classification or a claim that the site is safe.

## Requirements for the next phase

Before implementing a formula, define supported visible hazards and measurable
evidence, then document a versioned, deterministic mapping from reviewed evidence
to severity/exposure inputs and score bands. Select weights and thresholds only
after examining the chosen model's outputs and representative photographs.

The methodology must specify:

- Hazard definitions, evidence references and duplicate-hazard handling.
- What can be seen in the photograph versus user-provided or missing context.
- Severity and exposure assumptions; do not treat model confidence as severity.
- Missing/unclear evidence behavior and cases where scoring is unavailable.
- Formula, weights, score range, risk bands and worked examples.
- Model, guidance-source and scoring versions so results are reproducible.
- Supervisor review/override records and reasons, preserving original results.

Keep distinct states for **analysis unavailable**, **insufficient evidence**, and
**no supported hazard detected**. The last state still does not mean the site is
safe. A future score is a prototype assessment, not a validated safety certification.

This document records scoring constraints; it does not claim that the mentor's
risk-scoring requirement has already been implemented or validated.
