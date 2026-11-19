# Known CI issues

`cubrid-tcr` holds per-testcase knowledge: failure signatures, issue links, notes, and known-issue rules. Chronicle (`cubrid-tcc`) supplies the failure history. Before you attribute a CI failure to the PR, check each failure with `cubrid-tcr`.

## Check each failure

1. For testcase failures, take the suite directory that `cubrid-ci` collected, the one that holds `summary.json` and `failures/`. Index its run once, as [Index the current run once](ci-evidence.md#index-the-current-run-once) describes. `--record` needs the run in Chronicle.
2. Check every failure of that directory with one command:

```bash
cubrid-tcr --json check --ci-attempt "$SUITE_DIR" --record
```

It reads each failure's testcase path, shard, tested Engine SHA from the shard build provenance, and `message.txt`, which holds any CTP `CORE ANALYZER` stacks. It applies the testcase's rules and the rules of the shard's job, so a `test_sql_by_cci` failure needs no second call. `failures[]` has one entry per failure with `identity`, `verdict`, `hits`, `reason`, `stack_found`, and `history` counts. `--record` tags the occurrence when exactly one signature matches its stack; `record.result` says what happened. If the output has `rerun.mode` `carried_forward`, the attempt ran no cases; check the source attempt named in `rerun` instead.

3. For a job-level failure without testcase records, check the job name with the shard's tested Engine SHA. A workflow `head_sha` is not enough.

```bash
cubrid-tcr --json check --job "$JOB_NAME" --engine "$ENGINE_SHA"
```

`check` reads fix commits from `origin/develop` of `$TCR_ENGINE_REPO`. If it exits 2 and names that variable, pass `--engine-repo` with a local `CUBRID/cubrid` checkout.

4. Apply the label for the `verdict` from the table below. Cite the rule id, the issue, and the `reason`.
5. Keep every failure in the failure inventory, whatever its verdict. Still analyze every other failure in the same job.

| Verdict | Report label |
|---|---|
| `no_match` | Analyze as usual. |
| `known` | "Known issue, not caused by this PR." Do not analyze its root cause or propose a fix. |
| `fix_missing` | Known issue. Tell the user that the tested branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | Do not apply the rule. Analyze the failure as new. Tell the user that the issue may need to be reopened, and cite the run and the stack. |
| `expired` | Do not apply the rule. Tell the user to retire or extend it. |
| `unknown` | Known issue, with the `reason` that the state is unknown. If the reason is a missing stack, get the stack and check again. |

Each entry's `history` counts earlier failures by branch and signature. Report it as history context. History context does not prove a root cause or PR causality. `cubrid-tcr show "$TC_PATH" --suite "$SUITE"` prints the full testcase view with related issues and notes. If that view's `sync_hint` names a date window, record the gap in one line instead of running it. Window syncs outlast the agent's command time limit.

If `cubrid-tcr` is not installed or exits with code 2, record the limitation and analyze the failure as usual.

## Record what the analysis learned

Run these commands after the analysis. Each command is idempotent.

- If a stack matched no signature (`record.result` is `no_single_match` with no candidates) and the shape will recur, add one with `signature add`. To see the parsed frames, run `cubrid-tcr signature attach "$TC_PATH" --suite "$SUITE" --run "$RUN_ID" --shard "$SHARD" --stack-file "$SUITE_DIR/failures/<id>/message.txt"`. Then rerun the batch check with `--record`.
- If an issue looks related but nobody has confirmed it, run `cubrid-tcr link "$TC_PATH" --suite "$SUITE" --issue CBRD-n --relation suspected`.
- If a later reader needs a fact, run `cubrid-tcr note "$TC_PATH" --suite "$SUITE" --body "..." --ref ...`.

You can write links, signatures, and notes without asking, because they never change a verdict.

## Add a known-issue rule

A rule hides a failure from analysis, so only the user approves one.

1. Confirm the duplicate. `cubrid-jira-dup candidate-find` suggests candidates. The user confirms the issue.
2. Choose the narrowest signature that matches every known occurrence. Name the assertion site and the caller that distinguishes the bug. Do not use line numbers, because they differ by branch.
3. Run `cubrid-tcr rule add --id ID --signature SIG --issue CBRD-n --not-covered "..."` without `--yes`. Show the printed rule to the user.
4. After the user approves, rerun it with `--yes --approved-by <user>`.
5. Prove the rule. `check` with the motivating stack returns `known`. `check` with another stack from the same testcase returns `no_match`, if such a stack exists.

A rule for a recurring job-level failure without an issue uses `--job-contains TEXT` and needs `--expires YYYY-MM-DD`. Retire a rule with `cubrid-tcr rule retire ID --reason "..."`.
