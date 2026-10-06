---
name: cubrid-ci-analyze
description: Analyze exact-commit CUBRID GitHub Actions evidence collected by cubrid-ci and write an evidence-backed report under my-cubrid-docs. Use for failed-test analysis, failure attribution, root causes, or a CI analysis report for a CUBRID pull request. Use cubrid-ci status for a simple status query; this skill remains read-only when the user asks about repairs.
---

# CUBRID CI Analyzer

Take one status snapshot and one exact-head collection, then attempt exact merge-base collection before attributing failures. Interpret each bundle with its own append-only collection observation. Collection success means the requested evidence is complete; a red CI verdict is evidence, not a collector failure.

## Boundaries

- Analyze all three suites unless the user requests a subset: `test_medium`, `test_sql`, and `test_shell`.
- Use the snapshot available now. Add `--wait` only when the user explicitly asks to wait.
- Keep collection mechanics in `cubrid-ci`: accept its run selection, provenance checks, failure inventory, and durable paths.
- Read testcase source at the recorded Git revision from the local testcase repositories. Preserve every worktree and index unchanged.
- Separate observations, inferences, and unknowns. Every causal claim needs a PR relation, confidence, falsifier, and concrete next action.
- Write a full head analysis only when the head manifest and matching terminal observation say the requested head collection is complete. Missing baseline evidence limits comparison without downgrading a validated head inventory. For any incomplete, interrupted, or unvalidated collection, write a bounded warning report and make no regression or root-cause conclusion.
- Write under `/home/vimkim/gh/my-cubrid-docs`. Leave the report uncommitted and unpushed unless the user separately requests publication.
- This workflow writes only evidence, reports, and the collector-owned Git cache used for merge-base resolution. Keep GitHub acquisition in the CLI; trigger, cancellation, comments, testcase/source edits, reproduction, repairs, and local merges require their own authorized workflow. For unsupported evidence sources, follow the separately labeled fallback boundary in [CI evidence](../cubrid-common/references/ci-evidence.md); integrity failures never authorize bypass.

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

Do not repeat either head command to improve the snapshot. Use the returned `.output_dir`; never select an older bundle as the current result.

## 2. Validate the observation and bundle

Use `/home/vimkim/gh/cubrid-ci/schema` as the schema root. Under the returned `<output_dir>/observations`, select the observation whose terminal `result.json.command` equals the saved collector result, including `collected_at`. Validate its `request.json` and `result.json` with `collection-observation-request-v1.schema.json` and `collection-observation-result-v1.schema.json`. Require matching observation IDs; require the request to match the pinned repository, PR, commit, canonical requested suite set, and collection options; and require the result command to equal the saved collector result. If no unique matching observation exists, treat the collection as unvalidated raw evidence.

An observation with `request.json` but no `result.json` records an interrupted local collector process. It does not establish a provider, workflow, suite, or testcase failure. Select such an observation only when its identity, requested suites, and invocation time uniquely match this invocation; ambiguity leaves unvalidated raw evidence. Write a warning report from its validated request and retained files, without assigning CI causality.

For a terminal observation, validate the command result and `<output_dir>/manifest.json` with `command-result-v2.schema.json` and `manifest-v2.schema.json`. Require them to agree on repository, PR number and URL, full commit, output directory, requested suite set, suite states, and errors. Also require:

- schema version `2`, repository `CUBRID/cubrid`, and the pinned status SHA;
- manifest `.pr.head_sha` and `.commit` equal the pinned SHA;
- each `completed` suite's run and attempt equal its summary's identity;
- each completed summary validates against `suite-summary-v2.schema.json`;
- its `raw/index.json` validates against `raw-evidence-index-v2.schema.json`;
- when binary collection was requested, `binary-inventory.json` validates against `binary-inventory-v2.schema.json`, each downloaded file matches its declared length and digest, and the observation budget arithmetic and per-artifact consumption reconcile;
- every summary failure has one matching `failures/<stable_id>/metadata.json` validated by `failure-v2.schema.json`, and its declared message and optional diff file exist beneath that suite directory;
- counts reconcile: `.counts.tests = passed + failures + errors + skipped`, `.counts.planned = run + unrun + skipped`, and failure records total `failures + errors`.

Treat path escape, identity disagreement, missing declared evidence, count disagreement, or schema failure as unvalidated raw evidence. Produce only a warning report when PR and commit identity remain established; otherwise stop without inventing report identity.

After these validations, write a temporary assessment JSON with `identity`, `observation`, `manifest`, `requested_summaries`, `result_matches_observation`, `requested_suites_reconciled`, and `baseline`, using the closed values accepted by this skill's `scripts/report_mode.py`. From the skill source directory, run `python3 scripts/report_mode.py <assessment.json>`. Set `baseline` to `not_assessed` initially, then rerun this local gate with the baseline assessment after section 3a. Its `mode` is the strongest permitted head output: `full` permits the complete report, `warning` permits only the bounded warning report, and `stop` permits no report. Never upgrade its decision. `comparison_scope: validated_cases_only` permits bounded comparative claims only for the cases validated under the shared comparison contract; it never proves a regression by itself. The fixture-backed script is the executable safety boundary; the evidence checks above remain the source of its inputs.

`running`, `not_observed`, `job_level_failure`, and `collection_failed` are distinct states. Do not infer a test verdict for a suite without a validated complete summary.

For incomplete terminal observations, report each requested shard as `retained`, `failed`, or `not_attempted` from the validated acquisition ledger. A retained shard means its raw response set was durably acquired; it is not a suite verdict and does not support regression attribution without a validated suite summary. Report suite-level and shard-level acquisition failures with their precise stage, sanitized endpoint, consumed response bytes, and diagnostic. Report `not_attempted` as unknown, not failed. Treat binary bytes consumed by excluded or interrupted transfers as spent budget, and describe absent later binaries as budget-limited rather than provider-absent when the observation says the total budget was exhausted.

## 3. Inspect exact evidence and source

For a complete bundle, read the manifest, each completed summary, failure metadata, `message.txt`, optional `diff.txt`, and only the targeted raw text named in `raw/index.json` that bears on a failure. An absent diff with `diff_extraction: not_available` is an observed limitation, not missing-message evidence and not proof that outputs matched.

For each failure, select the testcase SHA from the matching summary shard and choose the local repository:

| Suite | Local Git repository |
|---|---|
| `test_medium`, `test_sql` | `/home/vimkim/gh/cubrid-testcases/develop` |
| `test_shell` | `/home/vimkim/gh/cubrid-testcases-private-ex/develop` |

Require the recorded commit and full testcase path to exist, then read it with `git -C <repo> show <sha>:<path>`. Use the same form for related answer or fixture paths. Never checkout, reset, fetch, or modify the testcase repository. If the local object or path is absent, record the exact source as unknown and keep the conclusion bounded.

Inspect CUBRID code only from a local checkout proven to contain the manifest commit, using `git show <commit>:<path>` where practical. A different local `HEAD` is context, not exact evidence. Consult relevant material in `my-cubrid-docs` and `my-cubrid-jira` when it directly informs attribution.

## 3a. Acquire and compare the exact merge-base baseline

For PR failure attribution, read [Merge-base comparison](../cubrid-common/references/ci-baseline.md). Run one `cubrid-ci collect-base <resolved-pr-url> --json` with the same suite filters, retain its exit and JSON, and validate the resulting schema-v3 bundle and observation-v2 pair independently. If the installed CLI lacks the command, record the missing capability and an unknown baseline; source changes in another checkout do not establish installed support.

Require the baseline relationship's PR number and head SHA to match the pinned head snapshot. Its target tip, exact merge base, and observation time establish the comparison identity. A changed head, ambiguous merge base, missing artifacts, or unavailable history constrains comparison; preserve the independently validated head report.

Compare each exact testcase path and observed signature with the validated baseline evidence, preserving test revisions and configuration differences. Classify head failures as `also_observed_on_base`, `additional_on_head`, or `uncomparable`, and record `base_only` separately. Set the report-mode assessment's `baseline` to `validated_exact`, `partial_exact`, `unavailable`, or `invalid`. Partial comparison permits conclusions only for independently validated matching suites/cases. Neither a valid baseline nor the gate's permission establishes causality.

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
4. Failure inventory: suite, full testcase path, result, observed signature, baseline classification, category, PR relation, and confidence. Reconcile head, shared, additional, uncomparable, and baseline-only counts separately.
5. Root-cause analysis grouped by cause. For every group, label observed evidence, inference, unknowns, falsifier, and next action.
6. Baseline comparison: pinned head/target/merge-base identities, discovery coverage, selected runs/attempts, exact input revisions, affected-file equality evidence, configuration differences, and comparison limitations. Include an explicit unavailable-baseline statement when applicable.
7. Prioritized actions and an evidence-file inventory. Keep pre-existing signatures visible as separate follow-up work; they do not waive CI requirements.

Classify PR relation as `direct`, `plausible`, `unlikely`, or `unknown`; classify confidence explicitly. A terminal red job with no testcase records is a job-level failure, not an empty passing suite. If complete evidence contains no failures or errors, say so and do not manufacture analysis.

For an incomplete, interrupted, or unvalidated-but-identified bundle, write only: identity, observation outcome, suite-state table, acquisition ledger, completed evidence that was actually validated, binary-budget limitations, structured diagnostics, unknowns, and actions needed to obtain validated terminal evidence. Put a prominent statement that no regression or root-cause conclusion is supported by this snapshot.

Never include credentials, headers, signed URLs, or environment values.

## 5. Reconcile and hand off

Re-read the saved report against the selected manifest and evidence. Require every requested suite to appear exactly once, every validated failure/error to appear exactly once, all totals to reconcile, every comparison to reconcile against the independently validated baseline and input scope, every attribution to cite concrete evidence, and every inference to have a falsifier. Correct discrepancies before sharing.

Return the report path, exact commit, suite states and counts, incomplete-evidence warnings, and the highest-priority next action.
