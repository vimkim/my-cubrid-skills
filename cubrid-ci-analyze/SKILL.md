---
name: cubrid-ci-analyze
description: Analyze exact-commit CUBRID GitHub Actions evidence collected by cubrid-ci, add testcase-history context with cubrid-tcc, and write an evidence-backed report in my-cubrid-docs. Use for failed-test analysis, failure attribution, root causes, or a CI analysis report for a CUBRID pull request. Use cubrid-ci status for a simple status query; repairs require a separate workflow.
---

# CUBRID CI Analyzer

Take one status snapshot and one exact-head collection, then attempt exact merge-base collection before attributing failures. Interpret each bundle with its own append-only collection observation. Collection success means the requested evidence is complete; a red CI verdict is evidence, not a collector failure.

## Boundaries

- Analyze all three suites unless the user requests a subset: `test_medium`, `test_sql`, and `test_shell`.
- Use the snapshot available now. Add `--wait` only when the user explicitly asks to wait.
- Keep exact-head and baseline collection mechanics in `cubrid-ci`: accept its run selection, provenance checks, failure inventory, durable paths, and retained-evidence verification. Use `cubrid-tcc` for testcase history under section 3b.
- Read testcase source at the recorded Git revision from the local testcase repositories. Preserve source and testcase worktrees and indexes unchanged.
- Separate observations, inferences, and unknowns. Every causal claim needs a PR relation, confidence, falsifier, and concrete next action.
- Write a full head analysis only when `report_mode.py` permits `full` for the verified head evidence (section 2). Missing baseline evidence limits comparison without downgrading a validated head inventory. For any incomplete, interrupted, or unvalidated collection, write a bounded warning report and make no regression or root-cause conclusion.
- Locate the report repository at `/home/vimkim/gh/my-cubrid-docs`. Before writing, follow [Document Git workflow](../cubrid-common/references/document-git-workflow.md) to select its task checkout, commit the reviewed report locally, and handle approved integration and publication.
- This workflow writes collector-owned evidence and Git cache data, Chronicle-owned history evidence and index data, plus documents in the report repository. Keep provider acquisition in the respective CLI; trigger, cancellation, comments, testcase/source edits, reproduction, repairs, and source/testcase merges require their own authorized workflow. For unsupported evidence sources, follow the separately labeled fallback boundary in [CI evidence](../cubrid-common/references/ci-evidence.md); integrity failures never authorize bypass.

## 1. Snapshot and collect once

Require `cubrid-ci`, `jq`, `gh`, and `cubrid-pr-status`. Run `cubrid-ci doctor --json`; stop with its diagnostics if setup is not healthy. Record `cubrid-ci --version` for the report. Probe once for retained-evidence verification; `VERIFY_AVAILABLE=0` means the installed collector predates it and section 2's fallback applies:

```bash
if cubrid-ci verify --help >/dev/null 2>&1; then VERIFY_AVAILABLE=1; else VERIFY_AVAILABLE=0; fi
```

Run exactly one delegated status command. Pass the supplied PR number or URL; when none was supplied, run it from the user's CUBRID worktree without a PR argument.

```bash
CI_ANALYSIS_TMP=$(mktemp -d -t cubrid-ci-analysis.XXXXXX)
STATUS_JSON="$CI_ANALYSIS_TMP/status.json"
RESULT_JSON="$CI_ANALYSIS_TMP/result.json"
ASSESSMENT_JSON="$CI_ANALYSIS_TMP/assessment.json"
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
PINNED_PR_URL=$(jq -er '.pr.url' "$STATUS_JSON")
PINNED_HEAD=$(jq -er '.pr.head_sha' "$STATUS_JSON")
SUITE_ARGS=()
# For a user-requested subset, append concrete pairs such as:
# SUITE_ARGS+=(--suite test_sql)

COLLECT_STARTED=$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)
if cubrid-ci collect "$PINNED_PR_URL" --commit "$PINNED_HEAD" \
    "${SUITE_ARGS[@]}" --json >"$RESULT_JSON"
then
  COLLECT_EXIT=0
else
  COLLECT_EXIT=$?
fi
```

Capture the collection exit and keep `RESULT_JSON` even when it is empty or a structured error. Exit `0` means all requested suites are complete, including terminal red suites. Exit `3` means evidence is unfinished or unavailable. Exits `2`, `4`, `5`, or `6` are input, trust, remote, or storage failures; keep their structured diagnostic for the report. Section 2 decides which report the evidence permits.

Run each head command exactly once. Section 2 verifies the bundle this invocation produced; never select an older bundle as the current result.

## 2. Verify the observation and bundle

`cubrid-ci verify` establishes offline whether `RESULT_JSON` came from one unique collection observation and whether its retained evidence is intact. It owns observation selection (including an interrupted or failed run that printed no result), schema, identity, manifest, path, digest, count, failure-file, binary-budget, and rerun-lineage checks. When `VERIFY_AVAILABLE` is `0`, use the fallback at the end of this section instead. Otherwise pass the pins, the same suite filters, and the collection start time:

```bash
VERIFY_JSON="$CI_ANALYSIS_TMP/verify.json"
if cubrid-ci verify "$RESULT_JSON" --pr "$PINNED_PR_URL" --pr-head "$PINNED_HEAD" \
    "${SUITE_ARGS[@]}" --since "$COLLECT_STARTED" --json >"$VERIFY_JSON"
then
  VERIFY_EXIT=0
else
  VERIFY_EXIT=$?
fi
jq -e '(.assessment // error("no verification assessment")) + {baseline: "not_assessed"}' \
    "$VERIFY_JSON" >"$ASSESSMENT_JSON"
```

Exit `0` means fully verified evidence. Exit `3` means unfinished, interrupted, failed, unselected, partial, or superseded evidence. Exit `4` means the retained evidence contradicts itself or the pins. Exit `6` means a local read failure, such as a permission error. Each of these writes an `.assessment`. Exit `2` is an invocation error without one, and `jq` then fails: correct the arguments and run `verify` again, since it only reads local files. If `verify` cannot produce an assessment at all, use the fallback.

`verify` establishes the facts; `report_mode.py` applies its decision table to them. From the skill source directory, run `python3 scripts/report_mode.py "$ASSESSMENT_JSON"`. Rerun it with the baseline state after section 3a. Its `mode` is the strongest permitted head output: `full` permits the complete report, `warning` permits only the bounded warning report, and `stop` permits no report. Never upgrade its decision. `comparison_scope: validated_cases_only` permits bounded comparative claims only for the cases validated under the shared comparison contract; it never proves a regression by itself.

Use the verification report as the evidence index:

- Read testcase verdicts only from suites whose `summary` is `validated`, at `<output_dir>/<path>`.
- For a suite with `rerun_sources`, follow [Rerun evidence](../cubrid-common/references/ci-reruns.md) to keep newly executed counts, carried-forward verdicts, and source failures distinct.
- Read the acquisition ledger and binary budget from `<observation_dir>/result.json`. Cite each `.issues[]` entry as a diagnostic.

An `interrupted` observation records a stopped local collector process. It does not establish a provider, workflow, suite, or testcase failure. Write a warning report from its request and retained files, without assigning CI causality.

**Collector without `verify`.** When `VERIFY_AVAILABLE` is `0`, record the missing capability and collector version as a limitation, and treat the bundle as unvalidated raw evidence. Write `ASSESSMENT_JSON` with `observation: unvalidated`, `manifest: missing`, `requested_summaries: none`, both booleans `false`, and `baseline: unavailable`. Set `identity` to `established` only when `RESULT_JSON` is a command result whose `.pr.number` and `.commit` equal `STATUS_JSON`'s `.pr.number` and `.pr.head_sha`, and to `unknown` otherwise. `report_mode.py` then permits at most a warning report. Name installing a collector that provides `verify` as the next action.

`running`, `not_observed`, `job_level_failure`, and `collection_failed` are distinct states. Do not infer a test verdict for a suite without a validated complete summary.

For incomplete terminal observations, report each requested shard as `retained`, `failed`, or `not_attempted` from the verified observation's acquisition ledger. A retained shard means its raw response set was durably acquired; it is not a suite verdict and does not support regression attribution without a validated suite summary. Report suite-level and shard-level acquisition failures with their precise stage, sanitized endpoint, consumed response bytes, and diagnostic. Report `not_attempted` as unknown, not failed. Treat binary bytes consumed by excluded or interrupted transfers as spent budget, and describe absent later binaries as budget-limited rather than provider-absent when the observation says the total budget was exhausted.

## 3. Inspect exact evidence and source

For a complete bundle, read the manifest, each validated summary, failure metadata, `message.txt`, optional `diff.txt`, and only the targeted raw text named in `raw/index.json` that bears on a failure. An absent diff with `diff_extraction: not_available` is an observed limitation, not missing-message evidence and not proof that outputs matched.

For each failure, select the testcase SHA from the matching summary shard and choose the local repository:

| Suite | Local Git repository |
|---|---|
| `test_medium`, `test_sql` | `/home/vimkim/gh/cubrid-testcases/develop` |
| `test_shell` | `/home/vimkim/gh/cubrid-testcases-private-ex/develop` |

Require the recorded commit and full testcase path to exist, then read it with `git -C <repo> show <sha>:<path>`. Use the same form for related answer or fixture paths. Never checkout, reset, fetch, or modify the testcase repository. If the local object or path is absent, record the exact source as unknown and keep the conclusion bounded.

Inspect CUBRID code only from a local checkout proven to contain the manifest commit, using `git show <commit>:<path>` where practical. A different local `HEAD` is context, not exact evidence. Consult relevant material in `my-cubrid-docs` and `my-cubrid-jira` when it directly informs attribution.

## 3a. Acquire and compare the exact merge-base baseline

For PR failure attribution, read [Merge-base comparison](../cubrid-common/references/ci-baseline.md). Run one baseline collection with the same suite filters, then verify it against the head pins:

```bash
BASE_RESULT_JSON="$CI_ANALYSIS_TMP/base-result.json"
BASE_VERIFY_JSON="$CI_ANALYSIS_TMP/base-verify.json"
if cubrid-ci collect-base "$PINNED_PR_URL" "${SUITE_ARGS[@]}" --json >"$BASE_RESULT_JSON"
then
  BASE_EXIT=0
else
  BASE_EXIT=$?
fi
cubrid-ci verify "$BASE_RESULT_JSON" --pr "$PINNED_PR_URL" --pr-head "$PINNED_HEAD" \
    "${SUITE_ARGS[@]}" --json >"$BASE_VERIFY_JSON"
BASELINE=$(jq -r '.baseline // "unavailable"' "$BASE_VERIFY_JSON" 2>/dev/null)
BASELINE=${BASELINE:-unavailable}
jq --arg baseline "$BASELINE" '.baseline = $baseline' "$ASSESSMENT_JSON" >"$ASSESSMENT_JSON.next"
mv "$ASSESSMENT_JSON.next" "$ASSESSMENT_JSON"
```

`BASELINE` is `validated_exact`, `partial_exact`, `unavailable`, or `invalid`. It is `unavailable` when the installed CLI lacks `collect-base` or `verify`; source changes in another checkout do not establish installed support. The pins make `verify` reject a baseline resolved from another PR or head. The saved result's `.selection.baseline` target tip, exact merge base, and observation time establish the comparison identity. A malformed, partial, or missing baseline constrains comparison; preserve the independently verified head report.

Compare each exact testcase path and observed signature with the validated baseline evidence, preserving test revisions and configuration differences. Classify head failures as `also_observed_on_base`, `additional_on_head`, or `uncomparable`, and record `base_only` separately. Partial comparison permits conclusions only for suites whose baseline `summary` is `validated`, and for matching cases within them. Neither a valid baseline nor the gate's permission establishes causality.

## 3b. Check testcase failure history

For a complete validated head bundle with testcase failures or errors, read [Testcase history with Chronicle](../cubrid-common/references/ci-evidence.md#testcase-history-with-chronicle). Follow it for each distinct failed testcase, using `cubrid-tcc` when installed. It defines exact-path and suite selection, occurrence matching, bounded index refresh, and the evidence needed for recurrence, matching symptoms, or suspected flakiness.

Keep historical context separate from the exact merge-base classification. Record unavailable history and unresolved identities as unknown. History cannot upgrade the report-mode gate, supply a missing validated baseline, or change the current failure inventory.

## 4. Write the report

If `$asd-ste100` is available, use its STE-flavored mode for English report prose.
Use Strict mode for procedures. Preserve evidence labels, identifiers, uncertainty,
and the strength of causal claims. Keep the report's requested language.

Select `ARTIFACT_WORKTREE` using the Document Git workflow before creating report files or directories. Derive the directory identity from a `CBRD-<number>` in the validated PR title, otherwise use `PR-<number>`. Apply the shared naming and reuse rules, reusing existing directory spelling as required by the report repository. A new report can use:

```text
<existing-or-new-identity-directory>/ci-analysis.md
```

Before updating a report, compare its PR, full commit, requested suites, runs/attempts, observation time, and completeness. Extend a matching ongoing report without losing earlier observations. Keep a separately cited snapshot or distinct scope in its own file, using a meaningful discriminator only when needed. Record exact identities inside the report and relevant scope in the index.

Lead with the result, analyzed scope, limitations, and next action. Put detailed evidence in later sections or tables. Use sections only when they carry relevant content. For a complete manifest, cover:

1. Summary and limits of the conclusion.
2. CI snapshot with each suite's state, run/attempt link, verdict, and reconciled counts.
3. Evidence scope: exact commit, collection time, collector version, evidence directory, testcase revisions, and limitations.
4. Failure inventory: suite, full testcase path, result, observed signature, baseline classification, category, PR relation, and confidence. Reconcile head, shared, additional, uncomparable, and baseline-only counts separately.
5. Root-cause analysis grouped by cause. For every group, label observed evidence, inference, unknowns, falsifier, and next action.
6. Baseline comparison: pinned head/target/merge-base identities, discovery coverage, selected runs/attempts, exact input revisions, affected-file equality evidence, configuration differences, and comparison limitations. Include an explicit unavailable-baseline statement when applicable.
7. Testcase history: selected occurrence, earlier failures and their Engine/testcase revisions, symptom comparison, flakiness assessment, query scope, freshness and coverage limitations, and retained evidence references. State when history or correspondence with the selected failure is unavailable. If there are no testcase failures or errors, omit the history section.
8. Prioritized actions and an evidence-file inventory. Keep pre-existing signatures visible as separate follow-up work; they do not waive CI requirements.

Classify PR relation as `direct`, `plausible`, `unlikely`, or `unknown`; classify confidence explicitly. A terminal red job with no testcase records is a job-level failure, not an empty passing suite. If complete evidence contains no failures or errors, say so and do not manufacture analysis.

For an incomplete, interrupted, or unvalidated-but-identified bundle, write only: identity, observation outcome, suite-state table, acquisition ledger, completed evidence that was actually validated, binary-budget limitations, structured diagnostics, unknowns, and actions needed to obtain validated terminal evidence. Put a prominent statement that no regression or root-cause conclusion is supported by this snapshot.

Never include credentials, headers, signed URLs, or environment values.

## 5. Reconcile and hand off

Re-read the saved report against the selected manifest and evidence. Require every requested suite to appear exactly once, every validated failure/error to appear exactly once, all totals to reconcile, every comparison to reconcile against the independently validated baseline and input scope, every attribution to cite concrete evidence, and every inference to have a falsifier. Check historical claims against retained occurrences, symptom evidence, and identity/coverage limitations. Correct discrepancies before sharing.

Complete the Document Git workflow's local review and task commit, including any required report index. Return the report path, exact analyzed commit, suite states and counts, incomplete-evidence warnings, task checkout/branch and report commit, checks, and the highest-priority next action. Present any required integration approval with this committed result; continue approved integration and publication under the same workflow.
