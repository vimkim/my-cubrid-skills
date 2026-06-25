#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: check-pr-material.sh --body PR_BODY.md FILE...

Checks generated CUBRID PR material before publishing.

Rules:
  - PR body top-level sections must be exactly:
      ## Purpose
      ## Implementation
      ## Remarks
  - Generated material must not contain local absolute paths or file:// URLs.
  - Generated material must not contain task-runner shortcut commands beginning with "just".
EOF
}

body_file=""
files=()

while (($#)); do
  case "$1" in
    --body)
      shift
      if (($# == 0)); then
        echo "error: --body requires a file" >&2
        usage
        exit 2
      fi
      body_file="$1"
      files+=("$1")
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while (($#)); do
        files+=("$1")
        shift
      done
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      files+=("$1")
      ;;
  esac
  shift
done

if [[ -z "$body_file" ]]; then
  echo "error: --body is required" >&2
  usage
  exit 2
fi

if ((${#files[@]} == 0)); then
  echo "error: at least one file is required" >&2
  usage
  exit 2
fi

fail=0

for file in "${files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "error: not a file: $file" >&2
    fail=1
  fi
done

if ((fail)); then
  exit 1
fi

check_pattern() {
  local label="$1"
  local pattern="$2"
  local file="$3"
  local matches

  matches="$(grep -nE "$pattern" "$file" || true)"
  if [[ -n "$matches" ]]; then
    echo "error: $label found in $file" >&2
    echo "$matches" >&2
    fail=1
  fi
}

local_path_re='(/home/[[:alnum:]_.-]+/|/Users/[[:alnum:]_.-]+/|file://|[[:alpha:]]:\\(Users|home)\\|[[:alpha:]]:\\)'
just_command_re='(^|[[:space:]`$>])just[[:space:]]+[[:alnum:]_.:/-]+'

for file in "${files[@]}"; do
  check_pattern "local path or file URL" "$local_path_re" "$file"
  check_pattern "just task-runner command" "$just_command_re" "$file"
done

mapfile -t body_headers < <(grep -E '^##[[:space:]]+' "$body_file" | sed -E 's/^##[[:space:]]+//; s/[[:space:]]+$//')
expected_headers=("Purpose" "Implementation" "Remarks")

if ((${#body_headers[@]} != ${#expected_headers[@]})); then
  echo "error: PR body must contain exactly these top-level sections: ## Purpose, ## Implementation, ## Remarks" >&2
  printf 'found: %s\n' "${body_headers[*]:-(none)}" >&2
  fail=1
else
  for i in "${!expected_headers[@]}"; do
    if [[ "${body_headers[$i]}" != "${expected_headers[$i]}" ]]; then
      echo "error: PR body section $((i + 1)) must be ## ${expected_headers[$i]}, found ## ${body_headers[$i]}" >&2
      fail=1
    fi
  done
fi

if ((fail)); then
  exit 1
fi

echo "PR material check passed."
