# my-cubrid-skills justfile

# Install all skills globally for Claude Code and Codex
install:
    npx skills add . -y -g --agent claude-code --agent codex

# Reinstall all skills globally for Claude Code and Codex
reinstall: install

# Update this repo, update global skills, then reinstall this collection
update:
    git pull --ff-only
    npx skills update -g -y
    just install

# List installed skills
list:
    npx skills list -g --agent claude-code --agent codex

# Update installed global skills
update-installed:
    npx skills update -g -y

# Remove a specific skill
remove skill:
    npx skills remove -g --agent claude-code --agent codex --yes {{ skill }}
