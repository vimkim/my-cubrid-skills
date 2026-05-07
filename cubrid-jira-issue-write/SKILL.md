---
name: cubrid-jira-issue-write
description: Write a JIRA issue report for the CUBRID project. Use this when the user wants to draft a bug report, feature request, or task ticket for CUBRID.
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

### Plain Language

Write the issue so a teammate from a different module — QA, customer support, a new hire — can read it once and understand. JIRA tickets travel far beyond the original author.

- **Short sentences.** One idea per sentence. If a sentence runs past two lines, split it.
- **Plain Korean over jargon.** Use ordinary words; only keep CUBRID-internal terms (function names, file paths, protocol acronyms) when they're load-bearing. Don't translate well-known English code identifiers (`pgbuf_fix`, `MVCC`, `WAL`) — keep them in code-style as-is.
- **Concrete over abstract.** "에러 코드 6곳을 모두 갱신해야 한다" beats "전반적인 일관성을 유지해야 한다." Name the file, the function, the number.
- **No filler.** Drop phrases like "본 이슈에서는...", "필요에 따라...", "전반적으로...". State the fact directly.
- **Reproducible Repro.** The Repro section should be copy-pasteable commands or SQL, not narrative prose.

### Audience: senior CUBRID engineers

Readers are the CTO, team lead, peer engineers, QA — they know the codebase. Write peer-to-peer prose, not tutorials.

- **No glossary tables for CUBRID basics** (`recdes`, `attrepr`, `OOS`, `assert_release`, `MVCC`, `OR_VAR_*`, `pgbuf_*`, etc.). Senior readers grep unfamiliar names; defining them reads as patronizing.
- **Project-specific terms on first use** get a 1-line aside, not a glossary entry — e.g., "`recdes_allocate_data_area` 가 NULL 시 자체 `er_set` 을 안 한다 (`storage_common.c:310-324`)".
- **No meta-labels in headers.** `### 왜 (한 번만 설명)`, `### \`*is_oos\` 계약 (호출자가 알아야 할 것)` — the parenthetical is an author's note to self. Drop it.
- **No obvious-statement filler.** If a senior reader can read the code and see it, don't say it.

### Avoid translationese and AI cadence

The biggest tell of LLM-written prose is rhythm. Hunt for these and rewrite.

**Translationese — word-for-word English idioms:**

| Avoid | Use |
|---|---|
| "에러가 ... 흘러간다" | "결과셋에 섞여 나간다", "그대로 반환된다" |
| "측면도 문제다" / "측면에서는" | restructure to drop "측면" |
| "수용한다" (limitation) | "그대로 둔다", "받아들인다" |
| "이렇다." (앞에 두고 코드 블록) | colon `:` 찍고 코드로 |
| "위함이다" / "기 위함이다" | "위해서다", "기 위해서다" |
| "그렇게도 안 한다" | "그것조차 하지 않는다" |

**AI lockstep cadence — multiple short "한다." sentences in a row.** Vary endings with `-므로`, `-기 때문에`, `-라`, `-도록`, longer subordinate clauses.

**Structural patterns to avoid:**

- **English-direct labels.** `**무엇을**:` / `**어떻게**:` / `**왜**:` are direct renderings of "What:/How:/Why:". Use Korean: `**변경**:`, `**부수 수정**:`, `**영향**:`. Same for header `### 왜` — use `### 배경` / `### 발단`.
- **Sentence-fragment 명사구 종결 ("...없음.", "...적용.", "...불필요.") in body prose.** OK in table cells, NOT in paragraphs.
- **`Fact: / Effect: / Ops 결론:` style bullet labels** — ITIL/RFC parody tone. Use peer-to-peer prose.
- **`->` arrows in subheaders.** Use descriptive Korean (`#### Case 4 — 메모리 부족`).
- **Self-narration filler.** Drop "다음과 같이 정의한다", "위 사항을 반영하여...", "본 티켓에서는 ... 한다".
- **존댓말 leak.** JIRA bodies are 평어 (한다체). Fix any `합니다` / `입니다`.

### Avoid duplication across sections

The same rationale appearing in TL;DR + Summary + Description + Implementation + A/C erodes trust fast.

- **TL;DR**: 2-3 sentences. WHAT changes + WHAT the user sees. NO mechanism.
- **Summary bullets**: ≤ 1 line each, additive.
- **Description**: the canonical "why". Restate elsewhere → back-reference or delete.
- **A/C**: checklist items, NOT prose retellings.
- **Out-of-scope vs. A/C**: each fact appears in ONE place.

After drafting, grep for sentences appearing in 2+ sections; pick the strongest location.

## Reference Examples

Refer to existing issues in `/home/vimkim/gh/my-cubrid-jira/issues/` for style consistency. Key examples:

- `CBRD-26637-refactor-error-handling.md` — Refactoring issue with implementation details
- `CBRD-26630-oos-inline-length.md` — Spec change with before/after tables
- `CBRD-26609-oos-physical-delete.md` — New feature with call flow diagrams and WAL design
- `CBRD-26769-heap-attrvalue-point-variable-int-return.md` — Refactoring with Case 1..N taxonomy, executive-tone Korean (post-grill, post natural-Korean review)

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

## Mandatory: Iterate with Grill-and-Revise

Every JIRA issue draft must go through `/grill-and-revise` before being filed. Do not post a single-pass issue. Single-pass issues drift toward hand-wavy filler, missing or non-executable Repro steps, unsupported root-cause claims, and TL;DRs that just restate the body. JIRA tickets are read across QA, dev, and customer support by people with no other context, so unclear writing has a long blast radius.

This step is required, not optional. It applies to every issue. No agent-side judgment — including size, scope, perceived triviality, or perceived risk — is a valid skip criterion. The only legitimate skip is when the user, in the message that triggered this skill, explicitly says "skip grill" or "don't grill this" (or unambiguous equivalent: "no grill", "skip the grill loop", "just push it"). If in doubt, do the grill loop.

**How to hand off:**

After saving the initial draft to `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-slug.md`, invoke `/grill-and-revise` with:

- **Topic & purpose**: JIRA ticket number, issue type (Correct Error / Improve / Development Subject / etc.), audience (CUBRID dev team, QA, customer-facing)
- **Output path**: the same file path so the loop revises in place
- **Source material**: relevant source files, prior analysis, `/jira CBRD-XXXXX` output, repro logs
- **Review angle**: technical accuracy, reproducibility (Repro section is executable), adherence to CUBRID issue conventions (Korean body, English `##` headers, NO emoji, NO non-BMP unicode), TL;DR + Summary actually summarize and don't duplicate the body, **natural Korean prose** (the "Audience: senior CUBRID engineers" and "Avoid translationese and AI cadence" sections above must be passed to the reviewer verbatim)
- **Round cap**: default 5
