---
name: cubrid-review-intake
description: "Start assigned CUBRID PR reviews with cubrid-review-flow: list pending review requests, stage a local diff, brief, and review worktree, hand off defect inspection to cubrid-code-review, and clean up finished review worktrees. Post nothing to GitHub without explicit user approval. Use when starting assigned PR reviews, preparing a review draft, or cleaning up finished review worktrees. Triggers on phrases like 'start my PR reviews', 'what reviews are assigned to me', 'prepare review for PR 1234', 'clean up review worktree', '리뷰 요청 온 PR 시작', '리뷰 워크트리 정리'."
argument-hint: "[PR number or status|cleanup]"
---

# CUBRID Review Intake

Take assigned CUBRID pull request reviews from request to cleanup. `cubrid-review-flow` finds the requests and stages the local material. [`cubrid-code-review`](../cubrid-code-review/SKILL.md) inspects the code. You post to GitHub only after the user approves.

Take a PR number, `status`, or `cleanup` from `$ARGUMENTS`. If there is no argument, start at step 2.

## 1. Preflight

```bash
command -v cubrid-review-flow gh
cubrid-review-flow --help
```

If `cubrid-review-flow` is missing, stop. Tell the user to run `just sync` in `~/gh/my-cubrid-workflow/automations/cubrid-review-flow`. Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy) before you decide whose review a request is.

## 2. List the review queue

```bash
cubrid-review-flow status --json
cubrid-review-flow tick --dry-run --json
```

`status` shows the open review requests and their local state (not staged, staged, reviewed, posted, or ready for cleanup). `tick --dry-run` shows the actions that the next automatic tick would take. It changes nothing. Show the user each PR: repository, number, title, author, requested-at time, local state, and planned action. Ask which PR to start if the user did not name one.

## 3. Prepare one PR

```bash
cubrid-review-flow prepare --pr <N> --json
cubrid-review-flow prepare --pr <N> --repo CUBRID/<repo> --json
```

Add `--repo` for a repository other than the tool's default (`CUBRID/cubrid`). The command creates or reuses a review worktree (through `cubrid-worktree`) and writes the diff and a review brief. Record the worktree path, the base and head SHAs, and the brief and diff paths from the output. If the head SHA changes later, run `prepare` again before you review.

## 4. Inspect the code

Run [`cubrid-code-review`](../cubrid-code-review/SKILL.md) on the prepared PR. Give it the worktree, the base and head SHAs, and the brief. Do not do a separate defect review in this skill.

The `cubrid-code-review` steps that publish or post (the report push to my-cubrid-docs and the GitHub summary) are subject to step 5.

## 5. Get approval before you post (Tier 2)

A GitHub review, review comment, PR comment, approval, or request for changes is an external post. Before you post:

1. Show the user the exact text, the event type (`COMMENT`, `APPROVE`, or `REQUEST_CHANGES`), each inline comment with its path and line, and the report link.
2. Post only after the user approves this content in this session. If the user changes the content, show it again before you post.
3. Post through the method that `cubrid-code-review` or `cubrid-review-flow` documents. Do not post again on retry if the first post succeeded.

If the user does not approve, keep the draft locally and report its path.

## 6. Clean up

When the review is posted, or the user drops it:

```bash
cubrid-review-flow cleanup --pr <N> --json
cubrid-review-flow cleanup --pr <N> --apply --json
```

Run the first command to preview. Apply only when the preview shows no local changes, no unpushed commits, and no unposted draft that the user wants to keep. Otherwise show the blocker and ask the user. Run `cubrid-review-flow status --json` again to confirm.

## 7. Report

Report the following:

- The PR.
- The worktree, brief, and report paths.
- The review verdict.
- What you posted, with links, or that you posted nothing.
- The cleanup result.
- The next PR in the queue.
