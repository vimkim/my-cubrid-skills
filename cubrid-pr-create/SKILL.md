---
name: cubrid-pr-create
description: Prepare a CUBRID PR body as persistent Markdown in my-cubrid-docs for human review, then create a draft PR or update an existing description after explicit confirmation. Use for creating, drafting, publishing, or revising CUBRID PR descriptions, including resuming a saved draft.
---

# CUBRID PR Creator

Use one skill in two phases: prepare reviewable files, then publish the reviewed
material after confirmation. A **PR body draft** is saved text; a **draft PR** is
an actual pull request on GitHub.

## Review and Publication Contract

- A request to create or update a PR starts preparation. Save the proposed body in
  `my-cubrid-docs` and present its location and intended publication operations.
  Preparation ends with the files ready for human review, without remote writes.
- Publication requires the user's explicit confirmation after the draft is
  available. One confirmation covers the exact listed operations, including any
  necessary docs integration/push and source push. Skill invocation, saved context,
  or an approval flag in a file does not establish permission.
- A **standing instruction** replaces per-draft review when the user says they are
  going to sleep or tells you to keep going. It confirms the PR operations it names
  or the task in progress already includes, within the limits it states, such as
  one draft PR per hour. Quote the user's words and when they said them in the draft
  context. Run every publication check as usual. When a check fails or a change would
  return material to review, skip the remaining writes of that publication, including
  its source push, and record the reason for the user.
- When the user edits the draft and says to publish, reread and validate its current
  contents, then upload them unchanged. An agent rewrite requires another review.
  Explain validation failures instead of silently repairing approved material.
- New PRs are created in draft status. Existing PRs receive a body update by default;
  change the title only if that change was presented and approved. Preserve their
  draft/ready status. A description-only update does not authorize a source push.
- A source revision change or an edit to the existing GitHub description requires
  reconciliation and another review. A changed destination or expanded operation
  list also returns to review. Unchanged retries retain the existing authorization.

## Route the Request

- For preparation or revision, follow the steps below.
- For confirmed publication of a saved draft, load its context and read
  [Publish reviewed material](references/publish.md). If the conversation does not
  establish confirmation of those files and operations, present them for review.
- Use a supplied PR URL/number to identify updates. Otherwise discover an open PR
  matching the exact target repository, head repository/branch, and base. Reuse that
  PR rather than creating a duplicate; ask if the intended PR is ambiguous.

Examples: `/cubrid-pr-create CBRD-26583`, a request to revise PR #1234, or
“publish the saved draft for CBRD-26583.” Extract a required ticket from the request,
branch, or existing PR; ask if it cannot be determined.

## Prepare the Review

### 1. Establish the Source and Target

Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy), its applicable user context, and the applicable repository instructions.
Inspect source status, branch/tracking information, and remote URLs. Preserve
unrelated changes; clarify whether relevant uncommitted work belongs in the PR
instead of committing it implicitly.

Resolve the target repository (normally `CUBRID/CUBRID`), source repository and
branch, and base. For an existing PR, read its actual metadata and body. For a new
PR, prefer the user's explicit base and current project integration guidance;
otherwise use `develop` for ordinary `CBRD-*` branches, `cubvec/cubvec` for
`cubvec/*`, or ask when unclear. Inspect live branches instead of assuming a
historical OOS integration branch still applies. Select source push routing using
`CUBRID.md`; the usual personal fork is `github.com/vimkim/cubrid`. Routing is not
publication permission.

Set `SOURCE_COMMIT` to the full hexadecimal source commit from
`git rev-parse --verify 'HEAD^{commit}'`.
For an update, compare it with the remote PR head and resolve discrepancies before
writing: the draft must explain the revision intended for publication. Record the
observed remote head commit, or that the branch does not yet exist for a new PR.

Fetch the base, inspect the commits and full diff, and consult `cubrid-jira` for
issue context. Summarize the whole change, not each commit separately. For an
existing PR, start from its current GitHub body and preserve manual content unless
the requested revision changes it. Retain its original body fingerprint for the
publication freshness check.

### 2. Save Persistent Files

Resolve the docs repository from `${CUBRID_PR_DOCS_REPO:-$HOME/gh/my-cubrid-docs}`.
Require a Git worktree whose `origin` fetch and push URLs resolve to
`github.com/vimkim/my-cubrid-docs` (SSH or HTTPS). Resolve canonical source and docs
paths; keep all draft files outside the CUBRID source worktree.

Follow [Document Git workflow](../cubrid-common/references/document-git-workflow.md)
to select `ARTIFACT_WORKTREE`, name the files, and prepare a local task commit.
Apply the destination's important-document rule to README indexes. Local task
commits remain separate from remote publication under the contract above.

Reuse the existing ticket directory spelling, or use `cbrd-XXXXX/` for a new
directory. Apply the shared naming rules. For a new draft:

| Artifact | Filename inside `cbrd-XXXXX/` |
| --- | --- |
| Required PR body | `pr-body.md` |
| Required draft context | `pr-context.md` |
| Optional detailed explanation | A short descriptive name such as `design.md` |

Set `body_file` and `context_file` to these saved files. Set `doc_file` only when
an explanation is warranted. The body file contains exactly the text to upload:
no frontmatter, proposed title, approval notes, or publication checklist.

Inspect matching drafts before writing. Resume the selected draft and preserve
user edits; create a distinct revision if a new draft would overwrite unrelated or
previously reviewed material. When the source revision changes, retain the old
files, reconcile their content, and prepare a distinct revision with its full source
commit recorded in the context. Use a short discriminator only when needed.

Create a detailed explanation only when technical context exceeds the short body's
scope. Use English `## Purpose`, `## Implementation`, and `## Remarks` headings with
Korean prose in the explanation; place structured test details under `### Test Plan`
in Remarks.
Choose its final public URL before review, normally
`https://github.com/vimkim/my-cubrid-docs/blob/main/cbrd-XXXXX/<filename>`.
A new explanation linked by the body must be published before the PR write.

### 3. Record Draft Context

Keep resume metadata in `context_file`, separate from the uploaded body:

- Ticket, full `SOURCE_COMMIT`, source repository/branch, base, and
  observed remote head commit or absence.
- Target repository, operation (`create` or `update`), and existing PR URL/number.
- Proposed title for creation; existing title and optional proposed replacement for
  updates. Record the existing PR's open/closed and draft/ready state.
- For updates, a SHA-256 fingerprint of the original GitHub body. Use the same
  decoded UTF-8 bytes for every comparison, with no added newline; for example,
  hash the `body` string from `gh pr view ... --json body` after JSON decoding.
- Docs task branch, integration branch, and repo-relative body/context/detail paths.
  Include any public explanation URL. Rediscover worktree locations with Git when
  resuming. Resolve the recorded paths directly, including for older drafts; never
  infer companion paths from SHA/agent suffixes. Keep machine-local paths out of
  tracked context.
- Exact proposed operations and destinations: docs commits to integrate/push (and
  files included), source push if needed, new draft PR creation or existing body
  update, and title change only when proposed. Include docs rebase/fast-forward
  merge, including final execution-record commits, if required by the local workflow.
  For creation, include the default `vimkim` assignment in the proposal.

The context is a proposal, not a durable approval token. When confirmed publication
begins, record the body/explanation fingerprints for that attempt. Record operation
results as they are verified, so a later session can distinguish an interrupted
attempt from a new revision. Establish authorization from the conversation.

### 4. Validate and Hand Back for Review

Review saved material against the diff, issue, and related context. Claims and
verification outcomes must match evidence; include limits and follow-up when
relevant. Resolve unknown intended behavior before proposing unsupported claims.
Use an independent reviewer only when the user requests one.

Optional static evidence: when `cubrid-static-check` is on `PATH`, run
`cubrid-static-check <base> "$SOURCE_COMMIT"` from the source worktree. It reports
only what the change adds: cppcheck and clang-tidy findings, new clones, and
functions whose complexity grew. Check each reported item against the code, and
present every real defect to the user with the review handoff; fixing source is
outside this skill. Record the summary table and your dispositions in
`context_file`. The PR body keeps describing verification with public project tools.

Run the material checker below and correct preparation defects. If a correction
changes text after the user has reviewed it, return that revision for review.
Commit only the intended files locally when required by the worktree workflow.

Show clickable local links to the body, context, and any explanation; identify the
source commit, target PR or branches, proposed title, and the exact publication
operations. Explain that the user can edit the body file directly. Ask for review
and explicit publication confirmation, then **end preparation here**. Keep the
docs task worktree available for review. Read the publication reference only when
continuing after confirmation.

## Writing Conventions

Apply [Links in shared material](../cubrid-common/references/shared-links.md) to
the body and any explanation. Use verified URLs accessible to the intended readers;
personal viewing links belong only in the chat handoff.

During preparation, use `$asd-ste100` if available for English titles and
explanatory prose. Use its STE-flavored mode. Preserve required headings,
identifiers, quotations, uncertainty, and the required Korean prose.

Titles use `[CBRD-XXXXX] Short English description`, with an imperative verb such
as `Fix`, `Add`, or `Refactor` and fewer than 60 characters after the ticket tag.

For updates, preserve the existing structure and manual content. A new body starts
with the JIRA URL and uses exactly these `##` sections in order:

```markdown
https://jira.cubrid.org/browse/CBRD-XXXXX

## Purpose

- 이 변경이 필요한 이유를 짧게 설명합니다.
- AS-IS: 현재 동작이나 한계를 한 문장으로 설명합니다.
- TO-BE: 변경 후 동작을 한 문장으로 설명합니다.

## Implementation

- 실제로 바꾼 내용을 설명합니다.

## Remarks

- 검증 결과, 리뷰할 부분, 제한 사항을 적습니다.
```

- Keep the whole body to one screen, roughly 25–35 lines or fewer for small changes.
  For new bodies, keep all three sections even for trivial fixes; use `### Test Plan` under Remarks
  if needed rather than a fourth `##` section.
- Use short, plain Korean sentences understandable by an 11th-grade Korean reader
  without CUBRID-internal knowledge. Gloss unfamiliar database terms once. Keep
  code identifiers and repo-relative paths in English code style.
- Use explicit `AS-IS:` and `TO-BE:` under Purpose when the change has a meaningful
  before/after contrast. Omit them for pure cleanup with no such contrast. Use the
  same contrast under Purpose in an explanation if one is written.
- When an explanation is included, link its public URL once, normally as the final
  Remarks bullet. Otherwise omit the link. The body must stand alone either way.
- Put deep technical detail in the optional explanation. Express verification
  with public project scripts, CMake/ctest, or outcomes, not personal `just` recipes.
- PR bodies and explanations contain repo-relative paths or public URLs, never
  local absolute paths, `file://` URLs, or machine-specific workspace paths.

## Material Checker

Resolve `checker` to this skill's `scripts/check-pr-material.sh`. It checks the
new body's three-section contract and all files for known local-path/task-runner
patterns. It does not establish factual accuracy, review approval, or source/PR freshness. It also
runs the shared Python link checker on every supplied file; passing the known-host
check does not establish access to other URLs.

Run it before the review handoff, before committing body/explanation changes, and
immediately before creating or updating a PR. Set `operation` from the recorded
create/update operation. Use the flag for updates, including retries, and keep the
default for new drafts:

```bash
material_files=("$body_file")
if [[ -n "${doc_file:-}" ]]; then
  material_files+=("$doc_file")
fi
checker_args=()
if [[ "$operation" == "update" ]]; then
  checker_args+=(--existing-body)
fi
bash "$checker" "${checker_args[@]}" --body "${material_files[@]}"
```

Check publication material only; the companion context is not the PR body. During
confirmed publication, validation is read-only. Report failures and return any
needed text changes to review instead of rewriting the approved files.
