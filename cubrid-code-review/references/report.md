# Review report contract

Save the report with the pinned snapshot. Use full revision SHAs in metadata. Use commit-specific source links when available. Otherwise use paths, line numbers, symbols, and the recorded SHA. Keep logs in the evidence directory.

## Report contents

Start with the user's review goal and the most consequential result. Then include the following information.

### Verdict and follow-up

Use one verdict:

| Verdict | Meaning |
|---|---|
| `changes-required` | At least one confirmed defect requires a change. |
| `no-confirmed-findings` | No confirmed defect remains, and all applicable planned coverage is complete. |
| `incomplete` | Required analysis or evidence remains. |
| `needs-budget` | The budget gate prevented reviewer execution. |

Confirmed defects take precedence over `incomplete`. Keep coverage status separate, so `changes-required` can also have incomplete coverage. State `Follow-up review required` as `yes` or `no`. Explain the reason. Identify whether unresolved work must precede merge or is optional evidence.

### Confirmed findings

Order findings by impact. Use the following priorities:

- `P0` requires immediate action for a demonstrated critical failure with broad reach.
- `P1` covers high-impact defects such as reachable data loss, corruption, isolation failures, crashes, or severe availability loss.
- `P2` covers other demonstrated correctness or material performance defects.
- `P3` covers low-impact defects that still have a concrete consequence.

For each finding, include the reviewer contract's candidate fields after adjudication. Give the shortest source location that shows the defect. State whether verification was dynamic or static. Describe the missing test as missing evidence, not as proof of a defect.

### Coverage and verification

Link `coverage.md`. Include every changed path or a clearly enumerated path group. Each row records its reviewer, invariant, evidence, result, and remaining action. Record not-applicable domains with their reasons.

List checks actually run, with their exact commands, revisions, configuration, exit status, and artifact paths. Distinguish passed, failed, inconclusive, and not-run checks. A build failure from missing dependencies does not establish a defect in the PR.

State unavailable source, missing specifications, untested configurations, reviewer dropouts, and unexamined interleavings. Record PR movement separately from the snapshot findings. Avoid a numeric completeness percentage unless its denominator is defined.

### Open questions and rejected candidates

Keep unproven risks separate from confirmed findings. Give each open question an owner and the check that would resolve it. Record significant rejected candidates with the source or experiment that disproved them. Summarize duplicate candidates under their accepted root cause.

Separate pre-existing defects from findings attributed to the reviewed change. Link them only when the evidence supports their relevance.

### Budget accounting

Record the budget mode, requested limits, enforcement mechanism, actual agent count, and allocation by assignment. Separate measured usage, estimates, and unknown usage. Include coordinator usage and continuation work. State whether percentage compliance is verified, unverified, or violated.

Do not claim compliance merely because all reviewers returned short reports. Do not omit incomplete coverage to make a budget-limited review appear complete.

## Handoff contents

Create `handoff.md` when follow-up review is required. Write a self-contained brief for a fresh coordinator. Include these items:

1. The user's goal and the exact reason this review stopped.
2. Repository, PR URL when present, comparison mode, full base and head SHAs, merge-base SHA when used, and patch hash when applicable.
3. Report, manifest, coverage, evidence, specification, and policy locations.
4. Confirmed findings and unresolved questions with stable IDs. Include disagreements and failed reproduction attempts.
5. Inspected scope and the precise remaining paths, invariants, configurations, or delta revisions.
6. Next commands and required environment. Include build and testcase identities, containment requirements, and existing runtime resource ownership.
7. The remaining budget and its measurement status. State which new work requires a new allocation. Reuse of an assignment does not reset its ceiling.
8. A proposed focused assignment for each unresolved question and its completion condition.
9. Conditions for finishing the review, including revalidation of changed source and affected callers after a fix.

For a changed PR, keep the old snapshot intact. Pin the new base and head before reviewing the delta. Revisit affected invariants beyond the new hunks. Preserve stable finding IDs when their root causes remain the same.

End the handoff with a resumable request that names this skill, the manifest path, the pinned scope, and the unresolved IDs. A handoff authorizes no new spending or publication by itself.
