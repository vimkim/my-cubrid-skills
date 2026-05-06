---
name: cubrid-jira-issue-write
description: Write a CUBRID JIRA issue report in Korean with English section headers (##). Analyzes codebase context, writes structured issue markdown to /home/vimkim/gh/my-cubrid-jira/issues/. Use when the user wants to write up a JIRA issue, document a bug finding, or create a feature/task report for CUBRID.
---

# CUBRID JIRA Issue Writer

Write structured JIRA issue reports for the CUBRID project. Output is a markdown file saved to `/home/vimkim/gh/my-cubrid-jira/issues/`.

## When to Use

- User says "write a jira issue", "jira로 작성", "이슈 작성", "리포트 작성"
- User has analysis results or findings to document as a JIRA issue
- User wants to formalize a bug report, feature request, or task

## Output Format

The issue file MUST follow these conventions:

### Language Rules

- **Section headers (`##`)**: Always in English
- **Subsection headers (`###`) and body text**: Always in Korean
- **Code snippets, function names, file paths**: Keep as-is (English/code)
- **Tables**: Korean content, English column headers are OK

### Character Restrictions

- **NO emoji** (e.g., no ✅, ❌, 🚀, 📝, ⚠️, etc.)
- **NO non-BMP Unicode characters** or special symbols (e.g., no →, ←, ✓, ✗, ★, ☆, ※, ▶, ◆, ●, ■, □)
- Use ASCII alternatives instead: `->` instead of `→`, `[x]`/`[ ]` instead of `✅`/`❌`, `*` or `-` instead of `●`/`■`
- **Reason**: The CUBRID JIRA API rejects requests containing emoji and many non-ASCII symbol characters. Stick to plain ASCII punctuation, Korean Hangul, and standard CJK characters only.

### File Naming

`CBRD-XXXXX-short-slug.md` where XXXXX is the JIRA ticket number and short-slug is a brief English descriptor.

If no JIRA ticket number is provided, ask the user for it or use a descriptive name.

## Issue Types

Reference: https://dev.cubrid.org/dev-process/jira/open

Always determine the issue type first — section structure depends on it. The four most commonly used types:

| Type | When to use | Korean |
|------|-------------|--------|
| **Correct Error** | Bug or error fix | 버그/에러 수정 |
| **Improve Function/Performance** | Enhance existing feature, perf tuning | 기능/성능 개선 |
| **Development Subject** | Add a new feature | 신규 기능 개발 |
| **Internal Management** | Internal-only work (version bumps, infra) | 내부 관리 |

Other types (use only if above don't fit):

- **Refactoring** — code cleanup / restructuring (uses the Improve template)
- **Task** — fallback when nothing else fits (discouraged)
- **Sub-task** — child of a parent issue

If the type is unclear, ask the user before drafting.

### Required Sections by Issue Type

Every issue starts with the **TL;DR + Summary** block (project-local convention, on top of the official template), then follows the official section list for that type.

#### Common Header (all types)

```markdown
# [TAG] 한국어 제목

> **TL;DR**: 1-3 문장으로 이슈 요약. 무엇이 문제이고, 무엇을 하려는지, 왜 중요한지 핵심만.

## Summary

- **문제 / 목적**: 한 줄 요약
- **원인 / 배경**: 한 줄 요약
- **제안 / 변경**: 한 줄 요약
- **영향 범위**: 영향받는 모듈, 사용자, 호환성

---
```

#### Correct Error template

```markdown
## Description
(버그의 개요)

## Test Build
(예: `CUBRID-11.0.0.0248-b53ae4a`, OS 정보 포함)

## Repro
(복붙으로 재현 가능한 단계. 서술이 아닌 실행 가능한 명령/SQL)

## Expected Result
(정상 동작 시 기대 결과)

## Actual Result
(실제 관찰된 잘못된 동작)

## Additional Information
(스택 트레이스, 로그, 관련 이슈 링크 등)
```

#### Improve Function/Performance, Development Subject, Refactoring template

```markdown
## Description
(배경, 목적, 문제 정의)

## Specification Changes
(변경되는 스펙. QA/매뉴얼 갱신을 위해 명시. 변경 없으면 N/A)

## Implementation
(설계 및 구현 방법. 코드 흐름, 자료구조, 알고리즘)

## Acceptance Criteria
- [ ] 수락 조건 1
- [ ] 수락 조건 2

## Definition of done
- [ ] 위 A/C 충족
- [ ] QA 통과
- [ ] 문서/매뉴얼 반영
```

#### Internal Management / Task template

```markdown
## Description
(작업의 목적과 설명)
```

### Section Rules

- **Patch/Revision versions** must be written explicitly in the description (JIRA UI only shows Major.Minor).
- Do **not** delete unused sections — replace contents with `N/A` instead.
- Use `TBD` for fields that are not yet known.
- Optional add-ons (project convention, append at the end if useful):
  - `## 참고 코드` — key source file references
  - `## Remarks` — follow-up work, PR links, related tickets

### Top-of-Issue Summary Rules

The `> **TL;DR**` blockquote and `## Summary` block are **required** and must appear before any detailed section. They exist so a reader can grasp the issue in under 30 seconds without reading the full body.

- **TL;DR**: 1-3 문장, 평문 한국어. 결론부터 적기 (무엇/왜/영향).
- **Summary bullets**: 각 항목 한 줄. 길어지면 자세한 내용은 아래 `## Description` / `## Implementation`으로 보낸다.
- TL;DR과 Summary는 **요약**이지 상세 설명이 아니다. 동일한 문장을 복붙하지 말고, 아래 본문에서 더 자세히 풀어 쓴다.

### Style Guide

1. **Title format**: `# [TAG] 한국어 설명` — TAG is a short category like `[OOS]`, `[BTREE]`, `[BROKER]`
2. **Lead with TL;DR + Summary** — a human-readable executive summary before any detailed section
3. **Use `---` horizontal rules** between major sections
4. **Tables** for structured data (function lists, format changes, comparison)
5. **Code blocks** with language annotation for source code
6. **Flow diagrams** using ASCII art in code blocks for call chains
7. **Bold** for emphasis on key terms
8. **Backticks** for all function names, variable names, file paths, and code references
9. Keep paragraphs concise — prefer bullet points and tables over long prose
10. Acceptance criteria as markdown checkboxes (`- [ ]`)

## Reference Examples

Refer to existing issues in `/home/vimkim/gh/my-cubrid-jira/issues/` for style consistency. Key examples:

- `CBRD-26637-refactor-error-handling.md` — Refactoring issue with implementation details
- `CBRD-26630-oos-inline-length.md` — Spec change with before/after tables
- `CBRD-26609-oos-physical-delete.md` — New feature with call flow diagrams and WAL design

## Execution Steps

1. **Check output directory**: Verify that `/home/vimkim/gh/my-cubrid-jira/issues/` exists. If it does NOT exist, **stop immediately** and tell the user: "Error: Issue directory `/home/vimkim/gh/my-cubrid-jira/issues/` does not exist. Please clone or create the repository first." Do NOT create the directory automatically.
2. **Determine the issue type**: Pick from `Correct Error`, `Improve Function/Performance`, `Development Subject`, `Internal Management` (or `Refactoring` / `Task`). Section structure depends on it. If unclear, ask the user.
3. **Gather context**: Read relevant source code, prior analysis, or conversation context
4. **Draft the TL;DR + Summary first**: Before writing detailed sections, write the top-of-issue executive summary (TL;DR blockquote + `## Summary` bullets). This forces a clear thesis and prevents the issue from devolving into an unfocused brain-dump.
5. **Write the issue body**: Use the type-specific template above, in Korean with English `##` headers. Keep all official sections — fill `N/A` or `TBD` rather than deleting.
6. **Save the file**: Write to `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-slug.md`
7. **Show the user**: Print the file path, the chosen issue type, and the TL;DR so the user can sanity-check the framing at a glance

## Arguments

Pass the JIRA ticket number and/or topic as arguments:

- `/write-jira-issue CBRD-26583 OOS compact analysis` — Write issue for specific ticket
- `/write-jira-issue` — Interactive mode, ask user for details

## Optional: Iterate with Grill-and-Revise

For high-stakes issues (root-cause analyses, post-mortems, design proposals, customer-facing bug reports) where rigor matters more than speed, hand the saved draft off to the `/grill-and-revise` skill. It loops a writer subagent against a relentless reviewer subagent until the reviewer approves or a round cap is hit, producing a much sharper issue than a single pass — single-pass writing tends toward hand-wavy filler that a separate, uninvested reviewer will catch.

**When to suggest it:**

- The issue is load-bearing (architectural change, complex bug, regression analysis)
- The user asks for a "thorough", "bulletproof", "peer-reviewed", "stress-tested", or "grilled" issue
- The user says "don't ship until it's solid" or asks another agent to review

**When NOT to use it:**

- Trivial bugs, typos, or simple Internal Management/Task tickets — single pass is fine
- The user wants speed over polish

**How to hand off:**

After saving the initial draft to `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-slug.md`, invoke `/grill-and-revise` with:

- **Topic & purpose**: JIRA ticket number, issue type (Correct Error / Improve / Development Subject / etc.), audience (CUBRID dev team, QA, customer-facing)
- **Output path**: the same file path so the loop revises in place
- **Source material**: relevant source files, prior analysis, `/jira CBRD-XXXXX` output, repro logs
- **Review angle**: technical accuracy, reproducibility (Repro section is executable), adherence to CUBRID issue conventions (Korean body, English `##` headers, NO emoji, NO non-BMP unicode), TL;DR + Summary actually summarize and don't duplicate the body
- **Round cap**: default 5
