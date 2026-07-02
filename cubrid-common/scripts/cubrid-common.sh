#!/usr/bin/env bash
# Shared shell helpers for CUBRID skills.
# Source this file from skill-specific scripts; do not execute it directly.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "FAIL: cubrid-common.sh must be sourced, not executed." >&2
  exit 2
fi

cubrid_common_fail() {
  echo "FAIL: $*" >&2
}

cubrid_common_note() {
  echo "$*" >&2
}

cubrid_require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    cubrid_common_fail "Required command not found: $cmd"
    return 1
  fi
}

cubrid_is_git_worktree() {
  local dir="${1:-$PWD}"
  local inside

  inside=$(git -C "$dir" rev-parse --is-inside-work-tree 2>/dev/null) \
    && [[ "$inside" == "true" ]]
}

cubrid_require_git_worktree() {
  local dir="${1:-$PWD}"

  if ! cubrid_is_git_worktree "$dir"; then
    cubrid_common_fail "Must run inside a Git worktree: $dir"
    return 1
  fi
}

cubrid_git_root() {
  local dir="${1:-$PWD}"
  git -C "$dir" rev-parse --show-toplevel
}

cubrid_is_source_tree() {
  local dir="${1:-$PWD}"
  [[ -f "$dir/CMakeLists.txt" ]] \
    && grep -qE '^[[:space:]]*project[[:space:]]*\([[:space:]]*CUBRID([[:space:]\)]|$)' "$dir/CMakeLists.txt"
}

cubrid_require_source_tree() {
  local dir="${1:-$PWD}"

  if [[ ! -f "$dir/CMakeLists.txt" ]]; then
    cubrid_common_fail "Not a CUBRID source checkout: CMakeLists.txt is missing in $dir"
    return 1
  fi

  if ! cubrid_is_source_tree "$dir"; then
    cubrid_common_fail "Not a CUBRID source checkout: CMakeLists.txt does not declare project(CUBRID)."
    return 1
  fi
}

cubrid_find_build_dir() {
  local dir="${1:-$PWD}"

  if [[ -n "${PRESET_MODE:-}" && -d "$dir/build_preset_${PRESET_MODE}" ]]; then
    printf '%s\n' "$dir/build_preset_${PRESET_MODE}"
    return 0
  fi

  find "$dir" -maxdepth 1 -type d -name 'build_preset_*' 2>/dev/null | sort | head -1
}

cubrid_list_cmake_presets() {
  local dir="${1:-$PWD}"

  if command -v cmake >/dev/null 2>&1 && [[ -f "$dir/CMakePresets.json" ]]; then
    (cd "$dir" && cmake --list-presets 2>/dev/null) || true
  fi
}

cubrid_preset_mode_is_valid() {
  local dir="${1:-$PWD}"

  [[ -n "${PRESET_MODE:-}" ]] || return 1
  [[ -f "$dir/CMakePresets.json" ]] || return 1
  command -v cmake >/dev/null 2>&1 || return 1

  (cd "$dir" && cmake --list-presets 2>/dev/null \
    | awk -F'"' '/"/ { print $2 }' \
    | grep -qx "$PRESET_MODE")
}

cubrid_require_valid_preset_mode() {
  local dir="${1:-$PWD}"

  if [[ -z "${PRESET_MODE:-}" ]]; then
    cubrid_common_fail "PRESET_MODE is not set. just build requires a CMake preset."
    cubrid_common_note "Available presets in this worktree:"
    cubrid_list_cmake_presets "$dir"
    cubrid_common_note "Set PRESET_MODE to one of the listed presets and re-run."
    return 1
  fi

  if [[ ! -f "$dir/CMakePresets.json" ]]; then
    cubrid_common_fail "CMakePresets.json is missing in $dir."
    return 1
  fi

  if ! command -v cmake >/dev/null 2>&1; then
    cubrid_common_fail "cmake is not available; cannot validate PRESET_MODE=$PRESET_MODE."
    return 1
  fi

  if ! cubrid_preset_mode_is_valid "$dir"; then
    cubrid_common_fail "PRESET_MODE=$PRESET_MODE is not a valid CMake preset for this worktree."
    cubrid_common_note "Available presets:"
    cubrid_list_cmake_presets "$dir"
    cubrid_common_note "Set PRESET_MODE to a valid preset and re-run."
    return 1
  fi
}

cubrid_require_just_build_recipe() {
  local dir="${1:-$PWD}"

  cubrid_require_command just || return 1
  if ! (cd "$dir" && just --list 2>/dev/null | grep -qE '^[[:space:]]*build([[:space:]]|$)'); then
    cubrid_common_fail "No just build recipe found in this checkout."
    return 1
  fi
}

cubrid_parse_pr_number() {
  local pr_input="$1"

  if [[ "$pr_input" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$pr_input"
  elif [[ "$pr_input" =~ ^https://github\.com/CUBRID/cubrid/pull/([0-9]+)/?$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
  else
    cubrid_common_fail "Expected a CUBRID PR number or canonical CUBRID PR URL: $pr_input"
    cubrid_common_note "Examples: 6930 or https://github.com/CUBRID/cubrid/pull/6930"
    return 1
  fi
}

cubrid_fetch_pr_json() {
  local pr_number="$1"
  local owner="${2:-CUBRID}"
  local repo="${3:-cubrid}"
  local pr_json

  if ! pr_json=$(gh api "repos/$owner/$repo/pulls/$pr_number" 2>&1); then
    cubrid_common_fail "Could not fetch PR #$pr_number from $owner/$repo"
    echo "$pr_json" >&2
    return 1
  fi

  printf '%s\n' "$pr_json"
}

cubrid_pr_review_metadata() {
  local pr_input="$1"
  local pr_number pr_json base_repo local_head repo_root pr_head

  cubrid_require_git_worktree "$PWD" || return 1
  cubrid_require_command gh || return 1
  cubrid_require_command jq || return 1

  pr_number=$(cubrid_parse_pr_number "$pr_input") || return 1
  pr_json=$(cubrid_fetch_pr_json "$pr_number" CUBRID cubrid) || return 1

  base_repo=$(jq -r '.base.repo.full_name // empty' <<<"$pr_json")
  if [[ "$base_repo" != "CUBRID/cubrid" ]]; then
    cubrid_common_fail "PR #$pr_number does not target CUBRID/cubrid."
    return 1
  fi

  local_head=$(git rev-parse HEAD)
  repo_root=$(git rev-parse --show-toplevel)
  pr_head=$(jq -r '.head.sha // empty' <<<"$pr_json")
  if [[ -z "$pr_head" ]]; then
    cubrid_common_fail "PR #$pr_number metadata does not contain a head SHA."
    return 1
  fi

  if [[ "$local_head" != "$pr_head" ]]; then
    cubrid_common_fail "Current worktree HEAD does not match CUBRID/cubrid PR #$pr_number."
    echo "Current HEAD: $local_head" >&2
    echo "PR HEAD:      $pr_head" >&2
    echo "Check out the PR head in this worktree, then rerun cubrid-pr-review." >&2
    return 1
  fi

  jq --arg repo_root "$repo_root" --arg local_head "$local_head" '{
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
  }' <<<"$pr_json"
}

cubrid_detect_remote() {
  local upstream
  upstream=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null) || upstream=""
  if [[ -n "$upstream" ]]; then
    local up_remote="${upstream%%/*}"
    local up_url
    up_url=$(git remote get-url "$up_remote" 2>/dev/null) || up_url=""
    if [[ -n "$up_url" ]] && printf '%s' "$up_url" \
        | grep -qiE 'github\.com[:/]cubrid/cubrid(\.git)?$'; then
      echo "Detected CUBRID remote via branch upstream: $up_remote ($up_url)" >&2
      printf '%s\n' "$up_remote"
      return 0
    fi
  fi

  local matches
  matches=$(git remote -v | awk '
    tolower($0) ~ /github\.com[:\/]cubrid\/cubrid(\.git)?[[:space:]]+\(fetch\)/ {
      print $1
    }
  ' | sort -u)
  if [[ -z "$matches" ]]; then
    echo "No git remote points at CUBRID/cubrid (case-insensitive). Available remotes:" >&2
    git remote -v >&2
    return 1
  fi

  local picked=""
  if printf '%s\n' "$matches" | grep -qx 'origin'; then
    picked='origin'
  elif printf '%s\n' "$matches" | grep -qx 'cub'; then
    picked='cub'
  else
    picked=$(printf '%s\n' "$matches" | head -1)
  fi

  echo "Detected CUBRID remote via URL scan: $picked" >&2
  local others
  others=$(printf '%s\n' "$matches" | grep -vx "$picked" | tr '\n' ' ')
  if [[ -n "$others" ]]; then
    echo "Other CUBRID-pointing remotes (ignored): $others" >&2
  fi
  printf '%s\n' "$picked"
}

detect_cubrid_remote() {
  cubrid_detect_remote "$@"
}
