---
name: cubrid-ci-analyze
description: Collect the currently available exact-commit CircleCI snapshot for a CUBRID GitHub pull request with the `cubrid-ci` binary, analyze failed tests across test_medium, test_sql, and test_shell, and write an evidence-backed report under my-cubrid-docs. Use when the user provides a CUBRID PR URL and asks for CI status, failed-test analysis, failure attribution, root causes, or a CI report. Triggers on phrases like "analyze this PR's CI", "analyze CI failures", "CI 실패 분석", "failed TC 분석", or "write a CI analysis report".
---

# CUBRID CI Analyzer

Use the Rust `cubrid-ci` collector as the only mechanism for discovering and downloading CircleCI evidence. Analyze the resulting local bundle and write a failure-focused report. Never reimplement collection with `gh`, `curl`, CircleCI APIs, or a bundled fetch script.

## Non-Negotiable Contracts

- Analyze `test_medium`, `test_sql`, and `test_shell` when the user supplies only a PR URL. If the user explicitly requests a subset, collect only that subset.
- Collect the snapshot that is available now. Never pass `--wait`; record an unavailable, missing, pending, build-blocked, or timed-out requested suite as a warning.
- Pin every suite to one full commit SHA. Never allow separate suite invocations to resolve different moving PR heads.
- Store durable evidence under `/home/vimkim/gh/cubrid-circleci-analyzer/data`.
- Use `--artifact-mode text` and `--include-test-sources`. Ask before using `--artifact-mode all` because core dumps and other binary artifacts can be large.
- Focus substantive analysis on failures. Report passing suites only as snapshot context.
- Treat observed evidence, inference, and unknowns as distinct. Never invent a diff, root cause, PR relationship, or successful result.
- Write the report to `/home/vimkim/gh/my-cubrid-docs`; do not write it in a CUBRID source worktree or the skills repository.
- Grill every report with `grill-with-docs` before sharing it.
- Do not trigger CI, rerun a job, modify CUBRID or testcase source, update the PR, or commit/push the report unless the user separately requests it.

## Step 1: Validate the Environment

1. Require a CUBRID PR URL in this form:

   ```text
   https://github.com/CUBRID/cubrid/pull/<number>
   ```

2. Require the installed collector and JSON reader, then record the collector version:

   ```bash
   command -v cubrid-ci
   command -v jq
   cubrid-ci --version
   ```

   If it is missing, stop and tell the user to install it from `/home/vimkim/gh/cubrid-circleci-analyzer` according to that repository's `README.md`. Do not silently substitute manual API calls.

3. Set and validate the fixed roots:

   ```bash
   ANALYZER_ROOT=/home/vimkim/gh/cubrid-circleci-analyzer
   DATA_ROOT="$ANALYZER_ROOT/data"
   DOCS_ROOT=/home/vimkim/gh/my-cubrid-docs

   test -d "$ANALYZER_ROOT"
   git -C "$DOCS_ROOT" rev-parse --is-inside-work-tree
   ```

4. Read `$ANALYZER_ROOT/README.md` if the installed CLI rejects an option or its version differs from the workflow assumed here. The tool is authoritative for collection behavior.

## Step 2: Pin the Snapshot Commit

Map suite names to CLI commands exactly:

| Suite | `cubrid-ci` command |
|---|---|
| `test_medium` | `test-medium` |
| `test_sql` | `test-sql` |
| `test_shell` | `test-shell` |

Choose the first requested command as the anchor. Use `test-medium` when all three suites are requested. Run the anchor once without a commit, with no `--wait`:

```bash
PR_URL='<pr-url>'
ANCHOR_COMMAND=test-medium
MARKER_FILE=$(mktemp -t cubrid-ci-marker.XXXXXX)
RESULT_FILE=$(mktemp -t cubrid-ci-result.XXXXXX.json)

if cubrid-ci --json "$ANCHOR_COMMAND" "$PR_URL" \
    --data-dir "$DATA_ROOT" \
    --artifact-mode text \
    --include-test-sources >"$RESULT_FILE"
then
  ANCHOR_EXIT=0
else
  ANCHOR_EXIT=$?
fi
```

The `if` form captures a nonzero exit without allowing shell `errexit` to abort the workflow.

- Exit `0`: read the suite path from `.output_dir` in `RESULT_FILE`, set `MANIFEST_PATH` to the sibling commit-level `manifest.json`, and read the full SHA from `.resolved_commit` there.
- Exit `3`: the requested suite is unavailable, but the tool wrote a commit manifest. Select it with the exact procedure below and retain the anchor warning.
- Exit `2`, `4`, `5`, or `6`: stop. Report the collector error and its documented meaning; do not create a CI analysis from untrusted or incomplete evidence.

For exit `3`, inspect only manifests created or replaced by this invocation and matching the exact PR URL:

```bash
MATCHING_MANIFESTS=()
while IFS= read -r -d '' candidate
do
  if jq -e --arg pr_url "$PR_URL" '.pr_url == $pr_url' "$candidate" >/dev/null
  then
    MATCHING_MANIFESTS+=("$candidate")
  fi
done < <(find "$DATA_ROOT" -type f -name manifest.json -newer "$MARKER_FILE" -print0)

if (( ${#MATCHING_MANIFESTS[@]} != 1 ))
then
  echo "Expected exactly one newly written manifest for $PR_URL" >&2
  exit 1
fi
MANIFEST_PATH=${MATCHING_MANIFESTS[0]}
```

For exit `0`, derive the same path without searching:

```bash
ANCHOR_SUITE_DIR=$(jq -er '.output_dir' "$RESULT_FILE")
MANIFEST_PATH=$(dirname -- "$ANCHOR_SUITE_DIR")/manifest.json
```

Resolve and validate the commit from the selected manifest:

```bash
SOURCE_COMMIT=$(jq -er '.resolved_commit' "$MANIFEST_PATH")
[[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]]
```

Delete only `MARKER_FILE` and `RESULT_FILE` after extracting the identity. Do not guess from an older evidence directory if no unique newly written manifest exists.

## Step 3: Collect Every Requested Suite

Run the remaining requested suites sequentially with the pinned full SHA:

```bash
SUITE_COMMAND=test-sql
if cubrid-ci --json "$SUITE_COMMAND" "$PR_URL" "$SOURCE_COMMIT" \
    --data-dir "$DATA_ROOT" \
    --artifact-mode text \
    --include-test-sources
then
  SUITE_EXIT=0
else
  SUITE_EXIT=$?
fi
```

Do not pass `--wait`. Do not launch suite collectors in parallel because they update the same commit-level manifest.

Handle each result as follows:

| Exit | Meaning | Action |
|---:|---|---|
| 0 | Terminal suite result validated and collected | Analyze the suite directory, even when CI itself failed |
| 3 | Missing, pending, build-blocked, or otherwise unavailable | Continue and add a prominent report warning |
| 2 | Invalid input or configuration | Stop and report the error |
| 4 | GitHub/CircleCI identity mismatch | Stop; do not trust the evidence |
| 5 | Remote API, authentication, or rate-limit failure | Stop and report the access boundary |
| 6 | Local storage, schema, or normalization failure | Stop and report the collector failure |

Remember that a failed CI suite collected successfully exits `0`; CI failure is evidence, not a collector error.

After collection, locate the commit directory from the anchor result or the unique matching manifest and require:

```text
<DATA_ROOT>/<directory_identity>/<short_sha>/manifest.json
```

Verify that `.schema_version == 1`, `.resolved_commit`, `.pr_url`, and `.short_sha` match the pinned request before analyzing any suite. Stop and consult the analyzer repository's schemas if the version is not supported.

## Step 4: Read the Evidence Bundle

Read evidence in this order:

1. Commit `manifest.json` for PR identity, title, branches, exact commit, prerequisites, and all suite states.
2. Each available requested suite's `summary.json` for CircleCI job identity, counts, durations, failed nodes, artifact counts, and testcase revision.
3. `failed-tc.txt` and `failed-tests.json` for the complete `result == "failure"` inventory and upstream messages. If `summary.json.error_count` or `.unknown_count` is nonzero, also inspect `attempts/<circleci-job>/raw/tests.json` and inventory those abnormal results explicitly.
4. Every directory under `failures/`: read `metadata.json`, `message.txt`, and `diff.txt`. An empty `diff.txt` means no diff was extracted; it is not proof that outputs matched.
5. Read `logs/index.json`, `artifacts.json`, and `sources/index.json` before opening targeted files under `logs/`, `artifacts/`, and `sources/`. Inspect file sizes and open only evidence relevant to a failure signature.
6. Relevant existing context in `/home/vimkim/gh/my-cubrid-docs` and `/home/vimkim/gh/my-cubrid-jira` before drawing CUBRID-specific conclusions.

Use downloaded testcase sources when present. If a source download failed, record the diagnostic from `sources/index.json`. Use a local testcase checkout only when its revision can be proven to equal `summary.json.testcase_revision`; otherwise treat it as contextual, not exact evidence.

If an exact local CUBRID checkout for the tested commit is already available, inspect the relevant changed code and call paths. Do not substitute a different local `HEAD`. If exact source is unavailable, state that limitation and keep conclusions bounded by the collected evidence.

Never use an older CI bundle as the current result. Historical bundles may be used only for an explicitly labeled baseline comparison, and only after validating their PR URL, full commit, suite, and CircleCI job identity.

## Step 5: Analyze Failures

For every test whose result is `failure`, `error`, or unknown:

1. State the directly observed failure signature: diff, fatal message, timeout, crash, missing output, or generic `Test failed`.
2. Explain what the test exercises, using exact downloaded source when available.
3. Determine the narrowest defensible root-cause category. Group tests by underlying cause, not by similar-looking symptoms.
4. Assess relation to the PR or feature as `direct`, `plausible`, `unlikely`, or `unknown`, and cite the concrete behavioral connection or absence of one.
5. Assign a confidence level and identify the next observation that could falsify the hypothesis.
6. Recommend a concrete next action at testcase, file, function, command, or artifact level. Do not propose answer-file churn until intended behavior or a stable baseline supports it.

Prefer these evidence labels in prose and tables:

- **Observed**: directly present in the exact bundle.
- **Inferred**: a reasoned explanation supported by stated evidence.
- **Unknown**: evidence is insufficient; local reproduction, another artifact mode, or exact source inspection is required.

Treat `failure_count`, `error_count`, and `unknown_count` separately. Do not count skipped tests as failures. If there are no failed or abnormal tests in the available requested suites, say so explicitly and do not manufacture failure analysis. If every requested suite is unavailable, write a snapshot warning report with no regression conclusion.

## Step 6: Resolve Report Identity

Read identity from the validated manifest:

- `SOURCE_COMMIT=.resolved_commit`
- `SHORT_SHA=.short_sha`
- ticket from `.directory_identity`
- PR number and URL from `.pr_number` and `.pr_url`
- active host identity: `codex` for Codex, `claude` for Claude Code, or another stable lowercase runtime name

Require a `CBRD-XXXXX` identity before writing. If the tool used `PR-<number>` because no ticket was discoverable, ask the user which CBRD ticket directory to use.

Normalize the directory to lowercase and set the path once:

```text
REPORT_PATH=/home/vimkim/gh/my-cubrid-docs/cbrd-xxxxx/ci_analysis_report_<SHORT_SHA>_<AGENT>.md
```

If `REPORT_PATH` already exists, verify that it names the same PR and full commit before revising it. If either identity differs, stop and ask the user; do not overwrite it or invent a suffix. Preserve unrelated user changes in the docs worktree.

## Step 7: Write the Report

Use English `##` section headers and concise technical English. Keep the snapshot table brief and devote detail to failures.

```markdown
# CI Failure Analysis: PR #<number> at `<short-sha>`

## Executive Summary

<failure count, strongest conclusion, warnings, and decision boundary>

## CI Snapshot

| Suite | State | CircleCI job | Tests | Failures | Errors | Unknown | Warning |
|---|---|---:|---:|---:|---:|---:|---|

## Evidence Scope

<exact commit, collection time, tool version, evidence directory, testcase revisions, limitations>

## Failure Inventory

| Suite | Test | Result | Observed signature | Category | PR relation | Confidence |
|---|---|---|---|---|---|---|

## Root-Cause Analysis

### <Category> (<count> tests)

<observed evidence, inference, falsifier, and concrete next action>

## Recommended Actions

<prioritized, actionable follow-up>

## Evidence and Limitations

<files inspected, unavailable suites, missing sources/artifacts, and conclusions not supported>
```

Include direct CircleCI job links from each `summary.json`. Name the persistent evidence directory, but do not include credentials, signed artifact URLs, authorization headers, or environment values. Do not claim that an unavailable suite passed, failed, or is unrelated to the PR.

## Step 8: Grill the Report

After saving the initial report, invoke `grill-with-docs` and revise the same `REPORT_PATH` in place.

Provide:

- **Topic and audience**: exact-commit CUBRID CI failure analysis for the PR author, QA, and maintainers.
- **Source material**: manifest, suite summaries, every failed-test record, targeted logs/artifacts/sources, relevant local docs, and exact source context if available.
- **Review angle**: suite identity is exact; unavailable suites are warnings; every attribution has concrete evidence; hypotheses are falsifiable; categories reflect root causes; recommendations are actionable; unknowns remain unknown.

Follow `grill-with-docs` as written: explore the codebase instead of asking answerable questions, ask the user one unresolved question at a time, and revise the report as decisions crystallize. Do not share a single-pass report; finish only after reaching shared understanding. Do not create or change a glossary or ADR unless the grill independently identifies a genuine domain-language or durable architectural decision that meets its own criteria.

## Step 9: Validate and Hand Off

Re-read the final report against the exact bundle and verify:

1. PR URL, full commit, short SHA, suite names, job numbers, counts, and testcase revisions match JSON evidence.
2. Every requested suite appears either as collected or as an explicit warning.
3. Every `failure`, `error`, and unknown test result appears exactly once in the inventory and in one root-cause category.
4. Totals reconcile across the snapshot, inventory, categories, and executive summary.
5. Observations, inferences, and unknowns are clearly separated.
6. The report contains no token, authorization header, signed artifact URL, or unrelated local change.

Return the report path, exact analyzed commit, failure/error/unknown counts by suite, unavailable-suite warnings, and the highest-priority next action. Leave the report uncommitted and unpushed unless the user asks for publication.
