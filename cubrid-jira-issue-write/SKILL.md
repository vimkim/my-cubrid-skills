---
name: cubrid-jira-issue-write
description: Write and publish CUBRID JIRA bug reports, feature requests, and task reports in Korean. Preserve the team's four-field triage and AI-Generated Context separation, explain background and causes clearly, and publish the versioned Markdown report to the matching existing issue.
---

# CUBRID JIRA Issue Writer

Write a structured JIRA issue saved as markdown to `/home/vimkim/gh/my-cubrid-jira/issues/`.

Help a reader unfamiliar with the subsystem understand the situation, why a change is needed, and what is proposed. Keep the team's summary above the AI-Generated Context divider, then develop the background and causal explanation below it. Let the explanation determine its length.

## When to Use

- User says "write a jira issue", "jira로 작성", "이슈 작성", "리포트 작성"
- User has analysis/findings to document, or wants to formalize a bug report, feature request, or task

## Hard Constraints (non-negotiable)

- **Save location**: `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-short-slug_<SHORT_SHA>_<AGENT>.md`. If the directory does not exist, **stop and tell the user** to clone/create the repo. Do NOT create it yourself. If no ticket number is known, ask whether one should be supplied; only after the user confirms this is a ticket-free draft, use `descriptive-slug_<SHORT_SHA>_<AGENT>.md`.
- **No emoji and no non-BMP (4-byte UTF-8) characters.** The CUBRID JIRA API rejects 4-byte characters, and emoji (🚀 ✅ ❌ 😀 …) read as AI-slop regardless of plane. Everything in the BMP is allowed — Korean/CJK, and ordinary typographic symbols when they aid readability: `★` (flow-diagram limit marker), box-drawing (`└ ├ │`), `→`, `✓`. ASCII forms (`->`, `[x]`/`[ ]`, `-`/`*`) are equally fine — use whichever reads cleaner, not because the API forces it.
- **Headers (`##`) in English. Subheaders (`###`) and all body text in Korean** (평어/한다체, never 합니다/입니다). Code, function names, file paths, identifiers stay as-is.
- **Never state the issue's own audience or readability target in the body.** No "신입도 읽을 수 있게 작성", no "독자 대상: ...", no reading-grade note, no "고등학생도 이해할 수 있도록". Readability is writer-side guidance; the reader benefits from it silently. Any sentence describing the doc's own clarity instead of the bug/feature gets deleted.

## Automatic Completion Contract

A request that triggers this skill authorizes the complete workflow for an existing `CBRD-XXXXX` issue: write and review the report, commit only that report in `my-cubrid-jira`, push it to `origin/main`, and publish it as the matching live JIRA description through the `cubrid-jira` skill. Show previews for visibility, but do not pause for another confirmation.

Keep this authorization inside these exact boundaries:

- Require the local repository at `/home/vimkim/gh/my-cubrid-jira` to be on `main` with `origin` pointing to `github.com/vimkim/my-cubrid-jira` in HTTPS or SSH form.
- Preserve unrelated worktree and index changes. Stage and commit only the resolved issue file.
- Require the issue key derived from the filename to equal the JIRA target key.
- Push the Markdown commit successfully before the live JIRA update. If the push fails, stop before uploading.
- Use the `cubrid-jira` skill's publish-description workflow, including its dry-run, live update with `--yes`, and live read-back verification.
- If the live update fails after the push, keep the pushed commit, report the exact JIRA error and the partial-completion state, and do not claim success.

A ticket-free draft has no upload target. Save, review, commit, and push it like any other report, then report that only the JIRA upload was skipped. Creating a new JIRA issue is a separate workflow requiring the project, issue type, summary, and other required fields.

## Artifact Identity

Resolve the filename before writing the draft:

1. Set `SOURCE_COMMIT` to the specific CUBRID commit or PR head analyzed by the issue when one is supplied. Otherwise use `git rev-parse HEAD` in the current CUBRID worktree. Never use the `my-cubrid-jira` repository commit. If no relevant CUBRID commit or worktree can be identified, ask the user.
2. Validate `SOURCE_COMMIT` and take its first seven hexadecimal characters as `SHORT_SHA`.
3. Set `AGENT` from the active AI host's runtime identity. Use `codex` for Codex and `claude` for Claude Code. For another host, use its stable lowercase agent name. Do not infer the host from installed binaries because multiple AI CLIs may coexist; if runtime identity is unclear, ask the user.
4. Compute the output path once and reuse that exact file through revision and final handoff. The basename must end with `_<SHORT_SHA>_<AGENT>.md`.

For example, Codex documenting `f5794fb...` writes `CBRD-26972-oos-show-heap-capacity_f5794fb_codex.md`; Claude Code writes `CBRD-26972-oos-show-heap-capacity_f5794fb_claude.md`.

## Issue Types

Reference: https://dev.cubrid.org/dev-process/jira/open — determine the type **first**; section structure depends on it.

| Type | When | Korean |
|------|------|--------|
| **Correct Error** | bug / error fix | 버그·에러 수정 |
| **Improve Function/Performance** | enhance existing feature, perf | 기능·성능 개선 |
| **Development Subject** | new feature | 신규 기능 개발 |
| **Internal Management** | version bumps, infra, internal-only | 내부 관리 |

`Refactoring` uses the Improve template; `Task` is a discouraged fallback; `Sub-task` is a child issue. If the type is unclear, ask before drafting.

## Output Structure

The team requires all four fields above the explicit AI-Generated Context divider. Keep the reason summarized here; explain its background and causes in detail below.

```markdown
# [TAG] 한국어 제목

## Issue Triage

**이슈 수행 목적**: <달성하려는 결과>

**이슈 수행 이유**: <어떤 상황에서 무엇이 달라졌거나 문제가 되었는지 요약>

**영향**: <누가 어떤 불편이나 실패를 겪는지, 또는 무엇이 제한되는지>

**이슈 수행 방안**: <합의된 변경 방향과 범위. 미결정 사항은 TBD>

---

## AI-Generated Context

> 아래는 AI가 코드와 맥락을 분석해 작성한 상세 자료다.

<type-specific sections below, beginning with Description>
```

In `## Description`, establish the situation before presenting technical changes: explain the relevant background, what changed or fails, and how that leads to the reported impact. Then develop the proposal and supporting evidence in the appropriate sections. Several paragraphs are appropriate when the reader needs them; a straightforward bug may need only a short explanation.

The summary and detailed explanation may repeat facts, reasons, and impact. Reintroduce them when it helps the reader follow the argument, adding context, mechanisms, or evidence. Remove repetition that adds no understanding, rather than enforcing one location per fact. An extra scope summary is optional.

### Triage content

- **목적**: the intended outcome, stated briefly.
- **이유**: enough situational context to explain why this work is needed now. Use concrete evidence appropriate to the issue: observed behavior, changed requirements, a workflow problem, or a relevant technical limit.
- **영향**: the practical consequence for users, developers, QA, performance, or maintainability. Keep this field visible even when the reason also mentions the consequence.
- **이슈 수행 방안**: the agreed approach and scope, grounded in the conversation, JIRA decisions, or an explicit design document. Distinguish proposals from agreed decisions. Use `TBD - 합의 미확인` for an unresolved decision, or `TBD - ANALYSIS 단계에서 결정` when that deferral is agreed.

Show AS-IS/TO-BE when a before/after comparison clarifies the change. Choose prose, a table, or a list to suit the material. Put detailed source references, algorithms, and reproduction steps below the divider; retain a precise identifier in the summary when it is needed to understand the issue.

### Type-specific sections (go below the `## AI-Generated Context` divider)

**Correct Error:**

```markdown
## Description
(발생 상황과 배경, 관찰한 문제와 영향, 확인된 원인 또는 조사할 내용)

## Test Build
(예: `CUBRID-11.0.0.0248-b53ae4a`, OS 포함)

## Repro
(필요한 환경과 복붙으로 재현 가능한 명령/SQL)

## Expected Result
## Actual Result
## Additional Information
(스택 트레이스, 로그, 관련 이슈 링크)
```

**Improve / Development Subject / Refactoring:**

```markdown
## Description
(배경, 목적, 문제 정의)

## Specification Changes
(변경 스펙. QA/매뉴얼 갱신용. 변경 없으면 N/A)

## Implementation
(설계·구현. 코드 흐름, 자료구조, 알고리즘)

## Acceptance Criteria
- [ ] 수락 조건 1

## Definition of done
- [ ] 위 A/C 충족
- [ ] QA 통과
- [ ] 문서/매뉴얼 반영
```

**Internal Management / Task:** just `## Description`.

**Section rules:** Patch/Revision versions go in the description explicitly (JIRA UI shows only Major.Minor). Don't delete unused official sections — fill `N/A`. Use `TBD` for unknowns. Optional tail add-ons: `## Code References` (key source refs), `## Remarks` (follow-ups, PR links, related tickets).

## Writing Guidance

- Explain the background before asking the reader to interpret a technical list or table. Include relevant history and changed circumstances when the sources establish them. Read the conversation and available source material first; ask only for consequential context that cannot be recovered there.
- Distinguish confirmed facts, user experience, hypotheses, and proposals through natural attribution. Leave unavailable causes or decisions open instead of supplying a plausible story.
- Explain unfamiliar terms and the significance of technical limits where needed. Give enough connected prose to make the causal relationship understandable; the issue need not become a general tutorial.
- Write natural Korean in 한다체. Use prose for explanations, tables for comparisons, and diagrams for flows when they help. Keep audience and readability guidance outside the issue body.

## Local-only Tooling (keep issues portable)

JIRA issues are read by devs, QA, and CS who do not share the author's local setup. Keep every command runnable on a fresh CUBRID dev VM.

- **Never write `just <recipe>` in an issue body, Repro, A/C, or table.** The `justfile` is local; a reader running `just shell-debug` gets `command not found`. Substitute the underlying command (e.g. `ctp.sh shell -c shell_ci.conf`, plus a 1-line note on pointing the conf's `scenario` at the test path).
- **Same for personal aliases/functions/dotfiles** (`my-rerun`, `cb`, custom helpers). If it isn't in the public CTP/CUBRID toolchain, it doesn't belong in the issue.
- **Acceptable wrappers** (universal to a CUBRID engineer): `ctp.sh`, `cubrid`, `csql`, `make`, `cmake`, `gh`, raw `bash`/`sh`. Prefer these.
- **If a personal recipe is the easiest repro for the author**, paraphrase the underlying command in the issue; keep the `just`/alias form in private notes only. Never put both.
- **Pre-upload scan**: `rg -nP '\bjust\s+\w' file.md` must return zero hits.

## Execution Steps

1. **Check output directory** exists (else stop — see Hard Constraints).
2. **Determine issue type** (section structure depends on it; ask if unclear).
3. **Gather context**: read source, prior analysis, `/cubrid-jira CBRD-XXXXX`, repro logs.
4. **Resolve artifact identity**: set `SOURCE_COMMIT`, `SHORT_SHA`, `AGENT`, and the final output path using **Artifact Identity**.
5. **Develop the background and causal explanation** from the gathered context. Establish the situation, problem, and impact before listing changes or implementation details.
6. **Compose the issue** using Output Structure and the type-specific sections. Summarize 목적, 이유, 영향, and 이슈 수행 방안 above the divider; place the detailed explanation under `## AI-Generated Context`. Useful restatement is allowed.
7. **Check evidence and decisions**: distinguish observations from inferred causes, and agreed changes from proposals or unknowns. Use AS-IS/TO-BE where it clarifies the change.
8. **Check output constraints**: Korean prose and English `##` headers, no emoji/non-BMP characters, portable commands. The `rg -nP '\bjust\s+\w'` scan must return zero matches.
9. **Save** to the resolved path ending in `_<SHORT_SHA>_<AGENT>.md`.
10. **Review the saved file** against the Document Review criteria below and correct defects in place.
11. **Show the publication preview**: path, source commit, agent name, chosen type, and Issue Triage block. This is informational; continue without asking for confirmation.
12. **Validate the notes repository** against the Automatic Completion Contract. Re-run all mandatory checks after revision.
13. **Commit only the issue file and push it**:

    ```bash
    issue_rel="issues/$(basename "$issue_file")"
    git -C /home/vimkim/gh/my-cubrid-jira add -- "$issue_rel"
    git -C /home/vimkim/gh/my-cubrid-jira commit \
      -m "docs(CBRD-XXXXX): add <short-slug> issue report" -- "$issue_rel"
    git -C /home/vimkim/gh/my-cubrid-jira push origin main
    ```

    If the intended file is already committed, skip the empty commit and still verify that `origin/main` contains it. Verify that the created commit contains only `issue_rel`; leave unrelated staged or untracked files untouched.
14. **Publish through `cubrid-jira`**: for a keyed report, hand off the matching ticket key and absolute `issue_file` to the `cubrid-jira` skill's publish-description workflow with delegated authorization for the live `--yes` update. Skip this step only for an explicitly ticket-free draft.
15. **Finish with verification**: report the Markdown commit and pushed branch; for a keyed report, also report the live JIRA URL and read-back result. Do not call a keyed workflow complete until both push and upload verification succeed. For a ticket-free draft, call out that no JIRA target existed.

## Arguments

- `/write-jira-issue CBRD-26583 OOS compact analysis` — write issue for a specific ticket
- `/write-jira-issue` — interactive mode, ask for details

## Document Review

Review the saved issue file in the current session against the ticket, issue type, source material, and the following criteria. Correct defects in the same file before publication:

- **Understanding**: the summary conveys why the issue matters, and Description establishes the background and causal explanation before technical changes. The reader can follow the situation, problem, impact, and proposed response without reconstructing them from code references.
- **Team structure**: 목적, 이유, 영향, and 이슈 수행 방안 are all above the explicit AI-Generated Context divider. The detailed body may repeat and expand the summary.
- **Evidence and scope**: claims match the sources; user observations and hypotheses are attributed; agreed changes and unresolved proposals are distinguishable. Reproduction commands include the necessary conditions and observed results are represented accurately.
- **Writing and output**: the explanation is sufficient and natural, technical terms are explained where needed, and the Hard Constraints and Local-only Tooling requirements hold. Repetition earns its place by helping understanding.

Ask a concise clarification only for a decision or required input that the conversation and sources cannot resolve. Use an independent reviewer only when the user requests one; provide the saved file, source material, and these criteria, and request concrete findings. A design interview is a separate user-requested activity, not a publication prerequisite.

Once the criteria are satisfied, continue directly with the preview, validation, commit, push, and `cubrid-jira` upload steps under the Automatic Completion Contract.
