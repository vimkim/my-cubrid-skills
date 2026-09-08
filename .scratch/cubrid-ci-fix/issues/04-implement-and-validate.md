# Implement and validate the agreed CI repair workflow

Type: task
Label: wayfinder:task
Status: resolved
Assignee: codex
Parent: ../map.md
Blocked by: 01, 02, 03

## Question

Does the implemented skill and each justified supporting-skill correction satisfy the agreed workflow, exact evidence identity, complete failed-TC inventory in my-cubrid-docs, approved repair loop, faithful local verification, and push gate? Implement the agreed changes under the map's explicit execution override, validate them with concrete workflow scenarios and source checks, and conduct the required live document review before requesting collection publication approval.

## Acceptance evidence

- The new SKILL.md exists in the requested repository and its name is confirmed.
- The audit covers runtime CI, miscellaneous checks, test creation, local shell execution, build preparation, and isolation guidance; every proposed supporting change traces to inspected source or an explicit user requirement.
- Runtime evidence covers test_shell, test_sql, and test_medium at one full source SHA, including missing/pending/error states without claiming they passed.
- GitHub Actions and CircleCI evidence paths are executable and verify run identity, attempts, and pagination where applicable.
- Each failed TC maps to an unambiguous Git-tracked path under the requested environment root; CI testcase revision and local revision are separately recorded.
- The durable failed-TC inventory lives in my-cubrid-docs, retains evidence links and attempt history, and separates runtime TC failures from non-runtime check failures.
- Root-cause analysis distinguishes observations, hypotheses, and unknowns, and justifies engine versus testcase edits before the first approval gate.
- The first gate presents a concrete proposed fix and scope; source/test mutations occur only after approval within the agreed retry boundary.
- Local preparation includes the requested JDBC submodule initialization and configure-build workflow, and recipes are grounded in actual local tooling.
- Focused validation verifies the intended installation, executed TC identity, nonzero execution count, results, and logs; skipped cases and infrastructure errors cannot become a pass.
- Failed verification leads back to the agreed repair loop. Successful verification produces a reviewable diff and evidence before push approval, covering every changed repository.
- Post-push behavior matches the user's answer and distinguishes a local pass from a successful PR CI result.
- New/changed executable helpers, if any, receive meaningful behavior validation. Skill frontmatter, references, scenarios, and approval boundaries are reviewed beyond syntax checks.
- Skill collection reinstall/commit/push remains behind its own repository-required completion confirmation.

## Implementation evidence

Created cubrid-ci-fix and the user-approved cubrid-sql-run; shared CTP preflight lives under cubrid-common/references. Corrected cubrid-ci-analyze, cubrid-ci-trigger, cubrid-build, cubrid-shell-run, create-testcases, and cubrid-isolation-test. README documents the accepted layout, and AGENTS lists the new skills.

Both new skills pass quick_validate. Eight changed/new skill identities and YAML frontmatter were checked, along with local Markdown links and git diff --check. The strict Codex validator rejects existing argument-hint metadata in older cross-host skills; that existing metadata was preserved and parsed separately. Independent [forward review](../research/forward-review.md) exercised five synthetic scenarios and inspected local medium setup; no concrete defect was demonstrated. No live CTP or CI execution was attempted for this documentation task.

The user reviewed the documents and authorized publication with “nice. commit and push.” The approved publication plan is just reinstall, just list, then commit/push the reviewed source changes and durable map/audits to origin/main. The isolated research branch is not a push target.

## Answer

Implementation and review are complete. The new coordinator and SQL/medium runner, six related workflow corrections, shared CTP preflight, and layout documentation satisfy the agreed workflow. Source validation and the linked independent scenario review provide the verification evidence; live PR repair is outside this skill-creation task. Publication is authorized and tracked through work item 65.
