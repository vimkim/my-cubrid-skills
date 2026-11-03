---
name: cubrid-jira-issue-write
description: Write or revise Korean CUBRID JIRA issues for triage, explaining the problem, its consequences, and the outcome needed for triage. Use for bug reports, improvements, new capabilities, investigations, and development tasks; publish completed reports to existing issues through cubrid-jira.
---

# CUBRID JIRA Issue Writer

Write an evidence-based issue that a colleague can understand without prior knowledge of the subsystem. Explain the problem, its consequences, and the outcome needed for triage. Leave implementation choices for ANALYSIS unless an existing decision applies.

## Authority and scope

Apply the user's current instructions over this skill's writing defaults and the [company OPEN guideline](https://dev.cubrid.org/dev-process/jira/open). The guideline is a legacy baseline for JIRA terminology and templates; it is not a requirement to finish a design before triage. Look up its current contents when field details matter; do not depend on a temporary local copy.

Add a one-line summary below the title. Preserve the team's four opening fields and explicit `AI-Generated Context` divider by default. These come from the user's request and the team's writing convention, rather than the official OPEN template. Keep the issue in concise, natural Korean 한다체, with English `##` headings and Korean `###` headings when needed. Explain unfamiliar terms once and retain identifiers as written. Follow an explicit user request to change the format.

Read [artifact and publication rules](references/publication.md) before choosing the output path. That reference defines the destination task checkout, naming, character constraints, review, and publication steps. A request to review or draft an issue, revise this skill, or discuss its guidance does not authorize external publication.

## Drafting workflow

1. **Establish the problem and evidence.** Read the conversation, supplied findings, relevant source or logs, and the existing ticket through `cubrid-jira` when a key is known. Identify the observed or reported condition, needed behavior or capability, affected workflow, and consequences. For a new capability, identify the unmet need. Attribute user reports and distinguish them from independently verified observations.
2. **Recommend classification and scope.** Read [issue classification](references/issue-classification.md). Separate the JIRA type, problem categories, and affected components. Recommend a type with a short reason and continue drafting when the choice is reversible. Ask only when ambiguity changes the problem, scope, or publication target. Separate problems that can be accepted and assigned independently; a shared symptom alone is not a reason to split one problem across modules.
3. **Develop the triage argument.** Explain the problem, impact, and needed outcome before considering solutions. Resolve contradictions in the available accounts, or expose the unresolved discrepancy and its effect on the conclusion. Ask for missing evidence only when it changes whether or what to approve; record other unknowns as specific ANALYSIS questions.
4. **Compose and save.** Use the opening structure, shared explanation, and relevant type-specific evidence below. Resolve the destination task checkout, report identity, and exact path using the publication reference before writing. Save one report and revise it in place.
5. **Review the saved report.** Apply the review criteria below and correct concrete defects. Review in the current session; an independent reviewer or design interview is optional and requires the user's request.
6. **Complete the requested workflow.** Follow the publication reference after review: commit the report locally, present required integration and publication approval, and continue authorized operations. Respect an explicit draft-only request or other publication limit, and reuse applicable authorization already established in the conversation.

## The triage argument

Use these questions to review the draft, not as required headings. Below the opening fields, add the minimum shared explanation that lets a colleague understand the problem and assess the evidence. One connected paragraph can be enough for a small issue.

- **Problem:** Identify the task, relevant conditions, current behavior or unmet need, and expected outcome. Ground the gap in an observation, requirement, or attributed user report. A proved root cause is not required.
- **Impact:** Connect the problem to the affected user's work and concrete cost or risk. Internal users include developers, QA engineers, and operators. Distinguish measured or observed impact from plausible risk, and leave unknown frequency or magnitude unasserted.
- **Needed outcome:** Explain what resolving the issue enables. Discuss workarounds, urgency, deferral cost, or scope objections only when available evidence makes them useful to the decision. A preference for cleaner code alone does not establish impact.

State the decision needed from triage when it is useful. Propose an analysis owner only when the user requests it or the context supports that proposal, and identify whose proposal it is. Assignment, priority, and confirmation remain triage decisions; proposed ownership is not an existing commitment.

## Output structure

```markdown
# [TAG] 문제 또는 필요한 결과를 나타내는 한국어 제목

**한 줄 요약**: <이슈가 생긴 계기와 이번에 다룰 문제 또는 필요한 결과를 한 문장으로 설명한다.>

## Issue Triage

**이슈 수행 목적**: <문제가 해결되었을 때 얻어야 할 결과>

**이슈 수행 이유**: <문제와 발생 조건, 지금 검토할 근거>

**영향**: <누가 어떤 결과를 겪는지, 확인된 범위와 중요한 불확실성>

**이슈 수행 방안**: TBD - ANALYSIS 단계에서 해결 방안과 구현 범위를 결정한다.

---

## AI-Generated Context

## Description

<어떤 작업에서 무슨 문제가 생기는지, 어떤 결과가 필요한지 설명한다. 확인한 근거와 중요한 미확인 사항을 덧붙인다.>
```

Write the one-line summary so a team lead opening the issue can immediately answer "What is this issue about?" State the concrete problem or needed outcome and its origin when known. Internal context belongs here when it explains why the issue exists. For a PR follow-up, identify the PR, summarize the specific review concern, and explain what this issue will address. Link the originating comment when available. For example: `PR #<번호>에서 <구체적인 문제>를 지적한 리뷰 댓글에 대응하여, <필요한 결과>를 다루는 후속 이슈다.` Use only supported context. When the origin is unknown or irrelevant, summarize the problem and needed outcome without inventing a PR or discussion. A title repeated verbatim or a PR number alone does not explain the issue.

The four fields summarize the triage argument. Below the divider, add context or evidence that the summary and opening fields do not already explain. State each material unknown once, next to the conclusion or next analysis step it affects. Keep writing instructions and process boilerplate out of the issue body. Add `Triage Request` only when it clarifies a concrete request.

The local heading is a proposed title or description heading. For an existing issue, show the live JIRA summary separately in the handoff. Uploading the description does not change that summary; a summary change needs separate explicit authorization and an update workflow that changes the summary field.

For a requested feature or improvement, name the explicitly requested capability in the title and purpose. Preserve that capability as the agreed scope while leaving detailed design and integration choices for ANALYSIS.

The default `이슈 수행 방안` is `TBD - ANALYSIS 단계에서 해결 방안과 구현 범위를 결정한다.` An explicit, already agreed direction may be summarized with its source and remaining uncertainties. A suggestion becomes a candidate for analysis, not an agreed approach. Scope the **problem and desired outcome** for triage even while the implementation scope remains open.

### Evidence and sections by issue type

Place applicable evidence below the shared explanation. The following sections are options from the legacy templates, not a required checklist. Follow a currently verified team requirement when one applies. Omit empty or inapplicable sections; describe a material unknown as a concrete question where it affects the conclusion. A missing reproduction or root cause does not prevent a draft.

| JIRA type | Additional sections and triage-stage content |
|---|---|
| Correct Error | Use `Test Build`, `Repro`, `Expected Result`, `Actual Result`, or `Additional Information` where useful. Include the smallest observed example and relevant environment. For an available reproduction, give copyable setup and commands, the observed build/revision, and results. Mark unexecuted steps as proposed. If reproduction is unavailable, record missing prerequisites and the next verification question. Distinguish tested versions from untested ones; a source baseline alone does not prove a version is affected. |
| Improve Function/Performance, Development Subject, Refactoring | Use `Specification Changes`, `Acceptance Criteria`, or `Definition of done` for known behavior, constraints, and verification outcomes. Include `Implementation` only for an already agreed direction or useful analysis question. Express acceptance as observable outcomes; leave unagreed thresholds and final validation plans for ANALYSIS. |
| Internal Management, Task | Keep the shared explanation. Add deliverables, dependencies, or completion evidence when useful. An investigation can finish with evidence and a decision; its acceptance need not promise a code fix. |
| Sub-task | Use the parent problem and the child's specific outcome and evidence. Link the parent and define the boundary of the child assignment. |

Acceptance criteria describe what success means, not an unselected algorithm. `Definition of done` identifies relevant verification; choose checks suited to the issue rather than copying a generic QA/manual checklist. Detailed design, final specifications, and implementation validation can remain explicit ANALYSIS deliverables.

### Optional options for analysis

Include `## Options for Analysis` only when available evidence makes an early comparison useful or the user requests it. Omitting the section is a complete result. If included, state that these are candidates, then critically compare them against the same problem and desired outcomes:

| 후보 방안 | 기대 효과와 장점 | 한계·단점과 실패 조건 | 비용·위험·호환성 | 근거와 ANALYSIS 확인 사항 |
|---|---|---|---|---|
| <후보> | <어떤 문제를 얼마나 해소하는가> | <남는 문제와 적용이 어려운 조건> | <근거가 있는 상대 비교; 미상은 미상> | <확인된 사실, 가정, 판별 방법> |

Compare the candidates explicitly after the table: what tradeoff each makes, which conditions would favor each, and what evidence would decide between them. Include the current behavior or workaround as a baseline when it clarifies the decision. With only one plausible candidate, critique it and state the evidence needed to evaluate it; avoid inventing a second candidate. Any preliminary preference must be conditional and grounded. Final selection remains in ANALYSIS.

## Portable evidence

Apply [Links in shared material](../cubrid-common/references/shared-links.md) to
the report and any shared supporting documents. Resolve `link_checker` to
`../cubrid-common/scripts/check-shared-links.py` relative to this skill, then run
`python3 "$link_checker" "$issue_file"` on the saved report before review. Pass
any shared supporting files as additional arguments. Correct preparation failures;
personal viewing links belong only in the chat handoff.

Use project-provided commands, CMake, ctest, or the relevant suite's actual runner. Translate personal `just` recipes, aliases, and local-only helpers into their underlying commands. Supply required configuration, assets, and paths so another engineer can reproduce the reported result. Match the runner to the evidence; do not replace a native testkit run with a CTP command. Mark missing prerequisites explicitly.

The issue body must have zero matches for `rg -nP '\bjust\s+\w'`. This scan is a guard against one common local dependency; also review the commands and referenced assets for portability.

## Review criteria

Review the saved file against the conversation, ticket, and evidence. The report is ready when:

- **One-line summary:** A team lead can explain what the issue addresses and, when known, why it was raised from this sentence alone. A PR follow-up names the PR and the specific review concern, with a comment link when available. Internal context is explained rather than assumed.
- **Problem:** The current condition, needed behavior, and gap are explicit. Observations, user reports, inferred explanations, and unknowns are distinguishable. The report does not require a proved root cause before triage.
- **Impact:** A reader unfamiliar with the implementation can follow the affected user's task and expected result through the current difficulty to concrete costs or risks; repeating the technical symptom alone does not pass. Scope, frequency, magnitude, and uncertainty match the evidence, with unsupported impact left as a specific ANALYSIS question.
- **Need:** The report explains why the outcome matters and any relevant workaround limitations, without inventing urgency or impact. Any ownership proposal is supported and attributed.
- **Stage:** The opening method field uses the default text unless an existing decision is cited. Acceptance describes outcomes. Any optional candidates receive criticism, pros and cons, and a direct comparison; none silently becomes the selected design.
- **Consistency:** The title, one-line summary, four-field summary, detailed argument, expected result, and acceptance criteria describe the same problem and scope. Conflicting evidence is resolved or visibly open. Classification suggestions are distinguishable from live JIRA field values.
- **Output:** The one-line summary, four fields, and divider are present unless overridden. The Korean prose is understandable without internal knowledge, sections add useful content, character requirements hold, and evidence is portable. Apply the artifact and publication checks in the reference before publishing.
