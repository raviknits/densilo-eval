# Densilo 0.6.1 regression evaluation

This author-operated development evaluation targets four previously observed token regressions. The final codec factors repeated text and identifiers while preserving complete JSON rows. It uses no compression LLM or Headroom runtime code.

| Workload | Fewer total tokens than Headroom token mode | Second development seed |
|---|---:|---:|
| Code repair | 4.17% | 3.90% |
| Research conflicts | 68.92% | 70.27% |
| Session freshness | 5.55% | 5.79% |
| Structured lookup | 5.65% | 5.33% |

Each cell covers six trials; all candidate trials were correct. The candidate also used fewer total tokens than Headroom cache mode in all four workloads on both seeds. Across the full ten-family comparison, Densilo answered 60/60 correctly and used 128,176 total tokens: 13.66% fewer than Headroom token mode and 12.75% fewer than cache mode. The second seed adds 24/24 correct candidate trials. There are 456 completed observations across comparator arms, three repetitions per task, no infrastructure-invalid outcomes and no missing usage. Client and wire usage reconcile.

- [Full six-arm comparison](accepted/REPORT.md) and [machine-readable results](accepted/summary.json).
- [Second-seed four-arm comparison](accepted-fresh/REPORT.md).
- [42 explicit regression checks](regression-gate.json).
- [Wheel hash and source verification](artifact-verification.json). The independently supplied candidate wheel is not published in this evaluation repository.

## Limits and development history

These are already-seen synthetic families, and both seeds were used during development. They are not independent customer holdouts. Failed CSV and constant-column variants were rejected after arithmetic, ranking and extra-answer-field failures; detailed development attempts remain in the local engineering evidence bundle. A quota-interrupted run was excluded in full before restarting with unchanged frozen code after credits became available. Prompts, expected answers and graders were unchanged.

Aggregation used 19.1% more raw tokens than the previous Densilo release, with 6/6 correct versus 5/6. The six initial request bodies were identical after JSON parsing; later model decisions and extra rounds account for the difference. Overall family-bootstrap intervals for tokens-per-correct improvement versus Headroom cache/token still include zero. No claim of consistent customer superiority, paid net savings, or enterprise qualification is made.

The task files and frozen source hashes are included for reproduction. Cached input is a subset of input; output includes reasoning. Provider counters are not invoices.
