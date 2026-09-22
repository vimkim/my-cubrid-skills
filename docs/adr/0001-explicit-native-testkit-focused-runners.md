# Use explicit native testkit for focused regression runners

The personal focused SQL, medium, and shell workflows select their native cubrid-testkit family explicitly under containment and judge verdict-bearing artifacts rather than process status. CTP remains available as an asset dependency, but native preflight failures stop the workflow instead of silently delegating to the legacy runner; a separate CTP invocation requires an explicit user request.

SQL, medium, and shell retain independent skills and migration gates because their case boundaries and result contracts differ. Medium accepts complete ordered directories only, while shell adoption is limited to the validated focused workflow rather than implying whole-corpus equivalence. The unvalidated isolation skill is removed, with Git history as recovery, instead of presenting legacy behavior as migrated coverage.
