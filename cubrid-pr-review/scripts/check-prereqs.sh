#!/usr/bin/env bash
# check-prereqs.sh — Validate the current CUBRID worktree and fetch PR metadata
#
# On success: prints JSON metadata to stdout
# On failure: prints error to stderr and exits non-zero

set -euo pipefail

PR_INPUT="${1:-}"

if [[ -z "$PR_INPUT" ]]; then
  echo "FAIL: No PR number or URL provided." >&2
  echo "Usage: cubrid-pr-review 6930" >&2
  echo "   or: cubrid-pr-review https://github.com/CUBRID/cubrid/pull/6930" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || [[ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]]; then
  echo "FAIL: cubrid-pr-review must run inside a Git worktree." >&2
  exit 1
fi

if [[ "$PR_INPUT" =~ ^[0-9]+$ ]]; then
  PR_NUMBER="$PR_INPUT"
elif [[ "$PR_INPUT" =~ ^https://github\.com/CUBRID/cubrid/pull/([0-9]+)/?$ ]]; then
  PR_NUMBER="${BASH_REMATCH[1]}"
else
  echo "FAIL: Expected a CUBRID PR number or canonical CUBRID PR URL: $PR_INPUT" >&2
  echo "Examples: 6930 or https://github.com/CUBRID/cubrid/pull/6930" >&2
  exit 1
fi

OWNER="CUBRID"
REPO="cubrid"

PR_JSON=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER" 2>&1) || {
  echo "FAIL: Could not fetch PR #$PR_NUMBER from $OWNER/$REPO" >&2
  echo "$PR_JSON" >&2
  exit 1
}

BASE_REPO=$(jq -r '.base.repo.full_name // empty' <<<"$PR_JSON")
if [[ "$BASE_REPO" != "CUBRID/cubrid" ]]; then
  echo "FAIL: PR #$PR_NUMBER does not target CUBRID/cubrid." >&2
  exit 1
fi

LOCAL_HEAD=$(git rev-parse HEAD)
REPO_ROOT=$(git rev-parse --show-toplevel)
PR_HEAD=$(jq -r '.head.sha // empty' <<<"$PR_JSON")
if [[ -z "$PR_HEAD" ]]; then
  echo "FAIL: PR #$PR_NUMBER metadata does not contain a head SHA." >&2
  exit 1
fi

if [[ "$LOCAL_HEAD" != "$PR_HEAD" ]]; then
  echo "FAIL: Current worktree HEAD does not match CUBRID/cubrid PR #$PR_NUMBER." >&2
  echo "Current HEAD: $LOCAL_HEAD" >&2
  echo "PR HEAD:      $PR_HEAD" >&2
  echo "Check out the PR head in this worktree, then rerun cubrid-pr-review." >&2
  exit 1
fi

echo "$PR_JSON" | jq --arg repo_root "$REPO_ROOT" --arg local_head "$LOCAL_HEAD" '{
  status: "OK",
  owner: .base.repo.owner.login,
  repo: .base.repo.name,
  number: .number,
  pr_url: .html_url,
  repo_root: $repo_root,
  local_head: $local_head,
  head_sha: .head.sha,
  head_ref: .head.ref,
  base_ref: .base.ref,
  state: .state,
  title: .title,
  draft: .draft,
  author: .user.login,
  body: (.body // "")
}'
