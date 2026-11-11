# Known CI issue registry design

Status: proposed, 2026-11-11. Nothing here is implemented.

## Goal

When a CUBRID CI testcase fails, an agent should know at once whether the failure is a tracked issue. When the issue is resolved, the agent should also know whether its fix is already in the tested Engine commit.

Today that knowledge lives in [known-ci-issues.md](../cubrid-common/references/known-ci-issues.md). It has two entries on `main`. The unmerged branch `known-issue-cbrd-28018` (commit `0b0707d`) adds a third entry for `cbrd_27179` and CBRD-28018. That entry carries six prose "Check on match" steps: read the Jira state, find the fix commits, and test their ancestry. Every agent runs those steps by hand. Every new tracked issue would copy them again.

The user proposed a many-to-many map from testcase to issue, stored locally in SQLite, owned by a CLI, with the skills kept small. This document keeps the CLI and the small skills. It rejects SQLite for now. The [last section](#decisions-for-the-user) lists the calls only the user can make.

## Recommendation

Move the check into code, and keep the data as a reviewed text file.

- `cubrid-common/references/known-ci-issues.toml` holds the registry.
- `cubrid-common/scripts/known-issues.py` reads it and runs the check. It needs only the Python standard library (`tomllib`, `subprocess`, `urllib`).
- `known-ci-issues.md` shrinks to the command to run and a table that maps each verdict to a report label.

The check earns code because it is deterministic and repeats per entry: match a scope and a stack, read one Jira field, and run `git merge-base --is-ancestor`. The storage does not earn SQLite. The registry has three rows, and a wrong row hides a real failure from analysis. A diff that the user reviews before `just sync` is the guard against a wrong row. A local database has no such review step.

## Existing tools considered

None of the existing tools holds this data. Two of them supply inputs.

| Tool | Storage | Why the registry does not live there |
|---|---|---|
| `cubrid-tcc` 0.3.0 (Chronicle) | `~/.local/share/cubrid-tc-chronicle/history.sqlite3`, a derived index of retained CI results | Chronicle can rebuild its index from retained snapshots (`reparse`). Curated rows in that database cannot be rebuilt. Its queries are offline, and the check reads Jira. It does not index `test_sql_by_cci`, which one current entry covers, and `cubrid-tcc status cbrd_27179 --suite shell` returns `NOT_INDEXED` today. The registry reuses its testcase identity (suite plus full path) and its suite names. |
| `cubrid-ci` | exact-commit evidence bundles under `~/.local/share/cubrid-ci-data` | It supplies the tested Engine SHA and the failure inventory. It does not extract core stacks. `src/diff.rs` only detects the strings `core dump` and `coredump`. |
| `cubrid-jira-dup` | local CBRD corpus and embeddings | It suggests candidate issues before a registration. It does not decide them. |
| `cubrid-jira` | cache-first issue reads, gated writes | A cached read can show a stale status. The check reads the status fresh. |
| `work-tracker` | SQLite ledger of work items | It tracks work, not failure signatures. |

## Data shape

The registry has two record types. An **issue** is a CBRD key with optional pinned fix commits. A **matcher** binds one failure scope and an optional stack signature to at most one issue. The matcher is the join row, so the many-to-many relation needs no extra table. One testcase can have several matchers for different stacks and issues. One issue can have matchers in several testcases.

```toml
schema = 1

[[issue]]
key = "CBRD-28018"
title = "vacuum fixes a deallocated heap page as OLD_PAGE after a forced server restart"
fix_commits = []

[[matcher]]
id = "cbrd-27179-vacuum-deallocated-page"
issue = "CBRD-28018"
added = 2026-11-11
suite = "shell"
testcase = "shell/_37_elderberry/cbrd_23842_cdc/bug/cbrd_27179/cases/cbrd_27179.sh"
build = "debug"
frames = ["pgbuf_fix_debug", "vacuum_heap_page", "vacuum_heap", "vacuum_process_log_block"]
text = ["was_interrupted=false"]
evidence = ["CUBRID/cubrid#8469", "CUBRID/cubrid#8404", "CUBRID/cubrid#8299 run 42868959374"]
not_covered = "Another stack in this case, the same assertion in another testcase, and the RQG dead_data_03_big_record cores."

[[matcher]]
id = "sql-by-cci-every-branch"
added = 2026-11-09
expires = 2026-12-09
job_contains = "sql_by_cci"
evidence = ["my-cubrid-docs cbrd-oos-sql-by-cci/report.md", "run 42763653366"]
not_covered = "test_sql and other suites."
```

`validate` rejects every state below:

- A matcher has both `testcase` and `job_contains`, or neither. The scope is exactly one of them.
- A matcher has `testcase` but no `suite`. The suite is one of `sql`, `medium`, `shell`, or `sql_by_cci`.
- A matcher has no `issue` and no `expires`. An untracked failure must expire. An issue-backed matcher takes its lifetime from the Jira state.
- A matcher names an issue key that has no `[[issue]]` record.
- Two matchers share an `id`.
- A matcher has `text` but no `frames`. Text alone is too weak a signature.

`frames` is an ordered list of function names. It matches a backtrace when the names appear in that order, innermost first, with any frames between them. `text` lists substrings that must also appear, such as an argument value. A matcher without `frames` matches every failure in its scope. That suits job-level failures such as `sql_by_cci`.

## Verdicts

`check` returns one verdict per matching matcher. The verdict is a closed set, so the skill maps it to a label with one table and no prose branches.

| Verdict | Condition | Report label |
|---|---|---|
| `no_match` | No matcher matched. | Analyze as usual. |
| `expired` | The matched matcher has passed `expires`. | Do not apply. Tell the user to delete or extend the matcher. |
| `known` | The issue is unresolved, or the matcher has no issue and has not expired. | "Known issue, not caused by this PR." Cite the matcher and the issue. |
| `fix_missing` | The issue is resolved as Fixed, and the tested Engine commit does not contain the fix. | Known issue. Tell the user that the branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | The issue is resolved as Fixed, and the tested Engine commit contains the fix. | Do not apply. Analyze the failure as new. Tell the user that the issue may need to be reopened, and cite the run and the stack. |
| `unknown` | Jira did not answer, the resolution is not Fixed, no fix commit was found, or the ancestry could not be computed. | Known issue, with the reason the state is unknown. |

The rules for `fix_present` follow:

1. Use the issue's `fix_commits` when the list is not empty. Otherwise, run `git log --format=%H --grep='\[CBRD-28018\]' origin/develop` in the Engine repository. Squash-merged develop commits start with `[CBRD-n]`.
2. The fix is present when every fix commit is an ancestor of the tested commit (`git merge-base --is-ancestor`).
3. The fix is also present when the tested commit's own history has a commit whose subject names the key. That catches a cherry-pick, which changes the SHA. The JSON output names the rule that decided.

The CLI exits with code 0 for every verdict and code 2 for an operational error such as an unreadable registry. `cubrid-tcc` uses the same convention.

## CLI commands

```text
known-issues.py check (--testcase PATH --suite SUITE | --job NAME)
                      [--stack-file FILE] [--build debug|release]
                      --engine SHA [--engine-repo DIR] [--offline] [--json]
known-issues.py list [--issue KEY | --testcase PATH] [--json]
known-issues.py validate
known-issues.py register --id ID --suite SUITE --testcase PATH | --job-contains TEXT
                         [--issue KEY [--title TEXT]] [--frames F1,F2,...] [--text T]
                         [--expires DATE] --evidence REF... --not-covered TEXT [--write]
```

- `check` reads the registry, matches the scope and the stack, and then reads Jira and Git only for matchers with an issue. `--engine-repo` defaults to `/home/vimkim/gh/cb/develop`. `--offline` skips Jira and returns `unknown` for issue-backed matchers.
- `list` shows the relation in either direction.
- `validate` applies the schema rules above. The repository test suite runs it.
- `register` prints the TOML block it would append, and it writes nothing by default. `--write` appends the block, which adds the `[[issue]]` record when the key is new, and then runs `validate`. Registration is rare, so the command does not edit or delete records. A person removes a matcher by deleting its block in an ordinary reviewed edit.

The Jira read is one anonymous GET with a 30-second timeout: `https://jira.cubrid.org/rest/api/2/issue/<KEY>?fields=status,resolution`. On 2026-11-11 it returned status `Open` and resolution `None` for CBRD-28018.

## How the CI skills call it

`cubrid-ci-analyze` (`SKILL.md` line 117) and `cubrid-ci-trigger` (`SKILL.md` line 117) both point at `known-ci-issues.md`. Both keep that pointer. The reference changes to this routine:

1. For each failure in the inventory, take the suite and the full testcase path from the validated identity. For a job-level failure without testcase records, take the job name.
2. Take the tested Engine SHA from the shard build provenance, as [ci-evidence.md](../cubrid-common/references/ci-evidence.md) requires. A workflow `head_sha` is not enough.
3. If the failure left a core stack, save the backtrace text to a file in the evidence directory and pass it with `--stack-file`.
4. Run `check --json`. Apply the label from the verdict table, and cite the matcher id, the issue, and the rule that decided.
5. Keep every failure in the inventory, whatever its verdict.

`cubrid-common/SKILL.md` line 23 changes its description from "each with an expiry date" to "a registry checked by `scripts/known-issues.py`".

## Register routine

Register a matcher when the analysis concludes that a failure duplicates an existing CBRD issue, or when a failure recurs on every branch and no issue tracks it yet.

1. Confirm the duplicate. Run `cubrid-jira-dup candidate-find` for candidates. The user confirms the issue, because the tool suggests and does not decide.
2. Choose the narrowest signature that still matches every known occurrence. Name the assertion site and the caller that distinguishes the bug. For CBRD-28018 that is `pgbuf_fix_debug` under `vacuum_heap_page` with `was_interrupted=false`. Do not add line numbers. They differ by branch: `vacuum.c` line 1678 on `develop` and line 1776 on `feature/oos-merge` at `cd24a21`.
3. Run `register` without `--write` and show the block to the user.
4. After the user approves, run `register --write`.
5. Prove the matcher. Run `check` with the motivating failure's stack and confirm the verdict is `known`. Run `check` with a stack from another failure in the same testcase, if one exists, and confirm the verdict is `no_match`.
6. Commit and sync through this repository's completion workflow. The matcher is active only after `just sync`.

## Migration

1. Write the three current entries as TOML: the `sql_by_cci` matcher from `main`, and the CBRD-28018 issue and matcher from commit `0b0707d`. The "Check on match" steps become code and are not copied.
2. Run `validate`.
3. Run `check` for each entry and record the output in the change:
   - `--job "shard sql_by_cci 01"` returns `known`.
   - The `cbrd_27179` stack from PR #8299 run 42868959374 returns `known`, because the issue is Open.
   - The same testcase with another stack returns `no_match`.
   - The same stack with `--offline` returns `unknown`.
4. Replace the entries section of `known-ci-issues.md` with the routine and the verdict table.
5. Leave the branch `known-issue-cbrd-28018` alone. The user decides whether to delete it after the migration lands.

## Not built

- SQLite storage. The registry has three rows, and registration needs a review. The user can choose SQLite (see below), and an import from the TOML file takes one command.
- Stack extraction from cores. No current tool extracts stacks. The agent supplies the backtrace text, and the CLI only matches it.
- Fuzzy or embedding matching. `cubrid-jira-dup` does that, before registration.
- Automatic registration. A wrong matcher hides a real failure, so a person approves each one.
- Jira writes, such as a reopen comment on `fix_present`. The CLI reports, and the user acts.
- A Chronicle integration, and direct reads of `cubrid-ci` bundles. Add them when hand-copying the suite, the path, and the SHA causes a mistake.
- Expiry for issue-backed matchers. The Jira state replaces it.

## Decisions for the user

1. **Storage.** The default is a TOML file in this repository. A new matcher then needs a commit and `just sync`, which also give a review. The alternative is your SQLite proposal, with a separate CLI and a database under `~/.local/share`. It registers at once, but it has no diff review and needs its own backups. Choose SQLite if registrations become frequent enough that a commit for each one costs more than the review is worth.
2. **Expiry for issue-backed matchers.** The default drops it. If you want a periodic human review even while the issue stays Open, keep an optional `review_by` date that turns the verdict into `expired`.
3. **Policy on `fix_present`.** The default stops applying the matcher and analyzes the failure as new. The alternative keeps the "known" label with a warning. The default treats a recurrence after the fix as a possible regression.
4. **The branch `known-issue-cbrd-28018`.** The default leaves it in place. Its content moves into the TOML file during migration. You decide whether to delete it after the migration.
5. **Approval for each registration.** The default asks you before every `register --write`. You can allow agents to register without asking when `cubrid-jira-dup` and the stack both match, but that removes the guard against a wrong matcher.
