---
name: cubrid-jira-issue-write
description: Write a CUBRID JIRA issue report in Korean with English section headers (##). Top of issue is a fixed Issue Triage block (목적/이유/방안 — first two required) followed by an explicitly separated AI-Generated Context block. Writes structured markdown to /home/vimkim/gh/my-cubrid-jira/issues/. Use when the user wants to write up a JIRA issue, document a bug finding, or create a feature/task report for CUBRID.
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

Every issue starts with the **Issue Triage** block (three required fields for fast triage), followed by an explicitly labeled **AI-Generated Context** block, then the official section list for that type.

The triage block exists because AI-generated issue bodies are often too long to read end-to-end during triage. Reviewers must be able to grasp 목적 / 이유 / 방안 in 10 seconds without entering the AI-written context.

#### Common Header (all types)

```markdown
# [TAG] 한국어 제목

## Issue Triage

> **이슈 수행 목적** (필수): 무엇을 해결하려고 하는가. 1-2 문장. 결과 상태로 기술 (예: "X 가 Y 하도록 한다", "Z 버그가 재현되지 않도록 한다").
>
> **이슈 수행 이유** (필수): 이 문제를 왜 해결해야 하는가. 1-2 문장. 비즈니스/품질/운영 측면의 근거 (예: 고객 장애, QA 실패, 성능 저하, 기술 부채 한계).
>
> **이슈 수행 방안**: 어떻게 해결할 것인가. 이슈 작성 시점에 기술 가능한 수준에서만 작성하고, 세부 설계는 ANALYSIS 단계에서 구체화. 모르면 `TBD - ANALYSIS 단계에서 결정`.

---

## AI-Generated Context

> 아래 내용은 AI 가 코드/맥락을 분석해 작성한 상세 자료입니다. 빠른 triage에는 위 **Issue Triage** 블록만으로 충분하며, 본문은 구현/리뷰 단계에서 참고하시면 됩니다.

### Summary

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

### Top-of-Issue Triage Rules

The `## Issue Triage` block is **required** and must be the first content after the title. It exists so a reviewer can decide priority/assignment in under 10 seconds without reading any AI-generated context.

**Issue Triage block — three fields:**

- **이슈 수행 목적 (필수)**: 무엇을 해결하려고 하는가. 1-2 문장. 결과 상태로 기술. NOT 분석/배경.
- **이슈 수행 이유 (필수)**: 이 문제를 왜 해결해야 하는가. 1-2 문장. 비즈니스/품질/운영 근거.
- **이슈 수행 방안**: 어떻게 해결할 것인가. **이슈 작성 시점에 기술 가능한 수준만 작성**. 세부 설계는 ANALYSIS 단계에서 구체화. 모르면 `TBD - ANALYSIS 단계에서 결정`이라고 명시. AI 가 임의로 추측한 구현 계획을 채워넣지 말 것.

**AI-Generated Context block — separation rule:**

모든 AI 분석 결과(Summary 불릿, Description, Implementation, 흐름도, 코드 인용 등)는 `## AI-Generated Context` 헤더 이후에 둔다. 이 분리는 리뷰어가 "사람이 직접 작성한 triage 요약"과 "AI 가 채운 상세 맥락"을 구분할 수 있게 해 준다.

**Anti-patterns:**

- TL;DR 부활시키기: `> **TL;DR**:` 블록은 더 이상 사용하지 않는다. 대신 `## Issue Triage` 의 세 필드를 채운다.
- 목적/이유 합치기: 목적과 이유는 별개 필드다. "X 를 Y 하기 위해 Z 한다" 한 문장으로 두 필드를 동시에 채우지 말 것.
- 방안 과잉 작성: 작성 시점에 알 수 없는 구현 디테일을 방안에 끼워 넣지 말 것. 그건 ANALYSIS 단계 / `## Implementation` 의 영역.
- 컨텍스트 누수: AI 분석 결과를 triage 블록 안에 끌어다 두지 말 것. AI 분석은 `## AI-Generated Context` 아래에만.

### Style Guide

1. **Title format**: `# [TAG] 한국어 설명` — TAG is a short category like `[OOS]`, `[BTREE]`, `[BROKER]`
2. **Lead with Issue Triage block** (목적/이유/방안) — human-readable triage summary before any AI-generated context
3. **Separate AI context** with `## AI-Generated Context` header — all detailed analysis lives below this divider
4. **Use `---` horizontal rules** between major sections
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

The same rationale appearing in Issue Triage + Summary + Description + Implementation + A/C erodes trust fast.

- **Issue Triage 목적/이유**: 결과 상태 + 근거. 메커니즘/구현은 NO.
- **Issue Triage 방안**: 작성 시점에 아는 수준만. 상세 설계는 `## Implementation` 으로.
- **Summary bullets**: ≤ 1 line each, triage 블록과는 다른 정보를 추가 (예: 영향 범위, 호환성).
- **Description**: 정식 "why". 위에서 이미 한 말을 그대로 복붙하지 말고 깊이를 더한다.
- **A/C**: checklist 항목. 산문 재서술 NO.
- **Out-of-scope vs. A/C**: 각 사실은 한 곳에만 등장.

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
4. **Draft the Issue Triage block first**: Before writing any detailed section, fill `## Issue Triage` with three fields — **이슈 수행 목적** (필수), **이슈 수행 이유** (필수), **이슈 수행 방안** (작성 가능한 수준). This forces a clear thesis and gives reviewers a 10-second triage path.
5. **Insert the AI-Generated Context divider**: After the triage block, add `## AI-Generated Context` header with the 1-line caveat note. All AI-written analysis (Summary bullets, Description, Implementation, etc.) goes below this divider.
6. **Write the issue body**: Use the type-specific template above, in Korean with English `##` headers. Keep all official sections — fill `N/A` or `TBD` rather than deleting.
7. **Save the file**: Write to `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-slug.md`
8. **Show the user**: Print the file path, the chosen issue type, and the **Issue Triage** block (목적/이유/방안 세 줄) so the user can sanity-check the framing at a glance

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
- **Review angle**: technical accuracy, reproducibility (Repro section is executable), adherence to CUBRID issue conventions (Korean body, English `##` headers, NO emoji, NO non-BMP unicode), **Issue Triage block** is present at the top with all three fields (목적/이유/방안) filled and not collapsed into one sentence, **AI-Generated Context divider** clearly separates AI-written detail from the triage summary, Summary/Description don't duplicate the triage block verbatim, **natural Korean prose** (the "Audience: senior CUBRID engineers" and "Avoid translationese and AI cadence" sections above must be passed to the reviewer verbatim)
- **Round cap**: default 5
