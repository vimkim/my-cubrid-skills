# Decide repair approval and completion boundaries

Type: grilling
Label: wayfinder:grilling
Status: resolved
Assignee: codex
Parent: ../map.md
Blocked by: none

## Question

Confirm the candidate skill name, whether fix approval covers retries within the same diagnosis and scope, whether approved pushes lead to monitoring and CI triggering until all checks pass, and whether creating a new focused runner belongs in this effort. Then resolve any evidence-dependent workflow decisions exposed by the audits.

## Comments

The four initial questions were sent to the user on 2026-09-08; answers are pending. The user already confirmed that this map includes implementation.

## Answer

User accepted all four recommendations: name cubrid-ci-fix; retry automatically within the approved diagnosis and scope; monitor and trigger CI after an approved push until all required checks pass; use existing focused runners and propose a separate framework only if needed. Implementation is included. Scope changes require renewed fix review; each new push requires approval.
