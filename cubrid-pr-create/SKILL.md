---
name: cubrid-pr-create
description: Open a GitHub pull request for the CUBRID project. Use this when the user wants to create a PR for their CUBRID changes.
---

# CUBRID PR Creator

Create GitHub pull requests for the CUBRID project following team conventions.

## When to Use

- User says "create pr", "make pr", "PR 만들어", "PR 올려", "풀리퀘"
- User wants to push changes and open a PR against CUBRID/CUBRID or a fork

## Arguments

Pass optional arguments to customize:

- `/cubrid-pr-create CBRD-26583` — Use this JIRA ticket number
- `/cubrid-pr-create CBRD-26583 feat/oos` — Ticket + base branch
- `/cubrid-pr-create` — Interactive: detect from branch name or ask

## Conventions

### Title Format

```
[CBRD-XXXXX] Short English description
```

- The JIRA ticket number is **required**. Extract from branch name (e.g., `cbrd-26583-oos-compact` → `CBRD-26583`) or ask the user.
- Description should be concise (<60 chars after the tag), in English.
- Use imperative mood: "Fix", "Add", "Refactor", "Support", not "Fixed", "Adding".

### Two artifacts, two audiences

This skill produces **two** things, and keeping them separate is the whole point:

1. **The PR body** — a short, plain-Korean, **one-screen** summary. It answers "what / why / where to look" in language a Korean 11th-grade student (고2) could follow. It carries **no** deep detail.
2. **The detailed explanation doc** — a separate markdown file in the `my-cubrid-docs` repo that holds the full technical write-up. The PR body links to it.

Never put the deep detail in the PR body. If a paragraph is too technical for a smart teenager, it belongs in the doc.

### Body Format (the one-screen summary)

- **Section headers (`##`)**: Always in **English**
- **Body text**: Always in **Korean**, plain and simple
- **Code snippets, function names, file paths**: Keep as-is (English/code)
- **Length**: The whole body must fit on one screen — roughly **25–35 lines**. If it grows past that, move detail into the doc.

The JIRA issue link **must** appear at the very top, before any header. The body has three short sections and ends with a link to the detailed doc:

```markdown
https://jira.cubrid.org/browse/CBRD-XXXXX

> **TL;DR**: 이 PR이 무엇을 바꾸는지·왜 바꾸는지 1–2문장, 쉬운 한국어로.

## What Changed

- 무엇을 바꿨는지 쉬운 말로 2–4줄. 바꾼 파일/함수 이름은 그대로 적는다.

## Why

- 왜 이 변경이 필요한지 1–2줄. 배경과 문제를 쉬운 말로.

## Review Points

- 리뷰어가 꼭 봐야 할 곳. `heap_file.c:12345`처럼 파일/함수까지 짚는다.

---

📖 **자세한 설명**: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md
```

The 📖 line is the canonical pointer to the doc. **If the link needs context** — a caveat, a follow-up note, or "여기를 먼저 읽으세요" guidance — add a short `## Remarks` section just above the `---` and put the md file's GitHub URL there instead of (or in addition to) the bare 📖 line:

```markdown
## Remarks

- 이 변경은 `feat/oos`에서만 적용됩니다. 배경과 엣지 케이스는 아래 문서를 참고하세요.
- 자세한 설명: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md
```

Either way, the doc's GitHub URL appears in the body exactly once — don't duplicate the bare 📖 line and the Remarks link. Keep whichever fits, and keep the body within one screen.

For a trivial PR (typo/comment fix), the `## What Changed`/`## Why`/`## Review Points` sections may be dropped, but the TL;DR line and the doc link (📖 line or Remarks) are always present.

### Writing for an 11th-Grade Korean Reader

The PR body must be understandable by a Korean high-school 11th grader (고2): fluent in Korean, but with **zero** CUBRID-internal knowledge. This is a **clarity** bar, not a precision tradeoff — stay concrete (name the real file, function, behavior) but phrase every explanation in plain words.

- **Short sentences.** One idea per sentence. No sentence runs past two lines.
- **Plain words over jargon.** Prefer everyday Korean. When a CUBRID/DB term is unavoidable, gloss it in one clause on first use: "OOS (큰 컬럼 값을 따로 떼어 다른 페이지에 저장하는 방식)". After the first gloss, use the term raw.
- **Explain the "why" like you would to a smart teenager.** A one-line analogy is welcome if it earns its place.
- **No filler.** Drop "본 PR은...", "전반적으로...", "필요에 따라...". State the fact directly.
- **Keep code identifiers in English code-style.** `pgbuf_unfix`, `MVCC`, `feat/oos` — don't translate or paraphrase.
- **The body stands alone.** A reviewer who never clicks the JIRA link or the doc still knows what changed and why, on one screen.
- **Depth goes to the doc, not the body.** If you want a third paragraph, that paragraph belongs in the detailed markdown file.

### Detailed Explanation Doc (separate repo)

Every PR's deep technical write-up lives in the `my-cubrid-docs` repo, not in the PR body.

- **Repo path**: `/home/vimkim/gh/my-cubrid-docs` (remote `origin` → `github.com/vimkim/my-cubrid-docs`)
- **Directory**: `cbrd-XXXXX/` — **lowercase** `cbrd-` + the JIRA number. Create it if missing.
- **Filename**: `CBRD-XXXXX-<slug>.md` — **uppercase** `CBRD-` in the filename, `<slug>` is a short kebab-case description, e.g. `CBRD-26583-reenable-oos-oid-replacement.md`
- **Published URL** (after commit + push):
  `https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md`
  (directory listing: `https://github.com/vimkim/my-cubrid-docs/tree/main/cbrd-XXXXX/`)

The doc holds what used to be the long PR body and more — it can be as technical as CUBRID maintainers need:

- `## Description` — 왜 이 변경이 필요한지 배경 설명
- `## Implementation` — 주요 변경 내용을 bullet로. 파일명, 함수명 포함.
- `## Remarks` — 제한 사항, 주의점, 후속 작업
- `## Test Plan` (관련 있으면) — 테스트 방법 및 검증 계획
- 다이어그램, 엣지 케이스, 호환성/성능 영향 등 필요한 만큼

Doc convention matches the PR body: English `##` headers, Korean prose, code identifiers as-is.

## Execution Steps

### Step 1: Gather Context

Run these in parallel:

1. `git status` — check for uncommitted changes
2. `git branch -vv` — current branch and tracking info
3. `git remote -v` — available remotes

If there are uncommitted changes, warn the user and ask whether to proceed or commit first.

### Step 2: Determine PR Parameters

1. **JIRA ticket**: Extract from arguments, branch name (`cbrd-XXXXX` or `CBRD-XXXXX` pattern), or ask.
2. **Base branch**: If not specified, detect:
   - For `feat/oos*` branches → base is `feat/oos`
   - For `CBRD-*` branches → base is `develop`
   - For `cubvec/*` branches → base is `cubvec/cubvec`
   - Otherwise ask the user
3. **Target repo**: Default `CUBRID/CUBRID`. Use `--repo` if different.
4. **Source**: Determine the user's fork remote (typically `vk` for `vimkim/cubrid`). The head ref format is `<github-user>:<branch>`.
5. **Docs repo**: Confirm `/home/vimkim/gh/my-cubrid-docs` exists (it should). The doc directory will be `cbrd-XXXXX/`.

### Step 3: Analyze Changes

1. Fetch the base branch: `git fetch <upstream-remote> <base-branch>`
2. Show commits: `git log --oneline <upstream>/<base>..HEAD`
3. Show diff stat: `git diff <upstream>/<base>...HEAD --stat`
4. Read the full diff to understand all changes.
5. If a JIRA ticket was identified, fetch context with `/jira CBRD-XXXXX` for richer description.

### Step 4: Write the Detailed Explanation Doc

1. Pick a short kebab-case `<slug>` from the change (e.g. `reenable-oos-oid-replacement`).
2. Create the directory and file:
   `/home/vimkim/gh/my-cubrid-docs/cbrd-XXXXX/CBRD-XXXXX-<slug>.md`
3. Write the full technical explanation there: `## Description`, `## Implementation`, `## Remarks`, and `## Test Plan` if relevant — with file/function names, diagrams, edge cases.
4. **Grill it.** Run the detailed doc through `/grill-with-docs` (see the Mandatory section below). The doc is the substantive artifact, so this is where the grill loop applies.

### Step 5: Commit and Push the Docs Repo

```bash
git -C /home/vimkim/gh/my-cubrid-docs add cbrd-XXXXX/
git -C /home/vimkim/gh/my-cubrid-docs commit -m "$(cat <<'EOF'
docs(CBRD-XXXXX): add PR explanation for <slug>

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
git -C /home/vimkim/gh/my-cubrid-docs push origin main
```

After pushing, the doc is live at:
`https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md`

This is the URL you put in the PR body's 📖 link. (`.omc` is git-ignored in this repo, so `git add cbrd-XXXXX/` won't pick up agent state.)

### Step 6: Draft the One-Screen PR Body

Write the simple, one-screen Korean body — TL;DR + `## What Changed` + `## Why` + `## Review Points` — and end it with the 📖 link to the doc from Step 5. Keep it within 25–35 lines and at the 11th-grade-reader bar.

**Draft the TL;DR first**, before the body sections. This forces a clear thesis and reveals when the PR is doing too many unrelated things.

Show the draft to the user and ask for confirmation before creating.

### Step 7: Push the Branch and Create the PR

1. Push the branch to the user's fork:
   ```bash
   git push <fork-remote> <branch> -u
   ```
2. Create the PR using `gh`:
   ```bash
   gh pr create --repo CUBRID/CUBRID \
     --draft \
     --base <base-branch> \
     --head <user>:<branch> \
     --assignee vimkim \
     --title "[CBRD-XXXXX] Title" \
     --body "$(cat <<'EOF'
   https://jira.cubrid.org/browse/CBRD-XXXXX

   > **TL;DR**: 한두 문장, 쉬운 한국어 요약.

   ## What Changed

   - 쉬운 말로 무엇을 바꿨는지...

   ## Why

   - 쉬운 말로 왜 바꿨는지...

   ## Review Points

   - `파일.c:줄번호` 짚어주기...

   ---

   📖 **자세한 설명**: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md
   EOF
   )"
   ```
3. Print the resulting PR URL.

## Example Output

```
Doc pushed: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-26583/CBRD-26583-reenable-oos-oid-replacement.md
PR created: https://github.com/CUBRID/cubrid/pull/6950

Title: [CBRD-26583] Re-enable OOS OID replacement in heap records
Base:  feat/oos
Head:  vimkim:feat/oos-replace-oos-oid
```

## Tips

- If the branch has already been pushed, skip the branch push step.
- If a PR already exists for the branch, show it instead of creating a duplicate. If the doc has changed, still commit/push the docs repo and update the PR body link.
- For multi-commit PRs, summarize the overall change rather than listing each commit message.
- Always use `gh pr create` with heredoc for the body to handle multi-line Korean text correctly.
- The one-screen rule is a hard limit. When in doubt, cut a sentence from the body and add it to the doc.

## Mandatory: Iterate with Grill-with-Docs

The **detailed explanation doc** (Step 4) must go through `/grill-with-docs` before the docs repo is committed and pushed. Do not push a single-pass doc. Single-pass write-ups drift toward hand-wavy filler and `## Implementation` bullets that hide what actually changed.

This step is required, not optional. It applies to every PR. No agent-side judgment — including size, scope, perceived triviality, or perceived risk — is a valid skip criterion. The only legitimate skip is when the user, in the message that triggered this skill, explicitly says "skip grill" or "don't grill this" (or unambiguous equivalent: "no grill", "skip the grill loop", "just push it"). If in doubt, do the grill loop.

**How to hand off:**

1. **Draft the doc to its real path** (`/home/vimkim/gh/my-cubrid-docs/cbrd-XXXXX/CBRD-XXXXX-<slug>.md`) — the loop revises it in place.
2. **Invoke `/grill-with-docs`** with:
   - **Topic & purpose**: PR title, JIRA ticket, target reviewers (CUBRID maintainers)
   - **Output path**: the doc file (the loop revises in place)
   - **Source material**: the diff (`git diff <upstream>/<base>...HEAD`), `/jira CBRD-XXXXX` output, related issues/PRs
   - **Review angle**: completeness and correctness of `## Description` / `## Implementation` / `## Remarks`, adherence to CUBRID doc conventions (Korean body, English `##` headers), every CUBRID-internal term glossed on first use
   - **Round cap**: default 5
3. **After approval**, commit + push the docs repo (Step 5), then draft the one-screen PR body (Step 6) and create the PR (Step 7).

The one-screen PR body is then derived from the approved doc — keep it simple, precise, and at the 11th-grade-reader bar. The body does not need its own grill loop; its job is only to summarize and link.
