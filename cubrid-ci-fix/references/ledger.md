# Durable repair record

Keep one effort index at `/home/vimkim/gh/my-cubrid-docs/<ticket-or-pr>/ci-fix/pr-<number>/index.md`. Use a known lowercase CBRD ticket, or `pr-<number>` when no ticket exists. Reuse a matching record after validating repository and PR URL; preserve unrelated work. Do not publish the docs repository without approval.

Store snapshots and local attempts under that directory with full engine SHA, run/job ID, attempt and unique local attempt number in their identity. Retain raw evidence in the collector's durable data directory or a separate API bundle and link it. Never overwrite a previous attempt with a later success. Avoid signed artifact URLs, tokens and credential-bearing remote URLs.

The index carries current PR/head, source and testcase checkout identities, current stage, outstanding approval, next action and links to snapshots. Its inventory must account for:

| Record | Required fields |
|---|---|
| Runtime occurrence | Suite, job/run, attempt, node, full TC path or unresolved identifier, result, engine SHA, testcase repository/revision evidence, logs/diff/source links |
| Miscellaneous/job failure | Check context/app, run/job/step, attempt, tested head/base/merge identity, conclusion and log link |
| Diagnosis | Observed signature, inferred cause, confidence, PR relationship, falsifier/next observation, affected inventory rows |
| Fix proposal | Repositories/files, intended behavior, proposed changes and verification plan |
| Approval | User response, approved scope and proposal version; renewed approval when scope changes |
| Local attempt | Source SHA plus diff identity, test SHA plus diff identity, configuration/fixtures, binary/build identity, command, selected/actual case set, counts, result, logs and setup limits |
| Publication | Reviewed diff/commits, approved destinations, push receipts, remote SHAs, TC branch selection, trigger comment/head receipt |

Use dispositions such as `observed`, `analyzed`, `awaiting-fix-approval`, `fixing`, `locally-verified`, `awaiting-push-approval`, `pushed-awaiting-ci`, `remote-passed`, `blocked`, `superseded`, and `accepted-outside-scope`. Local verification never silently advances a row to remote-passed.

Group causes separately from occurrence identity. The same test name on another node, configuration or attempt remains an individual occurrence. Failed/error/unknown totals must reconcile with raw results; skipped tests and job failures without test output get explicit records. Append history as attempts change, including failed reproductions and user decisions. Keep the next actionable step visible for another session.
