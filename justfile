# my-cubrid-skills justfile

# Sync installed skills with this repo: prune deleted/renamed skills, then install all current ones
sync:
    tools/sync-skills.sh

# Show which installed skills sync would prune, without changing anything
sync-dry-run:
    tools/sync-skills.sh --dry-run

# List installed skills
list:
    npx skills list -g --agent claude-code --agent codex

# Remove a specific skill
remove skill:
    npx skills remove -g --yes {{ skill }}
