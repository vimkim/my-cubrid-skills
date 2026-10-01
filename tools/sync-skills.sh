#!/usr/bin/env bash
# Sync this repository's skills into the global agent skill directories.
#
# `npx skills add .` only adds or refreshes skills, and local-path installs are
# not recorded in ~/.agents/.skill-lock.json, so deleted or renamed skills stay
# installed. This script prunes them first:
#
#   stale = skills that ever had <name>/SKILL.md in this repo's Git history
#         - skills currently present in the working tree
#         ∩ skills installed in ~/.agents/skills or ~/.claude/skills
#         - skills owned by another source in ~/.agents/.skill-lock.json
#
# Then it reinstalls every current skill.
#
# Usage: tools/sync-skills.sh [--dry-run]
set -euo pipefail

dry_run=0
case "${1:-}" in
  "") ;;
  -n|--dry-run) dry_run=1 ;;
  *) echo "usage: $0 [--dry-run]" >&2; exit 2 ;;
esac

repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cd "$repo"

agents_dir="$HOME/.agents/skills"
claude_dir="$HOME/.claude/skills"
lock_file="$HOME/.agents/.skill-lock.json"
agent_args=(--agent claude-code --agent codex)

current=$(for f in */SKILL.md; do echo "${f%/SKILL.md}"; done | sort -u)

historical=$(git log --all --pretty=format: --name-only -- '*/SKILL.md' \
  | grep -E '^[^/]+/SKILL\.md$' | cut -d/ -f1 | sort -u)

lock_owned=""
if [[ -f "$lock_file" ]]; then
  lock_owned=$(jq -r '.skills | keys[]' "$lock_file" | sort -u)
fi

stale=()
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  grep -qxF "$name" <<<"$current" && continue
  grep -qxF "$name" <<<"$lock_owned" && continue
  [[ -e "$agents_dir/$name" || -L "$claude_dir/$name" || -e "$claude_dir/$name" ]] || continue
  stale+=("$name")
done <<<"$historical"

if ((${#stale[@]})); then
  echo "Stale skills removed from this repo but still installed: ${stale[*]}"
else
  echo "No stale skills to prune."
fi

if ((dry_run)); then
  echo "Current skills: $(tr '\n' ' ' <<<"$current")"
  echo "Dry run: nothing changed."
  exit 0
fi

if ((${#stale[@]})); then
  npx skills remove -g -y "${stale[@]}"
  for name in "${stale[@]}"; do
    if [[ -e "$agents_dir/$name" || -L "$claude_dir/$name" ]]; then
      echo "error: $name is still installed after removal" >&2
      exit 1
    fi
  done
fi

npx skills add . -y -g "${agent_args[@]}"
