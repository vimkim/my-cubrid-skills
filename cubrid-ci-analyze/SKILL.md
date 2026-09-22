---
name: cubrid-ci-analyze
description: Analyze exact-commit CUBRID GitHub Actions evidence collected by cubrid-ci and write an evidence-backed report under my-cubrid-docs. Use for failed-test analysis, failure attribution, root causes, or a CI analysis report for a CUBRID pull request. Use cubrid-ci status for a simple status query; this skill remains read-only when the user asks about repairs.
---

# CUBRID CI Analyzer

Take one status snapshot, collect one exact-commit snapshot, and interpret the resulting schema-v2 evidence. Collection success means the requested evidence is complete; a red CI verdict is evidence, not a collector failure.

## Boundaries

- Analyze all three suites unless the user requests a subset: `test_medium`, `test_sql`, and `test_shell`.
- Use the snapshot available now. Add `--wait` only when the user explicitly asks to wait.
- Keep collection mechanics in `cubrid-ci`: accept its run selection, provenance checks, failure inventory, and durable paths.
- Read testcase source at the recorded Git revision from the local testcase repositories. Preserve every worktree and index unchanged.
- Separate observations, inferences, and unknowns. Every causal claim needs a PR relation, confidence, falsifier, and concrete next action.
- Write a full analysis only when the manifest says the requested collection is complete. For any incomplete collection, write a bounded warning report and make no regression or root-cause conclusion.
- Write under `/home/vimkim/gh/my-cubrid-docs`. Leave the report uncommitted and unpushed unless the user separately requests publication.
- This workflow is read-only outside its evidence and report outputs. It does not trigger CI, call provider APIs directly, download source, reproduce tests, edit source, or repair failures.

## 1. Snapshot and collect once

Require `cubrid-ci`, `jq`, `jsonschema`, `gh`, and `cubrid-pr-status`. Run `cubrid-ci doctor --json`; stop with its diagnostics if setup is not healthy. Record `cubrid-ci --version` for the report.

Run exactly one delegated status command. Pass the supplied PR number or URL; when none was supplied, run it from the user's CUBRID worktree without a PR argument.

```bash
CI_ANALYSIS_TMP=$(mktemp -d -t cubrid-ci-analysis.XXXXXX)
STATUS_JSON="$CI_ANALYSIS_TMP/status.json"
RESULT_JSON="$CI_ANALYSIS_TMP/result.json"
COLLECTOR_VERSION=$(cubrid-ci --version)
PR_REF=${PR_REF:-}

if [[ -n "$PR_REF" ]]
then
  cubrid-ci status "$PR_REF" --json >"$STATUS_JSON"
else
  cubrid-ci status --json >"$STATUS_JSON"
fi
```

Set `PR_REF` to the supplied PR number or URL before running the block; leave it empty for current-directory discovery.

Require a CUBRID PR identity and a 40-character `.pr.head_sha`. Pin that SHA and run exactly one collection command, passing the resolved PR explicitly so collection is independent of the report process's directory:

```bash
SUITE_ARGS=()
# For a user-requested subset, append concrete pairs such as:
# SUITE_ARGS+=(--suite test_sql)

if cubrid-ci collect "$(jq -er '.pr.url' "$STATUS_JSON")" \
    --commit "$(jq -er '.pr.head_sha' "$STATUS_JSON")" \
    "${SUITE_ARGS[@]}" --json >"$RESULT_JSON"
then
  COLLECT_EXIT=0
else
  COLLECT_EXIT=$?
fi
```

Capture the collection exit without discarding JSON. Exit `0` means all requested suites are complete, including terminal red suites. Exit `3` means evidence is unfinished or unavailable and requires a warning report. Exits `2`, `4`, `5`, or `6` are input, trust, remote, or storage failures: report the structured diagnostic and stop unless the result establishes both PR and commit identity and a manifest exists; in that case write only a warning report.

Do not repeat either command to improve the snapshot. Use the returned `.output_dir`; never select an older bundle as the current result.

## 2. Validate the bundle

Use `/home/vimkim/gh/cubrid-ci/schema` as the schema root. Validate the command result and `<output_dir>/manifest.json` with `command-result-v2.schema.json` and `manifest-v2.schema.json`. Require them to agree on repository, PR number and URL, full commit, output directory, requested suite set, suite states, and errors. Also require:

- schema version `2`, repository `CUBRID/cubrid`, and the pinned status SHA;
- manifest `.pr.head_sha` and `.commit` equal the pinned SHA;
- each `completed` suite's run and attempt equal its summary's identity;
- each completed summary validates against `suite-summary-v2.schema.json`;
- its `raw/index.json` validates against `raw-evidence-index-v2.schema.json`;
- every summary failure has one matching `failures/<stable_id>/metadata.json` validated by `failure-v2.schema.json`, and its declared message and optional diff file exist beneath that suite directory;
- counts reconcile: `.counts.tests = passed + failures + errors + skipped`, `.counts.planned = run + unrun + skipped`, and failure records total `failures + errors`.

Treat path escape, identity disagreement, missing declared evidence, count disagreement, or schema failure as untrusted evidence. Produce only a warning report when PR and commit identity remain established; otherwise stop without inventing report identity.

`running`, `not_observed`, `job_level_failure`, and `collection_failed` are distinct states. Do not infer a test verdict for a suite without a validated complete summary.

## 3. Inspect exact evidence and source

For a complete bundle, read the manifest, each completed summary, failure metadata, `message.txt`, optional `diff.txt`, and only the targeted raw text named in `raw/index.json` that bears on a failure. An absent diff with `diff_extraction: not_available` is an observed limitation, not missing-message evidence and not proof that outputs matched.

For each failure, select the testcase SHA from the matching summary shard and choose the local repository:

| Suite | Local Git repository |
|---|---|
| `test_medium`, `test_sql` | `/home/vimkim/gh/cubrid-testcases/develop` |
| `test_shell` | `/home/vimkim/gh/cubrid-testcases-private-ex/develop` |

Require the recorded commit and full testcase path to exist, then read it with `git -C <repo> show <sha>:<path>`. Use the same form for related answer or fixture paths. Never checkout, reset, fetch, or modify the testcase repository. If the local object or path is absent, record the exact source as unknown and keep the conclusion bounded.

Inspect CUBRID code only from a local checkout proven to contain the manifest commit, using `git show <commit>:<path>` where practical. A different local `HEAD` is context, not exact evidence. Consult relevant material in `my-cubrid-docs` and `my-cubrid-jira` when it directly informs attribution.

## 4. Write the report

Derive the directory identity from a `CBRD-<number>` in the validated PR title, otherwise use `PR-<number>`. Write:

```text
/home/vimkim/gh/my-cubrid-docs/<lowercase-identity>/ci_analysis_report_<short-sha>_<agent>.md
```

If that path already identifies another PR or full commit, stop rather than overwrite it.

For a complete manifest, include:

1. Executive summary and decision boundary.
2. CI snapshot with each suite's state, run/attempt link, verdict, and reconciled counts.
3. Evidence scope: exact commit, collection time, collector version, evidence directory, testcase revisions, and limitations.
4. Failure inventory: suite, testcase, result, observed signature, category, PR relation, and confidence.
5. Root-cause analysis grouped by cause. For every group, label observed evidence, inference, unknowns, falsifier, and next action.
6. Prioritized actions and an evidence-file inventory.

Classify PR relation as `direct`, `plausible`, `unlikely`, or `unknown`; classify confidence explicitly. A terminal red job with no testcase records is a job-level failure, not an empty passing suite. If complete evidence contains no failures or errors, say so and do not manufacture analysis.

For an incomplete or untrusted-but-identified bundle, write only: identity, suite-state table, completed evidence that was actually validated, structured diagnostics, unknowns, and actions needed to obtain trustworthy terminal evidence. Put a prominent statement that no regression or root-cause conclusion is supported by this snapshot.

Never include credentials, headers, signed URLs, or environment values.

## 5. Reconcile and hand off

Re-read the saved report against the selected manifest and evidence. Require every requested suite to appear exactly once, every validated failure/error to appear exactly once, all totals to reconcile, every attribution to cite concrete evidence, and every inference to have a falsifier. Correct discrepancies before sharing.

Return the report path, exact commit, suite states and counts, incomplete-evidence warnings, and the highest-priority next action.
