# my-cubrid-skills justfile

# Install all skills globally
install:
    npx skills add . -y -g

# List installed skills
list:
    npx skills list

# Check for updates
check:
    npx skills check

# Remove a specific skill
remove skill:
    npx skills remove {{skill}}
