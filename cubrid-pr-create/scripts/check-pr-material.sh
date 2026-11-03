#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: check-pr-material.sh [--existing-body] --body PR_BODY.md [FILE...]

Checks generated CUBRID PR material before publishing.

Rules:
  - New PR body top-level sections must be exactly:
      ## Purpose
      ## Implementation
      ## Remarks
  - Generated material must not contain local absolute paths or file:// URLs.
  - Generated material must not contain task-runner shortcut commands beginning with "just".
  - Shared links must pass the common Python personal-host check.
EOF
}

existing_body=0
body_file=""
files=()

while (($#)); do
  case "$1" in
    --existing-body)
      existing_body=1
      ;;
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

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 "$script_dir/../../cubrid-common/scripts/check-shared-links.py" "${files[@]}"; then
  fail=1
fi

if ((!existing_body)); then
  if ! headers="$(awk '
    {
      sub(/\r$/, "")
      line = $0
      candidate = line
      sub(/^   /, "", candidate)
      if (candidate == line) sub(/^  /, "", candidate)
      if (candidate == line) sub(/^ /, "", candidate)
      char = substr(candidate, 1, 1)
      count = 0
      if (char == "`" || char == "~") {
        while (substr(candidate, count + 1, 1) == char) count++
      }
      if (inside) {
        if (char == fence && count >= opening && substr(candidate, count + 1) ~ /^[[:space:]]*$/) inside = 0
        next
      }
      if (count >= 3 && (char != "`" || index(substr(candidate, count + 1), "`") == 0)) {
        inside = 1
        fence = char
        opening = count
        next
      }
      if (line ~ /^##[[:space:]]+/) {
        sub(/^##[[:space:]]+/, "", line)
        sub(/[[:space:]]+$/, "", line)
        print line
      }
    }
  ' "$body_file")"; then
    echo "error: failed to scan PR body headings: $body_file" >&2
    exit 1
  fi
  body_headers=()
  if [[ -n "$headers" ]]; then
    mapfile -t body_headers <<< "$headers"
  fi
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
fi

if ((fail)); then
  exit 1
fi

echo "PR material check passed."
