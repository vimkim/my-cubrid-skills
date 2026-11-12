---
name: cubrid-code-review
description: "Review CUBRID pull requests, commit pairs, or supplied diffs with budgeted specialist agents. Verify code defects across C/C++, concurrency, storage I/O, recovery, and HA. Produce an evidence-backed report and a handoff for unfinished review. For requested PR reviews, publish the report to my-cubrid-docs main and post a Korean summary with its link. Use when reviewing CUBRID engine changes. Triggers on phrases like 'review this CUBRID PR', 'review diff A B', 'cubrid-code-review'."
---

# Review CUBRID code

Review the supplied change at fixed revisions. Use about five specialist agents for a typical engine PR. Scale by affected invariants and subsystem boundaries.

The coordinator owns scope, budget, verification resources, and the final verdict. Reviewers investigate code. They do not fix the submitted change.

Use pstack's adversarial and blast-radius methods inside these assignments. The reviewer contract defines the adapted procedure. Running separate `interrogate`, `blast-radius`, or `arena` panels is unnecessary.

## 1. Pin the review scope

Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy) and its applicable user context. Read the target repository's applicable `AGENTS.md` and contribution rules. Preserve unrelated changes.

Resolve the request into one comparison before delegation:

| Input | Comparison |
|---|---|
| PR URL or number with a known repository | Resolve the current base and head SHAs. Compare the merge base with the head. Record all three SHAs. |
| Two commits A and B | Compare the exact trees with `git diff A B`. Use a merge base only if requested. |
| One commit | Compare its parent with the commit. For a root commit, use the empty tree. For a merge commit, require the parent choice. |
| Supplied patch | Record its SHA-256 and provenance. Identify the base and head when possible. Mark missing source context as a limitation. |
| Working changes explicitly requested | Save the selected staged, unstaged, or combined patch and its hash. Record HEAD and untracked-file inclusion. |

Resolve refs with `git rev-parse --verify --end-of-options '<ref>^{commit}'`. Record the literal comparison command with full SHAs. Quote ref arguments safely.

For a PR, inspect its description and linked issue. Use an available GitHub connector for remote metadata. Local Git supplies complete source and history. If necessary, fetch the pinned objects without changing the user's checkout. Recheck that fetched SHAs match the metadata.

Save the complete changed-file list, diff statistics, and patch. Inspect renames, deletions, submodules, and binary changes. Check whether remote patches are truncated. Obtain missing hunks from pinned Git objects. If source remains unavailable, record the uncovered files.

Read source with `git show <sha>:<path>` or a detached review worktree at the pinned head. A dirty working copy does not establish the snapshot's behavior.

If the comparison is empty, record that result and continue with section 6 without reviewers. If a required input is ambiguous, resolve it before reviewing that scope.

Completion requires an immutable patch identity and an inventory of every changed path, including paths that cannot be inspected.

## 2. Establish the budget

Read [the budget policy](references/budget.md) before any agent launch. It defines the default bounded mode and how to honor an explicit absolute budget from the user. The budget never delays launching the planned reviewers.

Create a run directory outside the submitted source tree. Use separate paths for each reviewer. Save a manifest with these fields:

- Repository, request, comparison mode, full revision SHAs or patch hash, and snapshot time.
- Applicable policy and specification paths. Record missing specifications without blocking code-correctness review.
- Budget mode, per-reviewer scope and targets, any explicit user limits, available telemetry, enforcement mechanism or `none`, and the total review envelope with its coordinator reservation.
- Planned agents, model and reasoning settings, assignments, output paths, and verification resource ownership.

Use the user's configured models when available. Otherwise use available models suited to the assigned work. Avoid a fixed vendor or model dependency. Record actual choices. Preserve enough reasoning capacity for concurrency and recovery analysis by narrowing scope first.

If pstack model settings exist, use the `interrogate reviewers` list as the specialist model pool. Read the harness's configured settings file. For Codex, check `~/.agents/pstack-models.md`. For Claude Code, check `~/.claude/rules/pstack-models.md`. For Cursor, check `~/.cursor/rules/pstack-models.mdc`. Assign distinct available models to a shared challenge when possible. Report unavailable models or reduced diversity. Model selection does not increase the agent count or override the budget.

When work uses parallel agents or crosses sessions, use `track-work` if available. Keep the pinned identity and next action in the work item.

Completion requires a recorded budget mode, a finite scope and target for each planned reviewer, and a total envelope that reserves coordinator verification. A prompt that asks an agent to limit itself is a target, not hard enforcement; the report discloses this.

## 3. Assign coverage

Read [the reviewer contract](references/reviewers.md). Build a coverage table before launching reviewers. Each row names a changed subsystem or invariant, its primary reviewer, source paths, and required verification.

Use these five roles for a typical engine PR:

| Reviewer | Primary responsibility |
|---|---|
| Systems | C/C++ correctness, ownership, Linux interfaces, and error handling. |
| Concurrency | Synchronization, lifetime across threads, transaction isolation, and consistency. |
| Storage and performance | Disk I/O, page and buffer behavior, Linux performance, and resource growth. |
| Recovery | WAL, undo and redo, atomicity, durability, crash recovery, and vacuum interactions. |
| HA | Replication, failover, replay, compatibility, and interactions between components. |

For a small change, combine roles into fewer agents. Mark irrelevant roles with a code-based reason. For a large change, split a role by an actual subsystem or invariant. Add agents only within the budget policy. Line count alone does not justify expansion.

Assign each hunk a primary owner. Assign callers and affected invariants too. Give cross-domain boundaries a named owner, such as vacuum slot reuse across concurrency and recovery. Reviewers may trace unchanged code to establish a defect introduced or exposed by this change.

For the one or two most consequential boundary risks, assign the same question to two existing reviewers. Give both identical pinned scope, intent, and safety conditions. Keep their initial answers independent. Record the shared question and both owners in the coverage table. If a second seat cannot fit, record the missing independent challenge.

The coordinator covers documented standards and specification conformance across the assignments. Avoid launching a separate generic style-review panel.

Each brief contains the user's goal, pinned identity, role, assigned paths, invariants, relevant context pointers, budget, output path, and completion conditions. Include any shared challenge question and the safety fact to test. Point to this skill and the reviewer contract. Do not copy the entire conversation into every brief.

Completion requires an owner for every changed path and every identified cross-domain risk, or an explicit coverage gap.

## 4. Review and verify

Launch the planned agents with fresh, bounded context. In Codex, use `spawn_agent` with `fork_turns="none"` when available. In Claude Code, use the available general-purpose subagent tool. Pass supported budget controls only. Reviewers must not spawn other agents.

Keep submitted source read-only. Each reviewer writes only its own report and isolated evidence. The coordinator schedules builds and runtime checks. Concurrent source readers may share a pinned checkout. Tests that alter databases, services, install prefixes, or resource pressure run in separate environments or serially.

Reviewers read their assigned code before reading other reviewers' conclusions. They trace success, failure, cleanup, and relevant concurrent or crash paths. Require evidence for every claimed violated invariant.

Each reviewer follows the contract's impact-tracing and adversarial steps. Trace a material dependency beyond direct callers. Test the fact that makes the affected behavior safe. Produce a reproducible failure or a bounded safety check against real code. Keep source-only concerns visible as unverified risks.

Use the narrowest suitable verification workflow when available:

- `cubrid-build` for engine builds and configured ctest tests.
- `cubrid-test-sql-run`, `cubrid-test-medium-run`, or `cubrid-test-shell-run` for focused native regressions.
- `cubrid-verify-vacuum-slot-undo` when its vacuum, OOS, or recovery-insert trigger applies.
- `cubrid-oos-context` when required OOS behavior affects the verdict.
- `cubrid-jira` for linked CBRD requirements. Search local design documents before external research.
- `cubrid-manual-search` for documented contracts. Source code establishes undocumented implementation behavior.
- `cubrid-ci-analyze` for existing evidence at the pinned engine and testcase revisions.
- `cubrid-performance`, `linux-perf`, or `benchmark-checklist` when an actual performance investigation is necessary.

Read a helper skill only when that branch applies. If it is unavailable, use an equivalent reproducible check or record the missing verification. These helpers run inside the existing assignment and budget. They do not authorize additional agents or external publication.

Keep test harness changes in a disposable workspace. Record source, testcase, build, and configuration identities. A failed reproduction remains inconclusive when prerequisites are missing. Existing CI success does not establish an untested recovery or interleaving invariant.

At the budget checkpoint, collect completed evidence and unresolved checks. Stop affected work at its target or explicit limit. Do not restart an agent to evade its budget. Preserve partial findings and create a handoff.

Completion requires a terminal result or an explicit gap for every assignment. An interrupted agent does not count as a pass.

## 5. Adjudicate the findings

Read each saved reviewer report. Reject a report that uses the wrong revision or lacks the assigned coverage evidence. Correct the assignment only within the remaining budget. Otherwise record the gap.

Recheck each candidate against the actual diff, relevant callers, and applicable contracts. Search for guards, ownership transfers, and recovery behavior that could disprove it. Compare the base behavior when needed to establish change attribution.

Accept a confirmed finding only after a run against real code demonstrates the wrong behavior and breaks the stated intent. Rerun the reviewer's command against the pinned implementation. Check the expected result, actual result, and change attribution. Record the coordinator's independent replay evidence. An exit code alone does not establish the defect.

A reproducible compiler failure in a supported build also provides execution evidence. Distinguish a source defect from missing build prerequisites.

If replay is unavailable or inconclusive, retain the candidate as an unverified risk. A complete source argument remains useful evidence there. Preserve its feasible schedule or crash sequence. A passing stress run does not disprove a race. Do not silently drop a material concern because its reproduction is expensive.

Deduplicate findings by root cause. Preserve the highest supported impact and all affected paths. Keep unproven concerns in open questions. Reviewer agreement alone does not prove a finding. A credible unresolved data-loss or concurrency concern requires follow-up.

Use an extra specialist only for a named unresolved question and an allowed budget allocation. Avoid automatic second full reviews. Classify pre-existing defects separately from defects introduced or exposed by the reviewed change.

Completion requires a disposition for every candidate and a completed coverage table. Distinguish disproven candidates from candidates awaiting execution. Record dropped counts and reasons by reviewer. Carry material unproven safety facts and missing independent checks into the handoff.

## 6. Save the report and handoff

Read [the report contract](references/report.md). Save `report.md`, `coverage.md`, and the manifest in the run directory. Use English unless the user requests another report language. Keep raw logs separate from the narrative.

Always state whether follow-up review is required. Create `handoff.md` when a required check remains, the budget ends early, reviewers disagree on a material risk, evidence is missing, or the PR moves.

Before finalizing a PR review, recheck the remote base and head SHAs. If either changed, keep the report tied to its original snapshot. Add the required delta review to the handoff. Do not restart automatically.

For an explicit PR-review request, continue with [PR publication](references/pr-publication.md) unless the user requests local-only results. The user's standing workflow authorizes integrating the review documents into `my-cubrid-docs/main`, pushing that branch, and posting a Korean PR summary with the report's `main` link. Reuse that authorization without another confirmation. Commit-pair, patch, and working-change reviews stay local unless publication is separately requested; discovering a related PR does not change their mode.

This publication scope covers review documents and a PR-page comment. Formal GitHub review submissions, source fixes, CI triggers, and source-branch merges or pushes require their own authorization.

End with the highest-impact findings, coverage limits, budget status, follow-up decision, and artifact locations. For published PR reviews, include the report and comment URLs. Report any unfinished publication step explicitly. A zero-finding result means no confirmed defect within the inspected scope. It does not certify the PR as safe to merge.
