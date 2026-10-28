---
name: cubrid-jira-issue-write
description: Write or revise Korean CUBRID JIRA issues for triage, explaining the problem, its consequences, and why work should be approved and assigned. Use for bug reports, improvements, new capabilities, investigations, and development tasks; publish completed reports to existing issues through cubrid-jira.
---

# CUBRID JIRA Issue Writer

Write an evidence-based case for the triage director to confirm the issue and assign analysis to the requesting author or team. The report must explain **what the problem is, why it causes a meaningful problem, and why resolving it deserves work**. Implementation is decided in ANALYSIS.

## Authority and scope

Apply the user's current instructions over this skill's writing defaults and the [company OPEN guideline](https://dev.cubrid.org/dev-process/jira/open). The guideline is a legacy baseline for JIRA terminology and templates; it is not a requirement to finish a design before triage. Look up its current contents when field details matter; do not depend on a temporary local copy.

Preserve the team's four opening fields and explicit `AI-Generated Context` divider by default. These come from the team's writing convention, rather than the official OPEN template. Keep the issue in Korean 한다체, with English `##` headings and Korean `###` headings; retain identifiers as written. Follow an explicit user request to change the format.

Read [artifact and publication rules](references/publication.md) before choosing the output path. That reference defines the destination task checkout, version identity, character constraints, review, and publication steps. A request to revise this skill or discuss its guidance does not trigger issue publication.

## Drafting workflow

1. **Establish the problem and evidence.** Read the conversation, supplied findings, relevant source or logs, and the existing ticket through `cubrid-jira` when a key is known. Identify the observed or reported condition, needed behavior or capability, affected workflow, and consequences. For a new capability, identify the unmet need. Attribute user reports and distinguish them from independently verified observations.
2. **Recommend classification and scope.** Read [issue classification](references/issue-classification.md). Separate the JIRA type, problem categories, and affected components. Recommend a type with a short reason and continue drafting when the choice is reversible. Ask only when ambiguity changes the problem, scope, or publication target. Separate problems that can be accepted and assigned independently; a shared symptom alone is not a reason to split one problem across modules.
3. **Develop the triage argument.** Write the three explanations below before considering solutions. Resolve contradictions in the available accounts, or expose the unresolved discrepancy and its effect on the conclusion. Ask for missing evidence only when it changes whether or what to approve; record other unknowns as specific ANALYSIS questions.
4. **Compose and save.** Use the opening structure, shared explanation, and relevant type-specific evidence below. Resolve the destination task checkout, report identity, and exact path using the publication reference before writing. Save one report and revise it in place.
5. **Review the saved report.** Apply the review criteria below and correct concrete defects. Review in the current session; an independent reviewer or design interview is optional and requires the user's request.
6. **Complete the requested workflow.** Follow the publication reference after review: commit the report locally, present required integration and publication approval, and continue authorized operations. Respect an explicit draft-only request or other publication limit, and reuse applicable authorization already established in the conversation.

## The triage argument

Develop these as connected explanations in `Description`. Use the Korean subheadings shown in the structure when they help distinguish the questions. Give enough detail for a reader unfamiliar with the subsystem to assess the case; a short opening summary does not replace the explanation.

- **What is the problem? / 무엇이 문제인가:** Establish the relevant background and triggering conditions. State current behavior or the missing capability, what is needed instead, and the gap between them. Anchor the gap in a reproducible example, observed workflow, requirement, or attributed user report. Root-cause knowledge is not a prerequisite for reporting a problem.
- **Why is it a problem? / 왜 문제인가:** Start from the affected user's workflow: what they are trying to do, what result they expect, how the current behavior blocks or complicates that work, and the resulting cost or risk. Explain this chain so a reader unfamiliar with the implementation can understand why the issue matters. For internal improvements, use the developer's, QA engineer's, or operator's workflow as appropriate. State the triggering conditions and observed scope. Distinguish observed or measured impact from plausible risk; identify unknown frequency or magnitude instead of inventing numbers. When impact lacks evidence, record a specific ANALYSIS question. A preference for cleaner code alone does not establish impact.
- **Why do we need to fix it? / 왜 해결해야 하는가:** Explain what remains unacceptable if the issue is deferred, what outcome resolving it enables, and why available workarounds are insufficient or costly. State the reason for starting work now when evidence supports one. When urgency is unknown, say so. Address known duplication, scope, compatibility, or workaround objections that could change the triage decision.

Make the requested decision explicit: confirm the problem and assign ANALYSIS to the requesting author or team. Explain relevant expertise or continuity only when the context supports it. Assignment, priority, and confirmation remain triage decisions; proposed ownership is not an existing commitment.

## Output structure

```markdown
# [TAG] 문제 또는 필요한 결과를 나타내는 한국어 제목

## Issue Triage

**이슈 수행 목적**: <문제가 해결되었을 때 얻어야 할 결과>

**이슈 수행 이유**: <문제와 발생 조건, 지금 검토할 근거>

**영향**: <누가 어떤 결과를 겪는지, 확인된 범위와 중요한 불확실성>

**이슈 수행 방안**: TBD - ANALYSIS 단계에서 해결 방안과 구현 범위를 결정한다.

---

## AI-Generated Context

> 아래는 제공된 자료와 확인한 근거를 바탕으로 작성한 상세 맥락이다. 미확인 사항은 본문에 구분한다.

## Description

### 무엇이 문제인가
<배경과 현재 상태, 필요한 상태, 확인 근거>

### 왜 문제인가
<사용자의 작업과 기대 결과, 현재 동작으로 겪는 어려움, 그로 인한 비용이나 위험을 연결한다. 확인된 영향과 예상 위험을 구분한다.>

### 왜 해결해야 하는가
<방치 비용, 우회책의 한계, 필요한 결과와 착수 근거>

## Triage Request
<이슈 확인 및 작성자 측의 ANALYSIS 배정을 요청한다. 요청 범위와 분석에서 확인할 사항을 적는다.>
```

The four fields summarize the argument. Expand their facts below the divider with background, reasoning, and evidence. Use useful restatement; remove repetition that adds no understanding. Keep the issue's audience and writing instructions out of the issue body.

For a requested feature or improvement, name the explicitly requested capability in the title and purpose. Preserve that capability as the agreed scope while leaving detailed design and integration choices for ANALYSIS.

The default `이슈 수행 방안` is `TBD - ANALYSIS 단계에서 해결 방안과 구현 범위를 결정한다.` An explicit, already agreed direction may be summarized with its source and remaining uncertainties. A suggestion becomes a candidate for analysis, not an agreed approach. Scope the **problem and desired outcome** for triage even while the implementation scope remains open.

### Evidence and sections by issue type

Place the relevant evidence below the divider after the shared explanation. Preserve the official sections for the selected template unless the user requests another structure. Use `N/A` for a genuinely inapplicable section; use `TBD` with the unanswered question for missing knowledge. A missing reproduction or root cause is an unknown, not `N/A`.

| JIRA type | Additional sections and triage-stage content |
|---|---|
| Correct Error | `Test Build`, `Repro`, `Expected Result`, `Actual Result`, `Additional Information`. Give the full observed build and commit, OS and relevant settings, copyable setup and commands, and actual evidence. Mark unexecuted steps as proposed. Record tested and untested release versions separately; the source baseline alone does not prove a version is affected. |
| Improve Function/Performance, Development Subject, Refactoring | `Specification Changes`, `Implementation`, `Acceptance Criteria`, `Definition of done`. Describe known required behavior and constraints. Default `Implementation` to `TBD - ANALYSIS 단계에서 결정한다.` Express acceptance as observable outcomes, with unagreed thresholds and final validation plans left for ANALYSIS. |
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

- **Problem:** The current condition, needed behavior, and gap are explicit. Observations, user reports, inferred explanations, and unknowns are distinguishable. The report does not require a proved root cause before triage.
- **Impact:** A reader unfamiliar with the implementation can follow the affected user's task and expected result through the current difficulty to concrete costs or risks; repeating the technical symptom alone does not pass. Scope, frequency, magnitude, and uncertainty match the evidence, with unsupported impact left as a specific ANALYSIS question.
- **Need and assignment:** The report explains the cost of deferral, expected benefit, and relevant workaround limitations. It requests confirmation and analysis ownership without inventing urgency, expertise, or an assignment.
- **Stage:** Implementation is TBD unless an existing decision is cited. Acceptance describes outcomes. Any optional candidates receive criticism, pros and cons, and a direct comparison; none silently becomes the selected design.
- **Consistency:** The title, four-field summary, detailed argument, expected result, and acceptance criteria describe the same problem and scope. Conflicting evidence is resolved or visibly open. Classification suggestions are distinguishable from live JIRA field values.
- **Output:** The four fields and divider are present unless overridden, prose and character requirements hold, and evidence is portable. Apply the artifact and publication checks in the reference before publishing.
