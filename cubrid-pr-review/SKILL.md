---
name: cubrid-pr-review
description: "CUBRID C/C++ PR code review with LSP/clangd analysis and C++ safety checks. Use when reviewing a CUBRID pull request, when the user shares a GitHub PR URL from a CUBRID repo, asks to review or check a pull request, or requests LSP-based analysis of PR changes. Even if the user just pastes a CUBRID PR link without explicit instructions, this skill applies."
argument-hint: "<pr-url>"
model: opus
effort: max
allowed-tools: Bash(gh *), Bash(git *), Bash(jq *), Bash(curl *), Bash(${CLAUDE_SKILL_DIR}/scripts/*), Read, Write, Glob, Grep, Agent, mcp__plugin_oh-my-claudecode_t__lsp_diagnostics, mcp__plugin_oh-my-claudecode_t__lsp_diagnostics_directory, mcp__plugin_oh-my-claudecode_t__lsp_hover, mcp__plugin_oh-my-claudecode_t__lsp_goto_definition, mcp__plugin_oh-my-claudecode_t__lsp_find_references, mcp__plugin_oh-my-claudecode_t__lsp_document_symbols
---

You are reviewing a CUBRID database engine pull request. CUBRID is a multi-threaded, open-source RDBMS with a large C/C++ codebase.

**PR URL (required):** $ARGUMENTS

---

## Step 1: Setup

Parse the PR URL to extract `OWNER`, `REPO`, `NUMBER`. Fetch PR metadata:

```bash
gh api "repos/OWNER/REPO/pulls/NUMBER"
```

Extract: `head_sha`, `base_ref`, `title`, `body`, `author`, `state`. If the PR is not open, warn but continue (closed/merged PRs can still be reviewed).

---

## Step 2: Gather Context (parallel)

Run these in parallel:

1. **PR diff:** `gh pr diff <NUMBER> -R <OWNER>/<REPO>`
2. **Existing PR comments** (inline + conversation):
   ```bash
   gh api "repos/OWNER/REPO/pulls/NUMBER/comments" --jq '.[] | {id, user: .user.login, path, line: .original_line, in_reply_to_id, body}'
   gh api "repos/OWNER/REPO/issues/NUMBER/comments" --jq '.[] | {id, user: .user.login, body}'
   ```
3. **JIRA context** (if PR title contains `CBRD-XXXXX`):
   ```bash
   cubrid-jira-search CBRD-XXXXX
   ```
4. **Read `${CLAUDE_SKILL_DIR}/reference.md`** for CUBRID-specific review knowledge.
5. **Read any CLAUDE.md / AGENTS.md** in directories containing changed files.

---

## Step 3: Deep Review

**CRITICAL: Do NOT save tokens, skip context, or abbreviate your analysis during this step.** Read every changed function in full. Follow every call chain that matters. This is where bugs hide and shallow review misses them. Be exhaustive.

For each changed file, read the **full functions** surrounding each diff hunk (not just the hunk). Then analyze:

### Logic & Correctness
- Null dereference, off-by-one, use-after-free, uninitialized variables
- Missing error checks, wrong operators, logic inversions
- Resource leaks (pgbuf_fix without pgbuf_unfix, db_value without db_value_clear)
- Error propagation after `er_set()` — must return error or goto cleanup
- Verify changed `if`/`switch`/`for` conditions are correct

### C++ Safety & Memory
- `free()` without `free_and_init()` (CUBRID always nullifies after free)
- Bare `malloc`/`free` instead of `db_private_alloc`/`free_and_init`
- Double-free, use-after-free
- Missing error path cleanup

### Concurrency & Thread Safety
- Lock ordering violations (acquiring A then B in one path, B then A in another)
- Missing locks before shared state access
- Thread-unsafe static/global variables
- Missing atomic operations on shared counters
- pgbuf latches held across blocking operations
- Deadlock potential
- MVCC snapshot misuse

### Architecture & Design
- Does the implementation match the JIRA ticket intent (if available)?
- Build mode awareness: is new code correctly guarded with SERVER_MODE/SA_MODE/CS_MODE?
- If a function signature changed, check all callers are updated
- New error codes require updates in 6 places (see reference.md)

### Security
- Buffer overflows, integer overflows
- Unchecked user input reaching internal functions
- SQL injection vectors in query processing code

### LSP Analysis (if compile_commands.json available)
Use LSP tools on changed files:
- `lsp_diagnostics` for clangd warnings on changed lines
- `lsp_hover` on suspicious types/variables
- `lsp_find_references` if a function signature changed
- `lsp_goto_definition` to verify type assumptions

If LSP is not available, skip silently and rely on manual analysis.

---

## Step 4: Filter

Discard findings that are:
- **Pre-existing** (not introduced by this PR)
- **Already raised** in existing PR comments
- **Stylistic** (formatting, naming preferences) unless CLAUDE.md requires it
- **On unmodified lines**

Every surviving finding needs **evidence**: a code snippet or diagnostic.

---

## Step 5: Report

Write a Korean-language review report as `PR-<NUMBER>-report.md` in the repository root (or current directory if not in a repo).

```markdown
# PR #<NUMBER> 코드 리뷰 보고서

**PR:** [<OWNER>/<REPO>#<NUMBER>](https://github.com/<OWNER>/<REPO>/pull/<NUMBER>)
**제목:** <PR title>
**작성자:** <author>
**HEAD SHA:** `<head_sha>`
**리뷰 일시:** <today's date>

---

## 1. PR 개요
<PR 목적 및 주요 변경 사항 요약>
<변경 파일 목록>

## 2. JIRA 컨텍스트
<JIRA 티켓 정보 요약 (해당 시, 없으면 섹션 생략)>

## 3. 리뷰 결과

### 3.1 심각한 이슈 (버그, 안전성, 동시성)
<발견 사항 또는 "이슈 없음">

### 3.2 개선 권장 사항
<발견 사항 또는 "없음">

### 3.3 기존 리뷰 코멘트 현황
<미응답 코멘트가 있으면 표로 정리>

## 4. 종합 평가
<결론 및 권장 사항>
```

Tell the user the report file path when done.

---

## Principles

- **Only flag issues introduced by this PR.**
- **Every finding needs evidence.** Code snippet or diagnostic.
- **Don't duplicate** existing PR comments.
- **Skip what CI catches.** No formatting or compiler warning duplicates.
- **Do not post comments to GitHub.** Report is local only.
- **Be thorough on what matters.** Do not cut corners on logic, architecture, security, or threading analysis. Read full functions, trace call chains, verify error paths completely.
