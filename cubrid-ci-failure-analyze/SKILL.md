---
name: cubrid-ci-failure-analyze
description: Discover the current-head CircleCI result for a CUBRID GitHub PR, retrieve failed test-case lists and failure messages (especially test_shell), or analyze those failures against test scripts, answer files, and source changes. Use when the user gives a CUBRID PR URL and asks for recent CI results, asks for failed TCs, shares a CircleCI URL or failed_tc.txt, or wants root-cause analysis of CI failures.
---

# CUBRID CI Test Failure Analyzer

Analyze failed shell test cases from CircleCI (or other CI) for CUBRID PRs. Produces a categorized report with root cause analysis and fix proposals.

## When to Use

- User says "analyze ci failures", "CI 실패 분석", "왜 TC 실패했어", "failed tc 분석"
- User gives a GitHub PR URL and asks for the recent/current CI result or `test_shell` failed-TC list
- User shares a CircleCI URL with test failures
- User has a `failed_tc.txt` or similar list of failed test cases
- User wants to understand why shell tests failed on a PR

## Arguments

- `/cubrid-ci-failure-analyze` — Interactive: look for `failed_tc.txt` in cwd
- `/cubrid-ci-failure-analyze <github-pr-url>` — Resolve the PR's current head to its CircleCI jobs and fetch failures
- `/cubrid-ci-failure-analyze <circleci-url>` — Fetch failures from a known CircleCI job
- `/cubrid-ci-failure-analyze <file>` — Read failure list from specified file

## Inputs

The skill needs:

1. **CI identity**: A GitHub PR URL, a CircleCI job URL/build number, or a failed-TC file
2. **Test case directory**: A directory containing the actual test scripts and answer files (e.g., `~/cubrid-testcases-private-ex`)
3. **Feature context**: The branch/PR being tested (to understand what changes might cause failures)

## Report Identity and Location

Resolve the report identity before writing any draft:

1. Set `AGENT` from the active AI host's runtime identity. Use `codex` for Codex and `claude` for Claude Code. For another host, use its stable lowercase agent name. Do not infer the host from installed binaries because multiple AI CLIs may coexist; if runtime identity is unclear, ask the user.
2. Set `SOURCE_COMMIT` to the commit actually tested by CI. Prefer the CircleCI/build revision, then the PR head SHA. Only when neither is available, use `git rev-parse HEAD` in the CUBRID source worktree. If the explicit CI/PR commit differs from local `HEAD`, keep the explicit subject commit; never label the report with an unrelated local commit.
3. Validate `SOURCE_COMMIT` and take its first seven hexadecimal characters as `SHORT_SHA`.
4. Extract the first `CBRD-XXXXX` from the PR title, PR body, branch, or user input and normalize the directory to lowercase. If no ticket can be determined, ask the user before writing.
5. Require `/home/vimkim/gh/my-cubrid-docs` to exist, create its `cbrd-xxxxx/` ticket directory if needed, and set:

   ```text
   REPORT_PATH=/home/vimkim/gh/my-cubrid-docs/cbrd-xxxxx/ci_failure_report_<SHORT_SHA>_<AGENT>.md
   ```

For example, Codex analyzing commit `f5794fb...` writes `ci_failure_report_f5794fb_codex.md`; Claude Code writes `ci_failure_report_f5794fb_claude.md`. Compute `REPORT_PATH` once and reuse it for the initial draft, grill loop, and final handoff. Never fall back to the CUBRID source root or current working directory.

## Execution Steps

### Step 1: Gather Inputs

1. Locate the failed TC list:
   - For a GitHub PR URL, run the bundled current-head fetcher described in **PR to CircleCI Discovery** below
   - Check arguments for a file path or CircleCI URL
   - Check cwd for `failed_tc.txt`
   - Ask user if not found
2. Identify the test case base directory:
   - Check if `~/cubrid-testcases-private-ex` exists
   - Check additional working directories
   - Ask user if not found
3. Identify the feature branch context:
   - `git branch --show-current`
   - `git log --oneline HEAD --not develop | head -20` to understand feature changes
4. Resolve `AGENT`, `SOURCE_COMMIT`, `SHORT_SHA`, the CBRD ticket, and `REPORT_PATH` using **Report Identity and Location**.

### Step 2: Fetch CI Failure Details

Fetch the complete CircleCI tests response, not only names. Preserve `tests.json` and `failed-tests.json`; each failed test's `message` may contain the actual/expected diff, console output, fatal error, or timeout needed for root-cause analysis. Keep `failed-tc.txt` as the compact inventory.

## PR to CircleCI Discovery

For a GitHub PR URL, use the bundled helper first:

```bash
run_dir=$(mktemp -d -t cubrid-ci-fetch.XXXXXX)
bash <skill-path>/scripts/fetch-pr-circleci.sh \
  'https://github.com/CUBRID/cubrid/pull/6864' test_shell "$run_dir"
```

The helper performs this exact chain:

```text
PR URL
  -> GitHub PR current head SHA (`headRefOid`)
  -> that commit's status context `ci/circleci: test_shell`
  -> CircleCI job number from `target_url`
  -> CircleCI v1.1 job metadata
  -> verify job `vcs_revision` == PR head SHA and `workflows.job_name` == test_shell
  -> CircleCI `/tests` response
  -> `failed-tc.txt` + full failure JSON
```

Artifacts are `summary.json`, `job.json`, `tests.json`, `failed-tests.json`, and `failed-tc.txt` in the new output directory. Read `summary.json` first, then the compact list, then targeted failure messages from `failed-tests.json`.

Treat **current** as "attached to the PR's current head SHA," not "the numerically highest CircleCI job" and not "the newest report found in local docs." Long-lived tracking PRs have many obsolete jobs. Never fall back to an older SHA when the current status is absent or pending; report that no completed current-head result exists.

For manual inspection, the equivalent discovery commands are:

```bash
head_sha=$(gh pr view <pr-number> --repo CUBRID/cubrid --json headRefOid --jq .headRefOid)
gh api "repos/CUBRID/cubrid/commits/$head_sha/status" \
  --jq '.statuses[] | select(.context == "ci/circleci: test_shell")'
curl -fsSL "https://circleci.com/api/v1.1/project/github/CUBRID/cubrid/<job-number>"
curl -fsSL "https://circleci.com/api/v1.1/project/github/CUBRID/cubrid/<job-number>/tests"
```

Use `gh pr checks` only as a convenient human-readable overview. Use the current-head commit status plus CircleCI job metadata for machine validation because GitHub Actions checks and legacy CircleCI status contexts are different API surfaces.

### Step 3: Read All Failed Test Cases (Parallel)

For each failed TC:

1. **Read the test script** (`.sh` file in `cases/` directory)
2. **Read the answer file** (`.answer` file — expected output)
3. **Read supporting SQL files** (`.sql` files used by the test)
4. **Note what the test does**: data types involved, operations tested (CRUD, unload/load, copydb, diagdb, etc.)

Use parallel reads — launch all file reads at once since they're independent.

### Step 4: Analyze Feature Changes

Understand what the feature branch changes that could cause failures:

1. Read key modified source files (use `git diff develop...HEAD --stat`)
2. Identify behavioral changes:
   - New file types or storage mechanisms
   - Changed output formats (diagdb, show heap header, etc.)
   - Disabled or stubbed functions
   - New error codes or changed error messages
3. Use explore agents in parallel for deeper code analysis if needed

### Step 5: Categorize and Analyze

For each failed TC, determine:

1. **Is it related to the feature?** — Match test operations against feature changes
2. **Root cause hypothesis** — Why the test fails given the feature changes
3. **Category** — Group TCs by shared root cause

Common categories:
- Output format mismatch (answer file needs update)
- Disabled/stubbed functionality
- New storage path not handled by existing tool (unloaddb, copydb, etc.)
- Error code changes
- Timeout / CI flakiness
- Unrelated regression

### Step 6: Generate Report

Write a structured markdown report with:

```markdown
# Failed TC Analysis Report: <branch> (<PR link>)

## Background
(Feature description, key behavioral changes)

## Category N: <Root Cause> (X TCs) — <OOS-related? / Feature-related?>

| # | TC | What it tests | Failure | Related? |
|---|-----|--------------|---------|----------|
| ... | ... | ... | ... | ... |

**Root cause analysis**: ...
**Proposed fix**: ...

## Summary

| Category | Count | Related? | Root Cause |
|----------|-------|----------|------------|
| ... | ... | ... | ... |

## Priority Actions
1. P0: ...
2. P1: ...
```

### Step 7: Save and Present

1. Save the report to `REPORT_PATH`.
2. Print `REPORT_PATH`, the analyzed seven-character commit, the agent name, and a concise summary with counts: X related, Y unrelated, Z total.

## Output Conventions

### Language

- **Section headers (`##`)**: English
- **Table content and analysis**: English (technical report for broad audience)
- **Code, paths, function names**: Keep as-is

### Style

- Tables for TC listings within each category
- Code blocks for call flow diagrams showing broken vs expected paths
- Bold for key findings and root causes
- Backticks for all code references
- Horizontal rules between major sections

## Tips

- **When in doubt about source code behavior, use LSP (clangd)** to analyze CUBRID C/C++ code. Use `lsp_hover` to check types, `lsp_goto_definition` to trace function implementations, `lsp_find_references` to understand call sites, and `lsp_diagnostics` to catch issues. This is especially useful when tracing how a changed function affects downstream callers.
- **When fetching CircleCI results, use API v1.1** for the job and tests endpoints. Example: `https://circleci.com/api/v1.1/project/github/CUBRID/cubrid/<build_num>/tests` currently works without credentials. If it returns an authentication error, report that boundary instead of scraping the CircleCI UI.
- Always read the actual test script AND answer file — the script tells you what operations are tested, the answer tells you what output is expected
- Look for data types that exceed storage thresholds (e.g., `varchar(20000)`, large JSON, CLOB/BLOB)
- Check for `diagdb`, `show heap header`, `cubrid spacedb` in test scripts — these are sensitive to storage format changes
- Check for `unloaddb`/`loaddb`/`copydb` — these require full record resolution
- TCs with no diff details from CI may need local reproduction to diagnose
- Group by root cause, not by symptom — multiple TCs often share a single underlying issue

## Mandatory for Analysis Reports: Iterate with Grill-with-Docs

Every CI failure **analysis report** must go through `/grill-with-docs` before being shared. A discovery-only request that returns the current job identity, status, counts, or failed-TC list does not create an analysis report and does not require the grill loop. Do not deliver a single-pass triage. Single-pass triage drifts toward weak root-cause hypotheses, mis-categorized TCs, and unsupported "Related?" calls. CI reports often drive merge or release decisions where mis-attribution is expensive.

This step is required, not optional. It applies to every report. No agent-side judgment — including size, scope, perceived triviality, or perceived risk — is a valid skip criterion. The only legitimate skip is when the user, in the message that triggered this skill, explicitly says "skip grill" or "don't grill this" (or unambiguous equivalent: "no grill", "skip the grill loop", "just push it"). If in doubt, do the grill loop.

**How to hand off:**

After saving the initial report to `REPORT_PATH`, invoke `/grill-with-docs` with:

- **Topic & purpose**: CI failure analysis for `<branch>` / `<PR link>`, audience is the PR author, QA, and CUBRID maintainers
- **Output path**: the same report file (the loop revises in place)
- **Source material**: the failed TC list, CircleCI output, the actual test scripts and answer files, `git diff develop...HEAD` summary, key modified source files
- **Review angle**: every "Related?" call is justified by a concrete behavioral change, root-cause hypotheses are testable (not hand-wavy), proposed fixes are concrete (file/function-level), categorization groups by underlying cause not symptom, Priority Actions are actionable
- **Round cap**: default 5
