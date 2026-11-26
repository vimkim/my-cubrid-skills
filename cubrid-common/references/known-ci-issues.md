# Known CI issues

`cubrid-tcr` holds per-testcase knowledge: failure signatures, issue links, notes, and known-issue rules. Chronicle (`cubrid-tcc`) supplies the failure history. Before you attribute a CI failure to the PR, check each failure with `cubrid-tcr`.

## Check each failure

1. For testcase failures, take the suite directory that `cubrid-ci` collected, the one that holds `summary.json` and `failures/`. Index its run once, as [Index the current run once](ci-evidence.md#index-the-current-run-once) describes. `--record` needs the run in Chronicle.
2. Check every failure of that directory with one command:

```bash
cubrid-tcr --json check --ci-attempt "$SUITE_DIR" --record
```

It reads each failure's testcase path, shard, tested Engine SHA from the shard build provenance, and `message.txt`, which holds any CTP `CORE ANALYZER` stacks. It applies the testcase's rules and the rules of the shard's job. For a `test_sql_by_cci` failure, it applies the matching `sql` testcase signature rules and the job rules, so the failure needs no second call. For such a failure, it skips Chronicle history (`history.available` is false) and `--record` writes nothing. `failures[]` has one entry per failure with `identity`, `verdict`, `hits`, `reason`, `stack_found`, and `history` counts. `--record` tags the occurrence when exactly one signature matches its stack; `record.result` says what happened. If the output has `rerun.mode` `carried_forward`, the attempt ran no cases; check the source attempt named in `rerun` instead.

If an entry's `history.status` is `NOT_INDEXED`, Chronicle has not indexed that testcase run, and the text output says `NOT_INDEXED` with its freshness. If `history.freshness` is `STALE` or `UNKNOWN`, the text output appends it to the counts. In both cases, report the history as incomplete. Do not read the counts as "no earlier failures".

3. For a job-level failure without testcase records, check the job name with the shard's tested Engine SHA. A workflow `head_sha` is not enough.

```bash
cubrid-tcr --json check --job "$JOB_NAME" --engine "$ENGINE_SHA"
```

When a rule's issue is resolved `Fixed` or `Done` in Jira, `check` tests whether the fix commit is in the tested Engine SHA and answers `fix_missing` or `fix_present`. It reads fix commits from `origin/develop` of `$TCR_ENGINE_REPO`. If it exits 2 and names that variable, pass `--engine-repo` with a local `CUBRID/cubrid` checkout.

4. Apply the label for the `verdict` from the table below. Cite the rule id, the issue, and the `reason`.
5. Keep every failure in the failure inventory, whatever its verdict. Still analyze every other failure in the same job.

| Verdict | Report label |
|---|---|
| `no_match` | Analyze as usual. |
| `known` | "Known issue, not caused by this PR." Do not analyze its root cause or propose a fix. |
| `known_job` | "Known noisy job." Keep the failure in the inventory, compare its symptom with the merge base, and analyze any symptom the rule's `not_covered` text does not describe. |
| `fix_missing` | Known issue. Tell the user that the tested branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | Do not apply the rule. Analyze the failure as new. Tell the user that the issue may need to be reopened, and cite the run and the stack. |
| `expired` | Do not apply the rule. Tell the user to retire or extend it. |
| `unknown` | Known issue, with the `reason` that the state is unknown. If the reason is a missing stack or failure text, get it and check again. |

Each entry's `history` counts earlier failures by branch and signature. Report it as history context. History context does not prove a root cause or PR causality. `cubrid-tcr show "$TC_PATH" --suite "$SUITE"` prints the full testcase view with related issues and notes. If that view's `sync_hint` names a date window, record the gap in one line instead of running it. Window syncs outlast the agent's command time limit. Every `--suite` option accepts the canonical names (`sql`, `medium`, `shell`) and the CI aliases (`test_sql`, `test_medium`, `test_shell`). `check` and `show` also accept `sql_by_cci` and `test_sql_by_cci`.

If `cubrid-tcr` is not installed or exits with code 2, record the limitation and analyze the failure as usual.

## Record what the analysis learned

Run these commands after the analysis and before the report handoff. `cubrid-ci-analyze` requires this step. Each command is idempotent.

- If a failure matched no signature (`record.result` is `no_single_match` with no candidates) and its shape will recur, add one with `signature add`, then rerun the batch check with `--record`.
  - For a core, pass `--frames` and any `--text`. To see the parsed frames, run `cubrid-tcr signature attach "$TC_PATH" --suite "$SUITE" --run "$RUN_ID" --shard "$SHARD" --stack-file "$SUITE_DIR/failures/<id>/message.txt"`.
  - For a NOK line without a core, pass only `--text` with the stable part of the line from `message.txt`, such as `--text 'NOK stat.log is empty'`. Leave out run-specific numbers and paths.
- If an issue looks related but nobody has confirmed it, run `cubrid-tcr link "$TC_PATH" --suite "$SUITE" --issue CBRD-n --relation suspected`.
- If a later reader needs a fact, run `cubrid-tcr note "$TC_PATH" --suite "$SUITE" --body "..." --ref ...`.
- `check` does not record `test_sql_by_cci` failures. To give such a failure a signature, use `--suite sql`, because `check` applies `sql` signature rules to it.
- If a failure that this PR did not cause recurs across PRs or on `develop`, and no rule covers it, propose a rule to the user as [Add a known-issue rule](#add-a-known-issue-rule) describes.

You can write links, signatures, and notes without asking, because they never change a verdict.

## Add a known-issue rule

A rule hides a failure from analysis, so only the user approves one.

1. Confirm the duplicate. `cubrid-jira-dup candidate-find` suggests candidates. The user confirms the issue.
2. Choose the narrowest signature that matches every known occurrence. For a core, name the assertion site and the caller that distinguishes the bug. Do not use line numbers, because they differ by branch. For a NOK line, use the text that names the symptom.
3. Run `cubrid-tcr rule add --id ID --signature SIG --issue CBRD-n --not-covered "..."` without `--yes`. Show the printed rule to the user.
4. After the user approves, rerun it with `--yes --approved-by <user>`.
5. Prove the rule. `check` with the motivating failure text returns `known`. `check` with another failure text from the same testcase returns `no_match`, if one exists.

A rule for a recurring job-level failure without an issue uses `--job-contains TEXT` and needs `--expires YYYY-MM-DD`. It answers `known_job`, never `known`. Retire a rule with `cubrid-tcr rule retire ID --reason "..."`.

`cubrid-tcr rules --audit` lists the active rules with their Jira state and days until expiry, and flags rules whose issue is resolved `Fixed` or `Done` or whose expiry is near. Run it when a verdict looks stale, and report its flags to the user, who decides whether to retire or extend a rule.

## Track blockers, culprits, and unblock readiness

When a failure's root cause and fix target are identified, record them as a first-class blocker in `cubrid-tcr` so PR unblock checks stay fast and reliable:

- Register or update a blocker (auto-hydrates culprit PR/commit metadata unless `--offline`):
  ```bash
  cubrid-tcr blocker add CBRD-28395 --culprit engine#8537 --fix-issue CBRD-28395 --signature <SIG>
  cubrid-tcr blocker add tc-4474 --culprit engine#7990 --pr tc#4474 --signature <SIG> --rule <RULE>
  cubrid-tcr blocker pr add CBRD-28395 engine#8810
  ```
- Inspect blocker merge readiness and affected open PRs (`cubrid-tcr` owns fix-PR merge state and exposes `wait_keys` in `--json`):
  ```bash
  cubrid-tcr blockers --affected-days 7
  cubrid-tcr unblock --pr <PR_NUMBER>
  ```
- Loose coupling with `work-tracker`: when a work item waits on a CI blocker, record `wait-for:<KEY>` (matching a `wait_keys` value such as `CBRD-28395` or `tc-4474`) in its `work-tracker` note rather than mirroring PR/JIRA state into `work-tracker`.
