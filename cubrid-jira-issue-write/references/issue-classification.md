# Issue classification

Read this reference when classifying an issue or suggesting broader categories or issue types. Recommend classification from the problem; a tentative type does not have to block a useful draft.

## Separate the classification axes

- **Project:** The repository or product responsible for the issue. The legacy guideline lists CBRD, APIS, CUBRIDMAN, TOOLS, and CUBRIDQA. This writer's artifact and publication workflow currently targets `CBRD-XXXXX`; a suggested category does not expand it to other projects.
- **JIRA issue type:** The kind of work tracked by the project. The legacy types below are a baseline, not proof of current field availability.
- **Problem category:** A concern such as reliability, compatibility, or test coverage. An issue may have more than one. These are writing and routing suggestions; use an existing label only when appropriate.
- **Component:** The affected module or subsystem. Select modules supported by evidence; add others as analysis discovers them. A concern such as reliability is not automatically a module name.

Suggest the type, relevant categories, and known components in the drafting handoff. Keep them out of live field mutations unless that action is authorized. Verify current project metadata before any authorized field change. Writing or publishing a description does not authorize creating types, labels, or components, changing priority, assigning owners, or transitioning status.

## Baseline JIRA types

| Type | Use when | Boundary |
|---|---|---|
| Correct Error | Observed behavior violates a known requirement or expected behavior. | A regression is a useful category here. Attribute the expectation when its status is disputed. |
| Improve Function/Performance | Existing behavior works but falls short of a justified capability, usability, or performance need. | A performance regression can instead be Correct Error when it violates an established requirement; classify from evidence. |
| Development Subject | A needed capability is absent. | Explain the blocked use case before proposing an architecture. |
| Refactoring | Structure, dependencies, or maintainability need improvement while intended external behavior is preserved. | Explain concrete maintenance cost or risk, rather than asserting that cleanup is beneficial. |
| Internal Management | Internal administrative or housekeeping work, such as version management. | Developer-facing improvements can still belong to another type; internal users alone do not determine the type. |
| Task | A bounded deliverable or investigation does not fit the other types well. | The old guideline discourages it as a fallback. Prefer a more precise fit when available; use Task when it accurately represents the work. |
| Sub-task | Part of an existing parent issue needs its own assignment and completion boundary. | State the parent relationship; this is decomposition, not the problem's technical category. |

## Suggested problem categories

Choose categories that help explain impact and route work. This is a menu, not a checklist for every issue, and none of these names asserts that a matching JIRA value exists.

| Category | Typical problem and triage evidence | Likely baseline type |
|---|---|---|
| Correctness / data integrity | Wrong results, corruption, or broken invariants; expected versus actual evidence. | Correct Error |
| Regression | A supported scenario worsened after a change; compared builds and reproduction conditions. | Correct Error; Improve Function/Performance when the expectation remains unagreed |
| Performance / resource efficiency | Latency, throughput, CPU, memory, disk, or network cost; workload and baseline measurements or attributed reports. | Improve Function/Performance; Correct Error for an established violation |
| Reliability / recovery | Crashes, hangs, failed recovery, or availability gaps; failure conditions and operational consequences. | Correct Error or Improve Function/Performance |
| Security / access control | A violated trust boundary or missing protection; supported exposure and consequences. | Correct Error, Improve Function/Performance, or Development Subject |
| Compatibility / migration | Upgrade, driver, platform, data-format, or interoperability friction; affected combinations and migration cost. | Correct Error, Improve Function/Performance, or Development Subject |
| Operability / observability | Difficult diagnosis, missing metrics, unclear errors, or manual recovery burden; the affected operator workflow. | Improve Function/Performance or Development Subject |
| Usability / accessibility | Error-prone commands, confusing interfaces, or access barriers; the task users cannot complete reliably. | Improve Function/Performance or Correct Error |
| Test quality / coverage | Flaky tests, missing regressions, weak verdicts, or costly setup; what escapes detection or wastes QA time. | Correct Error, Improve Function/Performance, or Task |
| Build / CI / developer tooling | Non-reproducible builds, unreliable automation, stale agent guidance, or tooling friction; blocked or repeated development work. | Correct Error, Improve Function/Performance, or Task |
| Documentation / specification consistency | Missing or conflicting instructions and behavior; resulting usage or validation errors. | Correct Error, Improve Function/Performance, or Task |
| Maintainability / technical debt | Coupling, duplication, or unclear ownership creates demonstrated change cost or risk. | Refactoring or Task |
| Investigation / feasibility | A consequential uncertainty prevents a decision; define the question, evidence to collect, and decision output. | Task; Sub-task under an existing problem |
| Release / dependency lifecycle | Release preparation, dependency updates, support transitions, or compliance deliverables; concrete obligations and dependencies. | Internal Management or Task; Correct Error for a specific defect |

For a cross-cutting capability, propose a feature label or component only if it improves routing; describe the need rather than assuming the value has been created.

## Possible new JIRA types

These are optional taxonomy proposals for a maintainer discussion. Use the baseline mapping until a type is verified as supported. Prefer categories or labels when they give sufficient visibility; extra types are useful when they need different ownership, evidence, or completion rules.

| Proposed type | Benefit and distinct completion result | Cost or ambiguity | Existing fallback |
|---|---|---|---|
| Investigation / Spike | Makes analysis-only work visible; completes with evidence, options, and a decision or next question. | Needs a bounded question and effort boundary; can otherwise become indefinite research. | Task or Sub-task |
| Test Improvement | Gives QA work explicit ownership and completion through reliable coverage or verdicts. | Overlaps defect fixes and CI work; avoid splitting a fix from its necessary regression test without a reason. | Correct Error, Improve Function/Performance, or Task |
| Documentation / Specification | Makes contract clarification and documentation deliverables visible. | Can split one behavior change across redundant issues; a category often suffices. | Correct Error, Improve Function/Performance, or Task |
| Compatibility / Migration | Tracks coordinated upgrade or interoperability outcomes and affected consumers. | Crosses bug, enhancement, and release work; useful mainly when coordination has a distinct owner. | Improve Function/Performance, Development Subject, or Task |
| Reliability / Operability | Highlights operational outcomes such as recovery, diagnosis, and availability. | Can overlap Correct Error and performance; clear service or operator outcomes are needed. | Correct Error or Improve Function/Performance |

Security, regression, and performance usually work well as categories because each can apply across multiple work types. Promote a concern to a new type only when a distinct workflow justifies the extra classification cost.
