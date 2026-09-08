# Create a CUBRID CI repair skill with human review

Label: wayfinder:map
Status: resolved

## Destination

Create and validate a CUBRID CI repair skill in this repository, and correct related CI/test skills where source inspection demonstrates errors. The workflow inventories PR CI failures, locates their test sources, maintains evidence in my-cubrid-docs, proposes root-cause fixes, applies approved fixes, and verifies them locally before requesting push approval.

## Notes

- The user explicitly included implementation on 2026-09-08. Execution is included in this map, overriding wayfinder's planning-only default.
- Confirmed skill names: `cubrid-ci-fix` and `cubrid-sql-run`. The user accepted the recommended layout: coordinator, independent analysis/trigger, specialized runners, and shared CTP preflight under cubrid-common.
- Tracker: local Markdown conventions in `/home/vimkim/.agents/skills/setup-matt-pocock-skills/issue-tracker-local.md`. Work-tracker item: 65.
- Consult `my-cubrid-skills-create`, `writing-for-agents`, `skill-creator`, and this repository's AGENTS.md for implementation. Consult existing `cubrid-ci-analyze`, `cubrid-ci-trigger`, `cubrid-build`, `cubrid-shell-run`, `create-testcases`, and `cubrid-isolation-test` for the audit; use `research` for research tickets and `grilling` plus `domain-modeling` for human decisions.
- Runtime suites: test_medium and test_sql use CUBRID_TESTCASES_DIR; test_shell uses CUBRID_TESTCASES_PRIVATE_EX_DIR. Also cover non-runtime checks such as formatting and licenses.
- Human approval is required after analysis and a concrete proposed fix, before source/test modifications. A second approval is required after successful local verification, before push. Retry automatically within approved diagnosis/scope; after approved pushes monitor CI until required checks pass. Each later push still requires approval.
- Required local preparation includes `git submodule update --init cubrid-jdbc` and `just configure-build`; verify actual recipes before encoding invocation syntax. Prefer existing focused runners over repeated full CTP setup.
- Keep skill edits in this repository. Reinstall, commit, and push of the skill collection require the separate completion confirmation specified by AGENTS.md.

## Decisions so far

- [Implement and validate the agreed CI repair workflow](issues/04-implement-and-validate.md): implemented, validated and reviewed; user authorized reinstall and publication to origin/main.
- [Decide repair approval and completion boundaries](issues/03-approve-workflow-boundaries.md): user accepted the four recommendations, including existing runners and post-push monitoring.
- [Choose reliable CI evidence and testcase identity sources](issues/01-audit-ci-evidence.md): retain exact-commit collector checks, add API coverage for gaps and miscellaneous checks, and verify testcase identity per test.
- [Choose faithful focused local test runners](issues/02-audit-local-runners.md): existing shell helper and CTP single-file SQL/medium cover focused execution; correct stale skills and require actual-case and installation evidence.

## Not yet specified

No remaining design questions from the audits. Any demonstrated need for a new framework will be proposed separately.

## Out of scope

Fixing a particular live PR during skill creation: no target PR was supplied. Running test suites or posting CI comments merely to draft the skill is unnecessary.
