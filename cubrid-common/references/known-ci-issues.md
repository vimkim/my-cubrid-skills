# Known CI issues

`cubrid-tcr` holds per-testcase knowledge: failure signatures, issue links, notes, and known-issue rules. Chronicle (`cubrid-tcc`) supplies the failure history. Before you attribute a CI failure to the PR, check each failure with `cubrid-tcr`.

## Check each failure

1. Take the suite and the full testcase path from the validated testcase identity. For a job-level failure without testcase records, take the job name.
2. Take the tested Engine SHA from the shard build provenance, as [CI evidence and testcase identity](ci-evidence.md) requires. A workflow `head_sha` is not enough.
3. Set `ENGINE_REPO` to a local `CUBRID/cubrid` checkout, such as the user's `develop` worktree. `check` reads its `origin/develop` to find fix commits, so fetch it first if it is stale.
4. If the failure left a core stack, save that core's backtrace text in the evidence directory. Save one core per file.
5. Run the check:

```bash
cubrid-tcr check --case "$TC_PATH" --suite "$SUITE" --engine "$ENGINE_SHA" \
    --engine-repo "$ENGINE_REPO" --stack-file "$EVIDENCE_DIR/core-stack.txt" --json
cubrid-tcr check --job "$JOB_NAME" --engine "$ENGINE_SHA" --engine-repo "$ENGINE_REPO" --json
```

6. Apply the label for the `verdict` from the table below. Cite the rule id, the issue, and the `reason`.
7. Keep every failure in the failure inventory, whatever its verdict. Still analyze every other failure in the same job.

| Verdict | Report label |
|---|---|
| `no_match` | Analyze as usual. |
| `known` | "Known issue, not caused by this PR." Do not analyze its root cause or propose a fix. |
| `fix_missing` | Known issue. Tell the user that the tested branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | Do not apply the rule. Analyze the failure as new. Tell the user that the issue may need to be reopened, and cite the run and the stack. |
| `expired` | Do not apply the rule. Tell the user to retire or extend it. |
| `unknown` | Known issue, with the `reason` that the state is unknown. If the reason is a missing stack, get the stack and check again. |

`check --case` also returns `context`, the testcase view. It lists earlier failures by PR, branch, and signature, plus the related issues and the notes. Report it as history context. History context does not prove a root cause or PR causality. If `context.history.sync_hint` is set, run that bounded sync once, and then run `check` again. Report remaining gaps instead of syncing again. `cubrid-tcr show "$TC_PATH" --suite "$SUITE"` prints the same view for a person.

If `cubrid-tcr` is not installed or exits with code 2, record the limitation and analyze the failure as usual.

## Record what the analysis learned

Run these commands after the analysis. Each command is idempotent.

- If a stack was available, tag the occurrence: `cubrid-tcr signature attach "$TC_PATH" --suite "$SUITE" --run "$RUN_ID" --shard "$SHARD" --stack-file "$STACK_FILE"`. If no signature matches, the command prints the parsed frames. Add a signature with `signature add` when the shape will recur.
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
