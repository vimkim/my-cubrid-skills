---
name: cubrid-pr-review
description: "CUBRID C/C++ PR code review with LSP/clangd analysis. Use when reviewing a CUBRID pull request, when the user shares a GitHub PR URL from a CUBRID repo, asks to review or check a pull request, or requests LSP-based analysis of PR changes."
argument-hint: "<pr-url>"
allowed-tools: Bash(gh *), Bash(git *), Bash(jq *), Bash(scripts/*), Read, Write, Glob, Grep, mcp__plugin_oh-my-claudecode_t__lsp_diagnostics, mcp__plugin_oh-my-claudecode_t__lsp_diagnostics_directory, mcp__plugin_oh-my-claudecode_t__lsp_hover, mcp__plugin_oh-my-claudecode_t__lsp_goto_definition, mcp__plugin_oh-my-claudecode_t__lsp_find_references, mcp__plugin_oh-my-claudecode_t__lsp_document_symbols
---

# CUBRID PR Reviewer

Review CUBRID database engine pull requests and produce a concise Korean review report. CUBRID is a multi-threaded, open-source RDBMS with a large C/C++ codebase, so reviews focus on correctness, memory safety, and concurrency.

## When to Use

- User shares a CUBRID GitHub PR URL (e.g., `https://github.com/CUBRID/cubrid/pull/6950`)
- User says "review this PR", "PR 리뷰", "코드 리뷰 부탁", "리뷰해줘"
- User requests LSP/clangd analysis of PR changes
- Even if the user just pastes a CUBRID PR link without explicit instructions, this skill applies.

## Arguments

- `/cubrid-pr-review <pr-url>` — Review the given PR
- `/cubrid-pr-review` — Ask the user for a PR URL

## Output Format

Write the report to `PR-<NUMBER>-report.md` in the repo root (or current directory). The report is **local-only** — never post it to GitHub.

### Language Rules

- **Section headers (`##`)**: English
- **Subsection headers (`###`)**: English (Note: `cubrid-jira-issue-write` uses Korean `###`; for review reports we keep `###` English to match the Findings category names like `Blocking (must fix)`.)
- **Body text**: Korean
- **Tables**: Korean content, English column headers OK
- **Code snippets, function names, file paths**: keep as-is

### Character Restrictions

- **NO emoji** (no checkmarks, crosses, rockets, warnings, etc.) (These examples appear here only as illustrations of what NOT to put in the report.)
- **NO non-BMP Unicode** or special symbols (no `->`, `<-`, check/cross marks, stars, bullets like `●`/`■`)
- Use ASCII alternatives: `->` instead of arrows, `[x]`/`[ ]` for checkboxes, `*`/`-` for bullets
- **Reason**: matches house style across `cubrid-pr-create` and `cubrid-jira-issue-write`, and avoids encoding issues if the report is later pasted into a ticket comment.

### Length Budget

- **Hard cap: 80 lines** for typical PRs, **200 lines** for large multi-module PRs.
- If the report would exceed 80 lines, first try to compress: drop low-signal findings, shorten code excerpts to the smallest illustrative span, collapse adjacent items. Going over 96 lines is permitted only when the PR has 5+ Blocking findings.

### Report Template

```markdown
# PR #<NUMBER> 코드 리뷰 보고서

**PR:** [<OWNER>/<REPO>#<NUMBER>](https://github.com/<OWNER>/<REPO>/pull/<NUMBER>)
**제목:** <PR title>
**작성자:** <author>
**HEAD SHA:** `<head_sha>`
**리뷰 일시:** <today's date>

> **TL;DR** (<Verdict>): 1-3 문장으로 결론과 핵심 이슈 1-2개.

## Summary

- **변경 요약**: 한 줄로 PR이 무엇을 바꾸는지
- **주요 이슈**: 가장 중요한 1-2 항목 (없으면 "없음")
- **확인 필요 사항**: 작성자가 확인/응답해야 할 질문 (없으면 "없음")

---

## Findings

<see Findings Rules below. 발견 사항이 전혀 없으면 이 섹션 본문을 `없음` 한 줄로 대체하고 아래 세 subsection은 모두 생략한다. 일부 카테고리만 비어 있다면 채워진 카테고리만 남기고 비어 있는 subsection은 통째로 생략한다.>

### Blocking (must fix)
<버그, 메모리/동시성 안전성 위반 등 머지 전에 반드시 수정되어야 하는 항목.>

### Non-blocking (should consider)
<수정을 권하지만 머지를 막지는 않는 사항.>

### Questions for the author
<작성자에게 확인이 필요한 질문.>

## JIRA Context
<JIRA 티켓 정보 요약 및 PR이 티켓 의도와 일치하는지 한두 줄. JIRA 없으면 섹션 생략.>

## Existing Comments
<PR에 달려 있고 작성자/메인테이너 답변이 없는 top-level 코멘트(`in_reply_to_id == null` 인 것 중 author/maintainer 답글이 없는 것)만 짧은 표로 정리. 없으면 섹션 생략.>
```

### Top-of-Report Summary Rules

The `> **TL;DR**` blockquote and `## Summary` block are **required** for every report. They exist so a reader can decide in 20 seconds whether the PR is shippable.

- **TL;DR carries the verdict.** TL;DR 라벨은 `**TL;DR**` 뒤 괄호 안에 `Blocking` / `Non-blocking` / `작성자 확인 필요` 중 하나로 적고, 그 뒤 1-3 문장 평문 한국어로 핵심 이슈를 요약한다. 같은 결론을 Summary에 다시 쓰지 않는다.
- **Summary bullets**: 각 항목 한 줄. 자세한 내용은 `## Findings`에서 풀어 쓴다.
- 사소한 PR(주석/typo)에서도 TL;DR 한 줄은 항상 포함한다.

### Findings Rules

This is the single source of truth for how findings are written. The template above just refers here.

- **Signal over volume.** 발견 사항이 없으면 본문을 `없음` 한 줄로 끝낸다. 채우기용 항목을 만들지 않는다. 30줄짜리 보고서가 300줄짜리 보고서보다 낫다. TL;DR과 Summary는 본문의 **요약**이지 본문 자체가 아니다 — 같은 문장을 그대로 복붙하지 않는다.
- **One sentence per finding** is the default — `파일:라인 + 한 문장 설명 + 근거 코드/진단`. 코드 인용은 1-5줄로 충분하다.
- **Every finding needs evidence**: 코드 스니펫(파일:라인)이나 LSP/clangd 진단. "might be wrong" 같은 모호한 지적은 금지.
- **Only flag issues introduced by this PR.** 이미 존재하던 문제, 이미 다른 코멘트에서 지적된 항목, 수정되지 않은 라인은 제외한다.
- **Skip what CI catches.** 포맷팅, astyle, cppcheck 경고 등 CI가 잡는 항목은 보고하지 않는다.

## Execution Steps

### Step 1: Setup

Parse the PR URL with the helper script and capture metadata in one shot:

```bash
scripts/check-prereqs.sh "$PR_URL"
```

The script prints JSON with `owner`, `repo`, `number`, `head_sha`, `base_ref`, `title`, `body`, `author`, `state`, `draft`. If it exits non-zero, surface the message and stop. If the PR is not open, or is marked draft, warn the user once and ask whether to proceed before continuing.

### Step 2: Gather Context (parallel)

Run these in parallel:

1. **PR diff:** `gh pr diff <NUMBER> -R <OWNER>/<REPO>`. If `gh pr diff` returns empty or fails, surface the error and stop — there is nothing to review.
2. **Existing PR comments**:
   ```bash
   gh api "repos/<OWNER>/<REPO>/pulls/<NUMBER>/comments" --jq '.[] | {id, user: .user.login, path, line: .original_line, in_reply_to_id, body}'
   gh api "repos/<OWNER>/<REPO>/issues/<NUMBER>/comments" --jq '.[] | {id, user: .user.login, body}'
   ```
3. **JIRA context** (if PR title contains `CBRD-XXXXX`): invoke `/jira CBRD-XXXXX` to fetch ticket context.
4. **Read `reference.md`** (sibling file in this skill's directory) for CUBRID-specific review knowledge: error-code six-place rule, memory/error-handling conventions, lock/page-buffer/WAL/MVCC protocols, build-mode guards, key data structures, false-positive guidance. If `reference.md` is missing on this checkout, warn the user once and proceed using only the review categories listed in Step 3 below — do not invent CUBRID-specific rules.
5. **Read any CLAUDE.md / AGENTS.md** in directories containing changed files. Use Glob to walk ancestor directories of each changed file looking for these context files.

### Step 3: Review

Read the **full functions** surrounding each diff hunk, not just the hunk. Trace call chains where it matters. Aim for **signal**: prefer reading one suspicious function carefully over skimming ten safe ones. Investigate broadly, report narrowly — deep reading is for filtering findings, not justifying long reports.

Focus on these high-signal categories for CUBRID. One sentence each — the detailed sub-checklists live in `reference.md`:

- **Logic & correctness**: did the change introduce a wrong branch, a missing error path, or an uninitialized read?
- **Memory safety**: are CUBRID's allocator/free-and-init conventions followed and are all error paths leak-free?
- **Concurrency & thread safety**: is shared state protected, and is lock/latch ordering preserved across all paths?
- **Architecture vs JIRA intent**: does the implementation match the ticket's stated goal, and are build-mode guards (`SERVER_MODE`/`SA_MODE`/`CS_MODE`) and updated callers correct?

If the diff touches the SQL parser, broker protocol, or CCI client interface, also check buffer/integer overflow and unchecked input. Skip generic security checklists otherwise.

**LSP analysis (optional).** If `compile_commands.json` is available, run `lsp_diagnostics` on changed files for clangd warnings on changed lines, `lsp_hover`/`lsp_goto_definition` on suspicious types, and `lsp_find_references` if a function signature changed. Skip silently if LSP is unavailable.

If `reference.md` is present and flags a rule (e.g., new error code -> 6 places), don't restate the rule body — link to it by name and point to the file:line that needs updating.

### Step 4: Filter

Drop findings that are:

- **Pre-existing** (not introduced by this PR)
- **Already raised** in existing PR comments
- **Stylistic** (formatting, naming) unless CLAUDE.md mandates it
- **On unmodified lines**
- **Out of the PR's stated scope** — don't critique the design of code the PR didn't intend to change, even if the diff exposed it

Every surviving finding needs a code snippet or diagnostic as evidence.

### Step 5: Write the Report

1. **Draft the TL;DR + Summary first.** Write the verdict label and conclusion before the body — this forces a clear stance and reveals whether the rest of the report supports it.
2. **Write Findings tightly.** One sentence per item. Group as Blocking / Non-blocking / Questions, omitting any subsection that has no items. If no category has any items, replace the section body with a single `없음` line and omit all three subsections.
3. **Add JIRA Context and Existing Comments only if useful.** Omit empty sections.
4. **Save** to `PR-<NUMBER>-report.md` in the repo root (or cwd).
5. **Print** three things so the user can sanity-check the call at a glance: (1) the saved file path, (2) the verdict label extracted from the TL;DR (`Blocking` / `Non-blocking` / `작성자 확인 필요`), (3) the TL;DR sentence(s) without the label prefix.

## Example Output

A short finished report looks like this — use it as a shape anchor, not a template to fill out verbatim. The example below is about 30 lines, well under half the 80-line budget; for a typical PR this is plenty.

```markdown
# PR #6950 코드 리뷰 보고서

**PR:** [CUBRID/CUBRID#6950](https://github.com/CUBRID/CUBRID/pull/6950)
**제목:** [CBRD-26583] Re-enable OOS OID replacement in heap records
**작성자:** vimkim
**HEAD SHA:** `abc1234`
**리뷰 일시:** 2026-05-06

> **TL;DR** (Blocking): `heap_record_replace_oos_oids` 에러 경로에서 `pgbuf_unfix` 누락으로 페이지 핀 누수 가능. 해당 한 곳만 고치면 머지 가능.

## Summary

- **변경 요약**: heap 레코드의 OOS OID 치환 로직을 `feat/oos`에 다시 활성화
- **주요 이슈**: `heap_file.c:12345` 에러 경로 페이지 핀 누수
- **확인 필요 사항**: 없음

---

## Findings

### Blocking (must fix)
- `src/storage/heap_file.c:12345` — `er_set` 후 `goto exit` 전에 `pgbuf_unfix(thread_p, page_p)` 누락. 해당 함수 진입에서 `pgbuf_fix` 했으므로 모든 종료 경로에서 unfix 필요. 근거: 같은 함수 line 12302의 정상 종료 경로에는 unfix 존재.

## JIRA Context
CBRD-26583 의 목표는 OOS OID 치환 재활성화. 본 PR은 그 범위 안.
```

(JIRA Context only; Existing Comments was omitted because no unresolved top-level comments existed. `Non-blocking` and `Questions for the author` subsections are also omitted because they had no items.)
