#!/usr/bin/env bash
# Standalone compatible engine; shared ownership protects transferred skills.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec "${SKILLS_SYNC_PYTHON:-python3}" "$root/tools/sync_skills.py" --collection "$root" "$@"
