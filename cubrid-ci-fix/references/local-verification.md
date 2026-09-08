# Local verification routing

Read [CTP preflight](../../cubrid-common/references/ctp-preflight.md) before running runtime tests.

- Shell: use [cubrid-shell-run](../../cubrid-shell-run/SKILL.md).
- SQL/medium: use [cubrid-sql-run](../../cubrid-sql-run/SKILL.md).
- Isolation cases: use [cubrid-isolation-test](../../cubrid-isolation-test/SKILL.md) when the failure actually requires that runner.

## Verification boundaries

Record CI/local configuration differences and distinguish a diagnostic probe from a faithful regression replay. Investigate flakes with controlled repeated runs and preserve all attempts; one later pass does not erase an earlier failure. Compare a stable baseline when intended behavior is uncertain. Expected-answer changes require a behavioral justification and preservation of assertion coverage.

For non-runtime checks, inspect the exact `.github/workflows` job and reproduce its relevant commands with the tested base/merge tree and tool versions. Formatting and license checks do not require an unrelated CTP run, but engine edits still require build and appropriate regression verification. No local run proves that remote CI consumed unpublished testcase changes.
