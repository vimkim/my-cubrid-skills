# my-cubrid-skills justfile

# Verify current installations, then recoverably prune eligible obsolete skills
sync *args:
    tools/sync-skills.sh {{args}}

# Preview installations, conflicts and removals without mutation
sync-dry-run *args:
    tools/sync-skills.sh --dry-run {{args}}

# List installed skills
list:
    npx skills list -g --agent claude-code --agent codex

# Remove a specific skill
remove skill:
    npx skills remove -g --yes {{ skill }}
