#!/usr/bin/env bash
# check-prereqs.sh - Validate the current CUBRID worktree and fetch PR metadata.
#
# On success: prints JSON metadata to stdout.
# On failure: prints error to stderr and exits non-zero.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../cubrid-common/scripts/cubrid-common.sh"
PR_INPUT="${1:-}"

if [[ -z "$PR_INPUT" ]]; then
  echo "FAIL: No PR number or URL provided." >&2
  echo "Usage: cubrid-pr-review 6930" >&2
  echo "   or: cubrid-pr-review https://github.com/CUBRID/cubrid/pull/6930" >&2
  exit 1
fi

if [[ ! -f "$COMMON" ]]; then
  echo "FAIL: shared CUBRID helpers not found: $COMMON" >&2
  echo "Install the full my-cubrid-skills collection so cubrid-common is present." >&2
  exit 1
fi

# shellcheck source=../../cubrid-common/scripts/cubrid-common.sh
source "$COMMON"

cubrid_pr_review_metadata "$PR_INPUT"
