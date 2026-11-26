# Known CI issues

General `cubrid-tcr` CLI usage, verdict definitions, signature syntax, and blocker commands live in the standalone `cubrid-tcr` skill (`cubrid-tc-registry/skills/cubrid-tcr/SKILL.md`). This reference defines how `cubrid-ci-analyze` and personal CUBRID workflows integrate `cubrid-tcr`.

## Check each failure

1. For testcase failures, take the suite directory collected by `cubrid-ci` (holding `summary.json` and `failures/`). Index its run in Chronicle first per [Index the current run once](ci-evidence.md#index-the-current-run-once) so `--record` can match occurrences.
2. Check the whole suite directory in one call:

```bash
cubrid-tcr --json check --ci-attempt "$SUITE_DIR" --record
```

If `rerun.mode` is `carried_forward`, check the source attempt named in `rerun` instead. For `history.status == "NOT_INDEXED"` or `history.freshness` `STALE`/`UNKNOWN`, report the history as incomplete rather than "no earlier failures".
3. For a job-level failure without testcase records, run `cubrid-tcr --json check --job "$JOB_NAME" --engine "$ENGINE_SHA"` using the shard's tested Engine SHA.
4. Apply the report label below, citing the rule ID, issue, and `reason`, and keep every failure in the failure inventory.

| Verdict | Report label |
|---|---|
| `no_match` | Analyze as usual. |
| `known` | "Known issue, not caused by this PR." Do not analyze its root cause or propose a fix. |
| `known_job` | "Known noisy job." Keep the failure in the inventory, compare its symptom with the merge base, and analyze any symptom the rule's `not_covered` text does not describe. |
| `fix_missing` | Known issue. Tell the user that the tested branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | Do not apply the rule. Analyze the failure as new. Tell the user that the issue may need to be reopened, and cite the run and the stack. |
| `expired` | Do not apply the rule. Tell the user to retire or extend it. |
| `unknown` | Known issue, with the `reason` that the state is unknown. If the reason is a missing stack or failure text, get it and check again. |

When `cubrid-tcr show "$TC_PATH" --suite "$SUITE"` returns a `sync_hint` naming a date window, record the gap in one line instead of running it. If `cubrid-tcr` is not installed or exits `2`, record the limitation and analyze as usual.

## Record what the analysis learned

Run these before handoff (`cubrid-ci-analyze` requires this step; skip only if `cubrid-tcr` is absent or exits `2` and record the limitation):

- Recurring unmatched failure (`record.result == "no_single_match"` with no candidates): add a signature with `signature add` (use `--suite sql` for `test_sql_by_cci` failures), then rerun `check --ci-attempt "$SUITE_DIR" --record`.
- Unconfirmed related issue: `cubrid-tcr link "$TC_PATH" --suite "$SUITE" --issue CBRD-n --relation suspected`.
- Useful fact for future readers: `cubrid-tcr note "$TC_PATH" --suite "$SUITE" --body "..." --ref ...`.
- Recurring failure not caused by this PR with no covering rule: propose `rule add` as below without approving it.

## Add a known-issue rule

1. Confirm duplicate issues with `cubrid-jira-dup candidate-find`; the user confirms the issue.
2. Run `cubrid-tcr rule add` without `--yes` and show the output to the user.
3. Only after explicit user approval, rerun with `--yes --approved-by <user>` and verify with `check`.
4. When a verdict looks stale, run `cubrid-tcr rules --audit` and report its flags to the user to decide on retirement or extension.

## Track blockers, culprits, and unblock readiness

When a root cause and fix target are identified, register or update a first-class blocker (`cubrid-tcr blocker add` / `blocker pr add`) and inspect readiness via `cubrid-tcr blockers --affected-days 7` or `cubrid-tcr unblock --pr <PR_NUMBER>`.

- **Loose coupling with `work-tracker`**: when a work item waits on a CI blocker, record `wait-for:<KEY>` (matching a `wait_keys` value such as `CBRD-28395` or `tc-4474`) in its `work-tracker` note rather than mirroring PR/JIRA state into `work-tracker`.
