#!/usr/bin/env bash
# Publish a completed CUBRID PR review report and post its three-line summary.

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  shift
fi

PR_INPUT="${1:-}"
REPORT_INPUT="${2:-}"
DOCS_ROOT="${CUBRID_PR_DOCS_REPO:-/home/vimkim/gh/my-cubrid-docs}"

fail()
{
  echo "FAIL: $*" >&2
  exit 1
}

if [[ -z "$PR_INPUT" || -z "$REPORT_INPUT" || $# -ne 2 ]]; then
  fail "Usage: publish-review.sh [--dry-run] <PR number or canonical URL> <report path>"
fi

if [[ "$PR_INPUT" =~ ^[0-9]+$ ]]; then
  PR_NUMBER="$PR_INPUT"
  PR_URL="https://github.com/CUBRID/cubrid/pull/$PR_NUMBER"
elif [[ "$PR_INPUT" =~ ^https://github\.com/CUBRID/cubrid/pull/([0-9]+)$ ]]; then
  PR_NUMBER="${BASH_REMATCH[1]}"
  PR_URL="$PR_INPUT"
else
  fail "PR must be a number or canonical https://github.com/CUBRID/cubrid/pull/<number> URL"
fi

[[ -d "$DOCS_ROOT" ]] || fail "Docs repository not found: $DOCS_ROOT"
[[ -f "$REPORT_INPUT" ]] || fail "Review report not found: $REPORT_INPUT"

DOCS_ROOT="$(realpath "$DOCS_ROOT")"
REPORT_PATH="$(realpath "$REPORT_INPUT")"
case "$REPORT_PATH" in
  "$DOCS_ROOT"/*) ;;
  *) fail "Review report must be inside $DOCS_ROOT" ;;
esac
REPORT_RELATIVE="${REPORT_PATH#"$DOCS_ROOT"/}"

REPO_ROOT="$(git -C "$DOCS_ROOT" rev-parse --show-toplevel 2>/dev/null)" \
  || fail "Docs path is not a Git worktree: $DOCS_ROOT"
[[ "$(realpath "$REPO_ROOT")" == "$DOCS_ROOT" ]] \
  || fail "Docs path must be the Git worktree root: $DOCS_ROOT"

ORIGIN_URL="$(git -C "$DOCS_ROOT" config --get remote.origin.url 2>/dev/null)" \
  || fail "Docs repository has no origin remote"
case "$ORIGIN_URL" in
  https://github.com/vimkim/my-cubrid-docs|https://github.com/vimkim/my-cubrid-docs.git|git@github.com:vimkim/my-cubrid-docs|git@github.com:vimkim/my-cubrid-docs.git) ;;
  *) fail "Unexpected docs origin: $ORIGIN_URL" ;;
esac

FINDINGS_HEADER_COUNT="$(grep -c '^## Findings$' "$REPORT_PATH" || true)"
[[ "$FINDINGS_HEADER_COUNT" -eq 1 ]] \
  || fail "Review report must contain exactly one '## Findings' section"

read -r \
  BLOCKING_COUNT NON_BLOCKING_COUNT QUESTION_COUNT \
  BLOCKING_HEADER_COUNT NON_BLOCKING_HEADER_COUNT QUESTION_HEADER_COUNT \
  NONE_COUNT UNSECTIONED_COUNT UNKNOWN_HEADER_COUNT < <(
  awk '
    /^## Findings$/ { in_findings = 1; next }
    in_findings && /^## / { in_findings = 0; section = "" }
    !in_findings { next }
    /^### Blocking \(must fix\)$/ {
      blocking_headers++; section = "blocking"; next
    }
    /^### Non-blocking \(should consider\)$/ {
      non_blocking_headers++; section = "non-blocking"; next
    }
    /^### Questions for the author$/ {
      question_headers++; section = "questions"; next
    }
    /^### / { unknown_headers++; section = "unknown"; next }
    section == "blocking" && /^- / { blocking++; next }
    section == "non-blocking" && /^- / { non_blocking++; next }
    section == "questions" && /^- / { questions++; next }
    section == "" && NF {
      if ($0 == "없음") none++
      else unsectioned++
    }
    END {
      print blocking + 0, non_blocking + 0, questions + 0,
            blocking_headers + 0, non_blocking_headers + 0,
            question_headers + 0, none + 0, unsectioned + 0,
            unknown_headers + 0
    }
  ' "$REPORT_PATH"
)

[[ "$BLOCKING_HEADER_COUNT" -le 1 \
   && "$NON_BLOCKING_HEADER_COUNT" -le 1 \
   && "$QUESTION_HEADER_COUNT" -le 1 \
   && "$UNKNOWN_HEADER_COUNT" -eq 0 ]] \
  || fail "Review report contains duplicate or unknown Finding subsections"
[[ ( "$BLOCKING_HEADER_COUNT" -eq 0 && "$BLOCKING_COUNT" -eq 0 ) \
   || ( "$BLOCKING_HEADER_COUNT" -eq 1 && "$BLOCKING_COUNT" -gt 0 ) ]] \
  || fail "Blocking subsection must contain at least one review point"
[[ ( "$NON_BLOCKING_HEADER_COUNT" -eq 0 && "$NON_BLOCKING_COUNT" -eq 0 ) \
   || ( "$NON_BLOCKING_HEADER_COUNT" -eq 1 && "$NON_BLOCKING_COUNT" -gt 0 ) ]] \
  || fail "Non-blocking subsection must contain at least one review point"
[[ ( "$QUESTION_HEADER_COUNT" -eq 0 && "$QUESTION_COUNT" -eq 0 ) \
   || ( "$QUESTION_HEADER_COUNT" -eq 1 && "$QUESTION_COUNT" -gt 0 ) ]] \
  || fail "Questions subsection must contain at least one question"

TOTAL_SUBSECTION_COUNT=$((
  BLOCKING_HEADER_COUNT + NON_BLOCKING_HEADER_COUNT + QUESTION_HEADER_COUNT
))
if [[ "$TOTAL_SUBSECTION_COUNT" -eq 0 ]]; then
  [[ "$NONE_COUNT" -eq 1 && "$UNSECTIONED_COUNT" -eq 0 ]] \
    || fail "A report without Finding subsections must contain only '없음'"
else
  [[ "$NONE_COUNT" -eq 0 && "$UNSECTIONED_COUNT" -eq 0 ]] \
    || fail "Finding points must be placed under the required subsections"
fi

if (( BLOCKING_COUNT > 0 )); then
  DECISION="REJECT"
else
  DECISION="ACCEPT"
fi

REPORT_URL="https://github.com/vimkim/my-cubrid-docs/blob/main/$REPORT_RELATIVE"
printf -v COMMENT_BODY \
  'Report: %s\nReview points: %d blocking, %d non-blocking\nDecision: %s' \
  "$REPORT_URL" "$BLOCKING_COUNT" "$NON_BLOCKING_COUNT" "$DECISION"

LINE_COUNT="$(awk 'END { print NR }' <<< "$COMMENT_BODY")"
[[ "$LINE_COUNT" -eq 3 ]] || fail "Internal error: summary comment is not exactly three lines"

if [[ "$DRY_RUN" == true ]]; then
  printf '%s\n' "$COMMENT_BODY"
  exit 0
fi

CURRENT_BRANCH="$(git -C "$DOCS_ROOT" symbolic-ref --quiet --short HEAD)" \
  || fail "Docs repository is in detached HEAD state"
[[ "$CURRENT_BRANCH" == "main" ]] || fail "Docs repository must be on main, found: $CURRENT_BRANCH"

git -C "$DOCS_ROOT" fetch origin main
LOCAL_HEAD="$(git -C "$DOCS_ROOT" rev-parse HEAD)"
REMOTE_HEAD="$(git -C "$DOCS_ROOT" rev-parse origin/main)"
NEEDS_PUSH=false

if [[ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]]; then
  git -C "$DOCS_ROOT" merge-base --is-ancestor origin/main HEAD \
    || fail "Docs main has diverged from origin/main"
  AHEAD_COUNT="$(git -C "$DOCS_ROOT" rev-list --count origin/main..HEAD)"
  [[ "$AHEAD_COUNT" -eq 1 ]] \
    || fail "Docs main has unpushed commits unrelated to this publication"
  mapfile -t UNPUSHED_PATHS < <(
    git -C "$DOCS_ROOT" diff-tree --no-commit-id --name-only -r HEAD
  )
  [[ "${#UNPUSHED_PATHS[@]}" -eq 1 && "${UNPUSHED_PATHS[0]}" == "$REPORT_RELATIVE" ]] \
    || fail "The unpushed docs commit is not limited to this review report"
  git -C "$DOCS_ROOT" diff --quiet HEAD -- "$REPORT_RELATIVE" \
    || fail "Review report changed after its unpushed commit"
  git -C "$DOCS_ROOT" diff --cached --quiet HEAD -- "$REPORT_RELATIVE" \
    || fail "Review report index differs from its unpushed commit"
  NEEDS_PUSH=true
else
  git -C "$DOCS_ROOT" add -- "$REPORT_RELATIVE"
  if ! git -C "$DOCS_ROOT" diff --cached --quiet -- "$REPORT_RELATIVE"; then
    git -C "$DOCS_ROOT" commit --only \
      -m "docs: add PR #$PR_NUMBER review report" -- "$REPORT_RELATIVE"
    NEEDS_PUSH=true
  fi
fi

if [[ "$NEEDS_PUSH" == true ]]; then
  git -C "$DOCS_ROOT" push origin HEAD:main
fi

git -C "$DOCS_ROOT" diff --quiet -- "$REPORT_RELATIVE" \
  || fail "Report changed while it was being published"
git -C "$DOCS_ROOT" diff --cached --quiet -- "$REPORT_RELATIVE" \
  || fail "Published report remains staged unexpectedly"

gh pr comment "$PR_URL" --body "$COMMENT_BODY"

printf 'Report path: %s\n' "$REPORT_PATH"
printf 'Report URL: %s\n' "$REPORT_URL"
printf 'Review points: %d blocking, %d non-blocking\n' "$BLOCKING_COUNT" "$NON_BLOCKING_COUNT"
printf 'Decision: %s\n' "$DECISION"
