---
name: cubrid-pr-create
description: Open a GitHub pull request for the CUBRID project with a [CBRD-XXXXX] title, Korean PR body, linked detailed doc, explicit AS-IS/TO-BE contrast when the change supports it, and pre-publish material checks. Use when the user wants to create, draft, push, or publish a CUBRID PR, including requests like "create pr", "make pr", "PR 만들어", "PR 올려", or "풀리퀘".
---

# CUBRID PR Creator

Create GitHub pull requests for the CUBRID project following team conventions.

## Non-Negotiable Output Contracts

- The PR body always uses exactly these `##` sections, in this order: `## Purpose`, `## Implementation`, `## Remarks`.
- Keep `##` headers in English and body prose in plain Korean.
- Put the JIRA issue URL at the very top, before `## Purpose`.
- Keep the whole PR body to one screen, roughly 25-35 lines.
- Put deep technical detail in the separate markdown doc, not in the PR body.
- When the change has a clear before/after contrast, state `AS-IS` and `TO-BE` explicitly inside `## Purpose` in both the PR body and detailed doc. Do not add new top-level sections for them.
- Never include local absolute paths, `file://` URLs, or machine-specific workspace paths in PR material. Use repo-relative paths or public GitHub/JIRA URLs.
- Never include project shortcut commands beginning with the `just` task runner in PR material. Replace them with the actual public verification command, or describe the verification outcome in words.
- Run the bundled material checker before showing the body draft, before committing the doc repo, and before creating the PR.

## Arguments

Pass optional arguments to customize:

- `/cubrid-pr-create CBRD-26583` - Use this JIRA ticket number
- `/cubrid-pr-create CBRD-26583 feat/oos` - Ticket plus base branch
- `/cubrid-pr-create` - Detect from branch name or ask

## Title Format

```text
[CBRD-XXXXX] Short English description
```

- The JIRA ticket number is required. Extract it from arguments or from branch names like `cbrd-26583-oos-compact`; otherwise ask the user.
- Keep the description concise, under 60 characters after the tag.
- Use imperative mood: `Fix`, `Add`, `Refactor`, `Support`; not `Fixed` or `Adding`.

## Two Artifacts, Two Audiences

Produce two separate artifacts:

1. The PR body: a short, plain-Korean one-screen summary. It answers what changed, why it matters, where reviewers should look, and, when possible, the AS-IS/TO-BE contrast.
2. The detailed explanation doc: a separate markdown file in the `my-cubrid-docs` repo. It holds the full technical write-up, including the detailed AS-IS/TO-BE explanation, and the PR body links to it.

Do not put deep detail in the PR body. If a paragraph is too technical for a Korean 11th-grade student with no CUBRID-internal knowledge, move it to the doc.

## PR Body Format

Use this exact section shape for every PR, including trivial typo or comment fixes:

```markdown
https://jira.cubrid.org/browse/CBRD-XXXXX

## Purpose

- 이 PR이 해결하려는 문제와 필요한 이유를 1-3줄로 설명합니다.
- 가능하면 `AS-IS:` 로 현재 동작/한계를 한 줄, `TO-BE:` 로 바뀐 동작/목표 상태를 한 줄로 대비합니다.

## Implementation

- 실제로 바꾼 내용을 2-5줄로 설명합니다.
- 파일명, 함수명, 브랜치명은 `src/...`, `heap_record_replace_oos_oids`, `feat/oos`처럼 그대로 씁니다.

## Remarks

- 리뷰어가 먼저 봐야 할 곳, 제한 사항, 후속 작업을 적습니다.
- 자세한 설명: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md
```

Rules:

- Do not use `## What Changed`, `## Why`, `## Review Points`, `## Description`, or a top-level `## Test Plan` in the PR body.
- Do not drop any of the three required sections. If a section is small, keep it short.
- Put the detailed doc URL exactly once, normally as the last bullet in `## Remarks`.
- The body must stand alone: a reviewer who does not open JIRA or the doc still understands the change at a high level.

### AS-IS / TO-BE Rule

- Use explicit `AS-IS:` and `TO-BE:` bullets in `## Purpose` when the PR changes current behavior, policy, default values, data flow, API behavior, recovery behavior, or operational procedure.
- Keep PR-body AS-IS/TO-BE bullets one sentence each. Put root cause, code path, and edge cases in the detailed doc.
- In the detailed doc, put AS-IS/TO-BE under `## Purpose` as bullets or a compact table, then explain implementation under `## Implementation`.
- Do not invent a TO-BE. If the intended behavior is not in the diff, JIRA, design doc, or user-provided context, ask before publishing or write `TO-BE: TBD - 합의 미확인` in the detailed doc and keep the PR body more conservative.
- Do not force AS-IS/TO-BE for pure cleanup, comment-only changes, dependency bumps, or internal maintenance where no reader-facing before/after contrast exists.

## Writing for an 11th-Grade Korean Reader

The PR body must be understandable by a Korean high-school 11th grader: fluent in Korean, but with zero CUBRID-internal knowledge.

- Use short sentences. One idea per sentence.
- Prefer everyday Korean. When a CUBRID or database term is unavoidable, gloss it once: `OOS (큰 컬럼 값을 따로 떼어 다른 페이지에 저장하는 방식)`.
- Keep code identifiers, file paths, branch names, and function names in English code style.
- Explain the reason for the change concretely. Avoid filler like `본 PR은`, `전반적으로`, and `필요에 따라`.
- Move any third paragraph of technical explanation into the detailed doc.

## Detailed Explanation Doc

Every PR's deep technical write-up lives in the `my-cubrid-docs` repo, not in the PR body.

- Resolve the local docs repo as `${CUBRID_PR_DOCS_REPO:-$HOME/gh/my-cubrid-docs}`.
- Its `origin` remote should point to `github.com/vimkim/my-cubrid-docs`.
- Directory: `cbrd-XXXXX/` using lowercase `cbrd-`.
- Filename: `CBRD-XXXXX-<slug>.md` using uppercase `CBRD-` in the filename.
- Published URL: `https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/CBRD-XXXXX-<slug>.md`.

Use the same top-level section contract in the doc:

- `## Purpose` - background, problem, intended outcome, and AS-IS/TO-BE contrast when applicable
- `## Implementation` - full technical change list with repo-relative file paths and function names
- `## Remarks` - limits, risks, compatibility notes, reviewer focus, follow-up, and verification notes

If test details need structure, put `### Test Plan` under `## Remarks` instead of adding another top-level PR-format section.

Doc convention matches the PR body: English headers, Korean prose, code identifiers as-is.

## Material Checker

Use the bundled checker at `scripts/check-pr-material.sh`, relative to this skill directory. Resolve it once as `checker="<this-skill-directory>/scripts/check-pr-material.sh"` before running commands from the CUBRID worktree. It validates the PR body section contract and rejects forbidden machine-local material.

Run it on the generated PR body file and the detailed doc before the user confirms, before committing the docs repo, and again immediately before `gh pr create`:

```bash
body_file="$(mktemp)"
# Write the PR body into "$body_file".
bash "$checker" --body "$body_file" "$doc_file"
```

If it fails, edit the PR body and doc until it passes. Do not ask the user to approve material that still contains local paths, `file://` URLs, machine-specific workspace paths, old PR headings, or task-runner shortcut commands.

## Execution Steps

### Step 1: Gather Context

Run these in parallel:

1. `git status` - check for uncommitted changes
2. `git branch -vv` - current branch and tracking info
3. `git remote -v` - available remotes

If there are uncommitted changes, warn the user and ask whether to proceed or commit first.

### Step 2: Determine PR Parameters

1. JIRA ticket: extract from arguments, branch name (`cbrd-XXXXX` or `CBRD-XXXXX`), or ask.
2. Base branch:
   - For `feat/oos*` branches, use `feat/oos`.
   - For `CBRD-*` branches, use `develop`.
   - For `cubvec/*` branches, use `cubvec/cubvec`.
   - Otherwise ask the user.
3. Target repo: default to `CUBRID/CUBRID` unless the user specifies another repo.
4. Source: determine the user's fork remote and use `<github-user>:<branch>` for the PR head.
5. Docs repo: set `docs_repo="${CUBRID_PR_DOCS_REPO:-$HOME/gh/my-cubrid-docs}"` and confirm it exists.

### Step 3: Analyze Changes

1. Fetch the base branch: `git fetch <upstream-remote> <base-branch>`.
2. Show commits: `git log --oneline <upstream>/<base>..HEAD`.
3. Show diff stat: `git diff <upstream>/<base>...HEAD --stat`.
4. Read the full diff to understand all changes.
5. If a JIRA ticket was identified, fetch context with `/jira CBRD-XXXXX` for richer description.

### Step 4: Write the Detailed Explanation Doc

1. Pick a short kebab-case `<slug>` from the change, such as `reenable-oos-oid-replacement`.
2. Create `doc_dir="$docs_repo/cbrd-XXXXX"` and `doc_file="$doc_dir/CBRD-XXXXX-<slug>.md"`.
3. Write the full technical explanation with `## Purpose`, `## Implementation`, and `## Remarks`. If a before/after contrast exists, make AS-IS/TO-BE explicit under `## Purpose`.
4. Use repo-relative paths like `src/storage/heap_file.c`, never local absolute paths.
5. Grill the doc using the mandatory loop below. The doc is the substantive artifact, so the grill loop applies there.

### Step 5: Draft the One-Screen PR Body

1. Write the PR body to `body_file="$(mktemp)"`.
2. Use only the required section order: `## Purpose`, `## Implementation`, `## Remarks`.
3. Keep it within 25-35 lines and at the 11th-grade-reader bar.
4. If the change has a clear before/after contrast, include short `AS-IS:` and `TO-BE:` bullets in `## Purpose`.
5. Put the detailed doc URL exactly once as the final bullet in `## Remarks`.

### Step 6: Run the Material Checker

Run:

```bash
bash "$checker" --body "$body_file" "$doc_file"
```

Fix every failure, then re-run. This check is required before showing the body to the user, before committing the docs repo, and before creating the PR.

### Step 7: Confirm With the User

Show the draft title, base branch, head branch, doc URL, and PR body. Ask for confirmation before publishing.

### Step 8: Commit and Push the Docs Repo

After the checker passes and the user confirms:

```bash
git -C "$docs_repo" add "cbrd-XXXXX/"
git -C "$docs_repo" commit -m "docs(CBRD-XXXXX): add PR explanation for <slug>"
git -C "$docs_repo" push origin main
```

After pushing, use the published GitHub URL in the PR body's `## Remarks` section.

### Step 9: Push the Branch and Create the PR

1. Push the branch to the user's fork:
   ```bash
   git push <fork-remote> <branch> -u
   ```
2. Re-run the checker:
   ```bash
   bash "$checker" --body "$body_file" "$doc_file"
   ```
3. Create the PR:
   ```bash
   gh pr create --repo CUBRID/CUBRID \
     --draft \
     --base <base-branch> \
     --head <user>:<branch> \
     --assignee vimkim \
     --title "[CBRD-XXXXX] Title" \
     --body-file "$body_file"
   ```
4. Print the resulting PR URL.

## Example Output

```text
Doc pushed: https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-26583/CBRD-26583-reenable-oos-oid-replacement.md
PR created: https://github.com/CUBRID/cubrid/pull/6950

Title: [CBRD-26583] Re-enable OOS OID replacement in heap records
Base:  feat/oos
Head:  vimkim:feat/oos-replace-oos-oid
```

## Tips

- If the branch has already been pushed, skip the branch push step.
- If a PR already exists for the branch, show it instead of creating a duplicate. If the doc has changed, still update the docs repo and PR body link.
- For multi-commit PRs, summarize the overall change rather than listing each commit message.
- Use `--body-file "$body_file"` for multi-line Korean text.
- The one-screen rule is a hard limit. When in doubt, cut a sentence from the body and add it to the doc.

## Mandatory: Iterate with Grill-with-Docs

The detailed explanation doc must go through `/grill-with-docs` before the docs repo is committed and pushed. Do not push a single-pass doc.

This applies to every PR. The only legitimate skip is when the user explicitly says `skip grill`, `do not grill this`, `no grill`, or an unambiguous equivalent in the message that triggered this skill.

Hand off with:

1. Topic and purpose: PR title, JIRA ticket, and target reviewers.
2. Output path: the `doc_file`; the loop revises it in place.
3. Source material: the diff, JIRA output, related issues, and related PRs.
4. Review angle: completeness and correctness of `## Purpose`, `## Implementation`, and `## Remarks`; explicit AS-IS/TO-BE contrast when the change supports it; CUBRID doc conventions; every CUBRID-internal term glossed on first use.
5. Round cap: default 5.

After approval, run the material checker, draft the PR body, confirm with the user, publish the docs repo, and create the PR.
