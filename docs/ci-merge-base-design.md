# Exact merge-base CI comparison design

## Accepted behavior

- PR failure analysis attempts exact merge-base comparison by default. Status-only requests remain lightweight.
- Missing or incomplete baseline evidence does not block an independently validated head report. Comparative conclusions remain unknown where evidence is missing.
- A matching failure signature is recorded separately as pre-existing evidence. It neither proves the same root cause nor waives applicable CI requirements.
- Provide a deterministic CLI for CI collection by Engine commit SHA, use Git to resolve the PR target/head merge base where sufficient, and provide a wrapper to collect that baseline.
- Extend the existing `cubrid-ci` repository with `collect-commit <sha>` and `collect-base <pr>` commands, sharing commit collection logic.
- Select the latest relevant execution per requested suite, recording run and attempt. A newer incomplete execution remains incomplete; an older success never silently replaces it. Provide an explicit run selector for historical investigation.
- Fetch missing pinned commits and ancestry into a dedicated Git cache without changing working branches. Use `git merge-base --all`; zero or multiple bases are unresolved.

## Verified implementation constraint

At source commit `45944012aaaa4ba985f22775cf715bbcdf121f78`, `cubrid-ci collect --commit` requires the supplied commit to equal the current published PR head. Historical commit collection therefore needs implementation support. GitHub Actions workflow `head_sha` alone does not prove the tested Engine revision; existing shard build provenance validation must remain authoritative.

## Confirmed implementation contract

The user confirmed the design through Q7. Deterministic commit selection, acquisition, and validation belong in `cubrid-ci`; failure-signature comparison and causal interpretation belong in the analysis skill. The shared comparison contract is [ci-baseline.md](../cubrid-common/references/ci-baseline.md).

The CLI adds command/manifest v3 and observation v2 for commit/base collection, retaining the current PR command's v2/v1 envelopes and the existing v2 suite/raw/failure schemas. Exact-commit status/check links supply candidates; an explicit run selector handles missing links without a speculative repository-wide scan. Older attempts require existing validated local evidence because the remote artifact paths are not attempt-addressable.

Implementation is in the sibling `cubrid-ci-commit-baseline` worktree on `feat/commit-baseline-collection`. The skill source worktree is `my-cubrid-skills-ci-merge-base-comparison` on `skill/ci-merge-base-comparison`. Installation, local integration, and publication remain separate completion actions under the user's workflow.

## Verification

The CLI's `just verify` passed 102 tests plus formatting, all-target checks, and Clippy. Read-only live `collect-commit` and `collect-base 8094` both collected the exact baseline shell evidence: dispatch run 37027696235, reused build run 36993422045, 3 failures, complete collection. The implementation repository records the pinned observations in `docs/verification/commit-baseline-collection.md`.

The analyzer report-mode tests pass, including missing/invalid baseline preserving a full head report, partial baseline permitting only validated cases, and complete baseline never upgrading incomplete head evidence. Signature and input-equivalence judgments remain agent analysis under the shared contract, not a new automated causal classifier.
