# Handoff: add merge-base CI comparison to existing CUBRID skills

## Next session objective

The user wants the useful baseline-comparison workflow from the CBRD-27443 investigation applied to the **existing skills**. Update the skill sources in this repository so an agent diagnosing a PR's failed CI first looks for CI evidence at the exact merge base of the PR target and head, compares actual failure signatures, and distinguishes pre-existing failures from additional PR failures before proposing repairs or expecting every failure to disappear.

This session only writes this handoff. Implementing or installing skill changes is the next agent's work. The user explicitly requested this file under `/home/vimkim/gh/my-cubrid-skills`, overriding the invoked `handoff` skill's default temporary-directory destination. Do not move it to a temporary directory.

## Read first / suggested skills

Invoke these skills through the Skill tool if available, otherwise read their source instructions:

- `writing-for-agents`: make workflow branches and completion criteria explicit; keep shared rules in one authoritative place.
- `cubrid-ci-analyze`: primary behavior to revise; preserve its exact-head collection and validation guarantees.
- `cubrid-common`: shared CI provenance and fallback rules; reconcile them with the analyzer.
- `cubrid-ci-trigger`: inspect the analysis/trigger boundary; change only if a pointer or necessary clarification is missing. Baseline lookup must remain read-only.
- `track-work`: register the skill implementation if it crosses sessions or will take at least 30 minutes; keep it distinct from the Engine implementation item 261.

Read repository `AGENTS.md` and `/home/vimkim/my-cubrid/CUBRID.md`. Work on a topic branch in a sibling worktree; inspect live branches/status before acting. Edit source skills here, not installed copies under `.agents/skills`. Follow the current repository approval requirements for `just sync`, commit/push and verification, resolving them against the user's higher-priority instructions. Writing this handoff does not authorize installing or publishing skills.

## Authoritative artifacts — use references, do not copy the investigation

- Full comparison report: `/home/vimkim/gh/my-cubrid-docs-27443-base-ci/cbrd-27443/ci_analysis_report_0809a48_codex.md`.
- Report commit: `f4e43ae`, branch `docs/cbrd-27443-base-ci`, in the worktree above. At handoff time this documentation branch has **not** been merged or pushed; the previous turn asked for confirmation. The current user request is for a handoff, not that merge.
- Structured comparison, validation and baseline verdicts: `cbrd-27443/ci_analysis_0809a48_run37416284168/` beside the report.
- Targeted baseline lookup evidence and experimental scripts: `/home/vimkim/.cache/cbrd27443-base-ci.UU8jOl/`. These are investigation artifacts, not production helpers to install unreviewed.
- Existing complete head collector bundle: `/home/vimkim/.local/share/cubrid-ci-data/github-actions/CUBRID-cubrid/pr-8094/0809a480df55ac6767a905d03fa3d31edd40a93c/`; pin observation `20261006T070427.660168257Z-1551569-0` and run `37416284168`, attempt 1. The root manifest may change in later collections.
- [Engine PR 8094](https://github.com/CUBRID/cubrid/pull/8094), [exact merge-base CI](https://github.com/CUBRID/cubrid/actions/runs/37027696235), [head CI](https://github.com/CUBRID/cubrid/actions/runs/37416284168).

Use the report for actual failure inventories, counts, causes, confidence and limitations. The durable lesson is that baseline evidence accounted for most failures, including a real assertion crash; it narrowed the PR-specific investigation without proving universal absence of regressions. The rewritten tests' CI pickup/pass evidence is also recorded there.

## Likely source changes and current gap

Inspect these files and their current tests before choosing the final scope:

- `cubrid-ci-analyze/SKILL.md`
- `cubrid-ci-analyze/scripts/report_mode.py`
- `cubrid-ci-analyze/tests/test_report_mode.py` and fixtures
- `cubrid-common/references/ci-evidence.md`
- `cubrid-ci-trigger/SKILL.md` and `references/gha-ci-operations.md`, only for relevant boundary/pointer consistency

The analyzer currently forbids direct provider APIs and requires the current published PR head for collection. The common evidence reference permits separate read-only API evidence when the collector is unsupported/unavailable/incomplete. The successful investigation used such a separate lookup because the collector could not collect an arbitrary historical merge-base commit as the current PR head. **Resolve this policy gap explicitly** rather than instructing agents to quietly bypass the analyzer or mislabel raw evidence as a validated collector bundle.

Inspect the live `/home/vimkim/gh/cubrid-ci` CLI and schemas before assuming this limitation still exists. Prefer a supported collector capability if available. If production support requires changes to that separate repository, describe the dependency and scope; do not silently expand a skills-only task into a CLI implementation. Shared evidence guidance may contain stale collector-schema assumptions; reconcile only what this workflow requires against the live schema.

## Behavior to encode

1. **Pin identities before comparison.** Capture repository, PR number, actual target branch, full head SHA, target tip SHA and observation time. Resolve their exact merge base with pinned commits. The target tip is not itself the merge base. Handle targets other than `develop` when supported. Preserve multiple-base or unavailable-history ambiguity rather than silently picking a convenient commit.
2. **Find existing baseline evidence first.** Search exact-commit statuses/checks and linked Actions runs, then inspect candidate run metadata, attempt, plan and build/test records. The successful lookup was a `workflow_dispatch` run, so a `pull_request`-only filter is insufficient. Record provenance and pagination/coverage limits.
3. **Prove the tested Engine identity.** GitHub Actions `head_sha` can identify workflow code instead of the tested Engine; a search by that field returned many unrelated PR runs in this investigation. Commit-status links and run titles are discovery hints, not sufficient identity proof. Validate tested Engine SHA using plan/build evidence. Distinguish synthetic merge trees, workflow revision, tested Engine revision and reused build origin. Build run ID need not equal test run ID when exact-SHA reuse is verified.
4. **Preserve validation boundaries.** Keep the one status / one exact-head collection and its schema/observation/integrity checks. Save any approved historical API lookup separately with explicit identity, acquisition scope and digests. Never manufacture a schema-v2 manifest or promote targeted baseline reads into a fully validated collection. An integrity mismatch is not a reason to bypass validation through another endpoint.
5. **Compare cases, signatures and inputs.** Cover requested suites with reconciled counts. Classify head failures as also observed on the base, additional on the head, or uncomparable; record base-only failures separately. Match exact case paths and actual messages/diffs/stacks, not just counts or basenames. Record independent public/private testcase revisions, build mode and relevant configuration. Check local Git objects for testcase/answer/helper equality where available; absent objects mean an explicit limitation.
6. **Keep causal claims bounded.** Same case plus matching signature supports a pre-existing signature; it does not prove identical root cause or excuse a crash. Base-pass/head-fail is a candidate regression or compatibility issue, not automatic proof that Engine behavior is wrong. Differing test revisions/configuration weaken attribution. Each hypothesis needs evidence, confidence, unknowns, a falsifier and a concrete next action.
7. **Handle missing evidence honestly.** No exact run, expired artifacts, inaccessible checks, partial suites or an ambiguous tested revision mean unknown/incomplete baseline, not baseline pass or PR regression. Nearby-commit evidence may be context only and must never be presented as exact merge-base CI. A missing baseline must not invalidate an independently validated head inventory, but must constrain comparative conclusions.
8. **Keep investigation read-only.** Lookup does not authorize new CI, cancellation, PR comments, repairs, testcase branch creation or any local merge. If a controlled same-test-revision comparison is needed, report the proposed experiment and leave triggering to the authorized CI workflow. Do not automatically waive project CI requirements because failures pre-exist.

Use concise main-path instructions with a conditional reference/helper for baseline acquisition details. Avoid copying long API recipes across multiple skills. Decide whether baseline lookup should be the default when attributing failures, while keeping simple status requests lightweight.

## Validation and acceptance

Use existing repository validation commands and meaningful fixture-based tests for any new executable logic. Cover these distinctions where the implementation introduces them:

- Exact dispatch baseline found versus unrelated run sharing the workflow SHA.
- Verified same-Engine cached build from another run versus wrong Engine artifact.
- Same failure signature on both sides; additional head failure; baseline-only failure.
- Different testcase revisions with identical affected files versus unverified sources/configuration.
- Missing/partial baseline and identity mismatch without false pass/regression claims.
- Newer attempts, suite selection and incomplete head evidence retaining existing report-mode constraints.

Completion means the source instructions consistently describe discovery, identity proof, bounded comparison and no-baseline behavior; applicable validation passes; the report format captures comparative evidence and limitations; and installed/publication actions follow the user's approval policy. Use the existing CBRD-27443 artifacts as a read-only worked example, not as hard-coded IDs or a reason to launch another CI run.

## Session state to preserve

The handoff was written from the clean `my-cubrid-skills` main checkout at `6e8a014`; recheck live state before starting. No skill implementation, installation or publication was performed in this handoff session. Other worktrees already exist; preserve them.

Engine PR work remains separate. Work item 261 records the completed baseline analysis and two additional legacy shell checks awaiting targeted diagnosis. The user's prohibition on locally merging the Engine or Tests branches still applies. Do not resume those repairs or the pending docs merge as a side effect of skill work.
