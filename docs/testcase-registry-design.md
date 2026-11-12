# Testcase knowledge registry design

Status: revision 3, 2026-11-11. The user accepted this design and every default in the last section. The CLI is merged into `main` of the local repository `~/gh/cubrid-tc-registry` and installed as `cubrid-tcr` 0.1.0. On 2026-11-12 the migration loaded the three `known-ci-issues.md` entries into the real registry, with both rules approved by the user.

## Goal

When a CUBRID CI testcase fails, an agent should see everything known about that testcase in one query. The query answers three questions:

1. Which PRs and which branches failed this testcase, and with which failure signature? The view covers all indexed history by default.
2. Which issues relate to this testcase, and how does each relate?
3. Which notes did people or agents leave about it?

Only part of that view decides the analysis. A tracked issue can still mark a failure as "known, not caused by this PR". The analysis then also needs to know whether the fix should already be in the tested Engine commit.

Revision 1 centered on a matcher that filters failures. This revision centers on the testcase, because the user asked for a testcase-centered view: "a TC failed in several PRs in the last 60 days and seems related to several issues", and "a feature branch already failed this TC earlier". The filter becomes one part of that view.

Today the knowledge lives in [known-ci-issues.md](../cubrid-common/references/known-ci-issues.md). It has three entries on `main`. Commit `0b0707d` added the third, for `cbrd_27179` and CBRD-28018, with six prose "Check on match" steps.

## Recommendation

- Build a new CLI, `cubrid-tcr` (testcase registry), in its own repository at `~/gh/cubrid-tc-registry`. Install it as a uv tool, like `cubrid-tcc`.
- Store curated knowledge in SQLite at `~/.local/share/cubrid-tc-registry/registry.sqlite3`. This reverses revision 1, and the user confirmed it. The reasons are in [Storage](#storage-sqlite-now-earns-its-place).
- Read failure history from Chronicle (`cubrid-tcc`). Do not collect it again.
- Store only what no current tool has. That is failure signatures, issue links, notes, and the known-issue rules.
- Keep the skills small. `known-ci-issues.md` shrinks to the routine and the verdict table.

## Where the failure history comes from

Chronicle already indexes testcase history by identity, and it is the right source. `cubrid-ci` collects exact-commit evidence for one PR head or one Engine commit. It does not answer "which PRs failed this testcase". It stays the source of the current failure inventory.

On 2026-11-11, one Chronicle occurrence of `cbrd_27179` (run 42868959374, after a bounded sync) carried these fields:

| Need | Chronicle field | Value for run 42868959374 |
|---|---|---|
| Testcase identity | `identity` | `CUBRID/cubrid-testcases-private-ex`, `shell`, the full path |
| PR | `pull_request.number` | 8299 |
| Target branch | `pull_request.base_ref` | `feature/oos-merge` |
| Engine commit | `engine_sha` | `cd24a212aa81` |
| Testcase revision | `testcase_sha`, `testcase_branch` | `55cc0fc6`, `tc/pr-8299` |
| Build | `build_mode` | `debug` |
| Time | `completed_at` | 2026-11-10T22:37:55Z |
| Outcome | `outcome`, `raw_verdict` | `FAIL` from `failed.list` |
| Signature | none | The shard has no JUnit XML (`failure_list_only`), so no message or stack is stored. |

`cubrid-tcc history <case> --suite <suite> --since <date> --json` returns these occurrences. `engine_branch` was `null` for this `issue_comment` run, so the view uses `pull_request.base_ref` and falls back to `engine_branch`. The view shows "unknown" when both are missing.

Chronicle has no failure signature. A crash shard gives only a failed list, with no stack. The registry therefore stores signatures and attaches them to Chronicle occurrences by stable keys. Chronicle does not index `test_sql_by_cci`, so that suite has no history in the view.

### Why `cbrd_27179` was NOT_INDEXED

The cause was a coverage gap in the local index. Chronicle had no defect. These facts were measured on 2026-11-11:

1. The testcase entered both `develop` and `feature/oos-merge` of the testcase repository in commit `ee2aae2bc`, on 2026-11-09 at 01:30 UTC.
2. Chronicle discovery covered runs created through 2026-11-10T11:23Z, with `discovery_complete: false`. The index held one shell run that completed after the testcase was added, and that run did not include the CDC shard.
3. The failing run 42868959374 completed at 2026-11-10T22:37:55Z, after the discovery window.
4. A bounded `cubrid-tcc sync-data --run 42868959374 --suite shell --revisit-limit 0` inserted 50 partial snapshots. `cubrid-tcc status cbrd_27179 --suite shell` then returned `FAILING` with 1 observation.

Two lessons follow for the design. The view must show Chronicle freshness and name the bounded sync that fills a gap. "No history" must also stay separate from "never failed".

## Data shape

The registry keys every record by Chronicle's testcase identity: repository, suite, path, and variant. It never keys records by Chronicle's local `execution.id`, which belongs to one local index.

| Record | Holds | Changes the analysis? |
|---|---|---|
| `signature` | A named failure shape for one testcase: ordered stack `frames`, required `text`, and a label. | No |
| `occurrence_signature` | One Chronicle occurrence, keyed by repository, run, attempt, shard, testcase, and ordinal, tagged with one signature. It also records the digest of the stack file and the actor. | No |
| `issue_link` | A testcase, an issue key, a relation, and an optional signature. | No |
| `note` | Free text about a testcase, with author, time, and optional references. Notes are append-only. A retired note stays in history. | No |
| `rule` | A known-issue rule. Its scope is either a signature or a job-name substring. It has an optional issue, an optional expiry, `not_covered`, and the approval that created it. | Yes |
| `event` | An append-only log of every write: actor, time, command, and before and after values. | No |

`issue_link.relation` is a closed set:

| Relation | Meaning | `cbrd_27179` example |
|---|---|---|
| `origin` | The testcase was written for this issue. | CBRD-27179 |
| `tracks` | This issue tracks a failure of the testcase. Confirmed by a person. | CBRD-28018, with signature `cbrd_27179-vacuum-deallocated-page` |
| `suspected` | The failure looks related, but nobody has confirmed it. | Not used yet |
| `fixed_by` | This issue's fix resolved an earlier failure. | Not used yet |

### Separate the filter from the reference

The registry separates the rule that filters from the link that only informs. A link never changes a verdict. Only a `rule` makes a failure "known". The two have different stakes. A wrong `suspected` link costs a reader a minute. A wrong rule hides a real failure from analysis.

- An agent can add a link, a signature, or a note without approval.
- Only a person can approve a rule, and the rule records who approved it.
- A rule with an issue requires a `tracks` link to the same issue for each testcase in its scope. `rule add` creates that link if it is missing.

`validate` rejects these states:

- A rule has both a signature scope and a job scope, or neither.
- A rule has no issue and no `expires`. An issue-backed rule takes its lifetime from the Jira state.
- A signature has `text` but no `frames`.
- An `occurrence_signature` points at a signature of a different testcase.
- A key other than `CBRD-<digits>` appears.

## Storage: SQLite now earns its place

Revision 1 chose a TOML file in this repository. The decision rested on three facts: the writes were rare, a wrong row was dangerous, and a commit followed by `just sync` gave a review. The new requirement changes the first fact. Each CI analysis now writes signatures, links, and notes, and parallel agent sessions do this at the same time. Under the TOML design, every note would need a skills-repository commit and a `just sync`, and parallel sessions would conflict on one file.

| Concern | TOML in this repository | SQLite in a CLI |
|---|---|---|
| A note from each analysis | One commit and `just sync` each | One transaction |
| Parallel agent sessions | Conflicts on one file | Serialized writes in WAL mode |
| Review of a wrong rule | Git diff | An approval flag on `rule add`, plus the `event` log |
| History | Git log | The `event` table |
| Backup | Git remote | `cubrid-tcr backup`, same as `work-tracker backup` |
| Joins with Chronicle | Loaded into memory | Indexed by the same identity keys |

SQLite wins now. The review gate moves from the diff to the approval step on `rule add`. That step was already the important one.

## CLI commands

```text
cubrid-tcr show CASE [--suite S] [--days N | --all] [--json]
cubrid-tcr check (--case CASE [--suite S] | --job NAME) --engine SHA
                 [--stack-file F] [--engine-repo DIR] [--offline] [--no-context] [--json]
cubrid-tcr signature add CASE --suite S --id ID --frames F1,F2,... [--text T] --label TEXT
cubrid-tcr signature attach CASE --suite S --run ID --shard N [--attempt N] --stack-file F
                 [--signature ID]
cubrid-tcr link CASE --suite S --issue KEY --relation origin|tracks|suspected|fixed_by [--signature ID]
cubrid-tcr note CASE --suite S --body TEXT [--ref REF...]
cubrid-tcr rule add --id ID (--signature ID | --job-contains TEXT) [--issue KEY] [--expires DATE]
                    --not-covered TEXT [--approved-by NAME --yes]
cubrid-tcr rule retire ID --reason TEXT
cubrid-tcr validate | log [CASE] | backup | export [--format toml]
```

- `show` is the testcase view. It resolves the case through `cubrid-tcc find`, reads `cubrid-tcc history` with no date window, and merges the registry records. The window applies only to the Chronicle failure list. Links, notes, rules, and signatures always appear in full.
  - By default, `show` lists every indexed failure.
  - If the list has more than 50 failures, `show` lists only the failures of the last 60 days. It summarizes the older ones as counts by branch and by signature, with the first and last failure dates, and it marks the output as shortened.
  - `--days N` always limits the list to N days. `--all` always lists every failure.
  - `show` never passes Chronicle's raw JSON through. One `history` result for one occurrence of `cbrd_27179` was about 350 KB.

  Its output has these parts:
  - Failures grouped by PR, with the target branch, the Engine commit, the time, and the signature. A failure with no signature shows "signature unknown".
  - Counts by branch and by signature.
  - Issue links by relation.
  - Active rules.
  - Notes, newest first.
  - Chronicle freshness and the bounded `sync-data` command to run when coverage is stale.
- `check` returns the verdict for one failure, and it also returns the `show` summary. One call gives the analyst the verdict and the context.
- `signature attach` matches the stack file against the testcase's signatures. If exactly one signature matches, it attaches that signature. If none matches, it prints the frames it parsed so that the agent can add a new signature. If more than one matches, it attaches nothing and lists them.
- `rule add` prints the rule and writes nothing without `--yes` and `--approved-by`.
- `export --format toml` writes a readable snapshot for review or for a Git backup.

Every write command is idempotent. A unique key covers each link, each occurrence tag, and each signature id. A repeated command reports "unchanged" and adds no event.

## Verdicts

The verdict rules from revision 1 apply to `rule` records. They are unchanged.

| Verdict | Condition | Report label |
|---|---|---|
| `no_match` | No rule matched. | Analyze as usual. Use the `show` context. |
| `expired` | The matched rule has passed `expires`. | Do not apply. Tell the user to retire or extend the rule. |
| `known` | The issue is unresolved, or the rule has no issue and has not expired. | "Known issue, not caused by this PR." Cite the rule and the issue. |
| `fix_missing` | The issue is resolved as Fixed, and the tested Engine commit does not contain the fix. | Known issue. Tell the user that the branch lacks the fix. For `feature/oos-merge`, a develop sync is needed. |
| `fix_present` | The issue is resolved as Fixed, and the tested Engine commit contains the fix. | Do not apply. Analyze the failure as new. Tell the user that the issue may need to be reopened. |
| `unknown` | Jira did not answer, the resolution is not Fixed, no fix commit was found, or the ancestry could not be computed. | Known issue, with the reason the state is unknown. |

A signature rule matches when the stack file matches its signature: the frames appear in order, innermost first, with any frames between them, and every `text` substring is present. Without `--stack-file`, a signature rule returns `unknown` with the reason "no stack". It never returns `no_match` in that case, because the failure may still be the known crash.

The fix is present under either of these conditions:

1. Every fix commit is an ancestor of the tested commit. The fix commits come from `git log --format=%H --grep='\[CBRD-n\]' origin/develop` in `/home/vimkim/gh/cb/develop`, because squash-merged develop commits start with `[CBRD-n]`.
2. The tested commit's own history has a commit whose subject names the key. That condition catches a cherry-pick, which changes the SHA.

The Jira read is one anonymous GET with a 30-second timeout on `rest/api/2/issue/<KEY>?fields=status,resolution`. On 2026-11-11 it returned `Open` and resolution `None` for CBRD-28018, and `origin/develop` had no commit naming CBRD-28018. The CLI exits with code 0 for every verdict and with code 2 for an operational error.

## How the CI skills call it

`cubrid-ci-analyze` and `cubrid-ci-trigger` keep their pointer to `known-ci-issues.md`. The reference becomes this routine for each failure in the inventory:

1. Take the suite and the full testcase path from the validated identity. For a job-level failure without testcase records, take the job name.
2. Take the tested Engine SHA from the shard build provenance, as [ci-evidence.md](../cubrid-common/references/ci-evidence.md) requires.
3. If the failure left a core stack, save the backtrace text in the evidence directory.
4. Run `cubrid-tcr check --json` with the stack file. Apply the label from the verdict table, and put the `show` summary in the report as history context. History context never proves the root cause.
5. If `show` reports stale Chronicle coverage for the window, run the bounded sync it names, and run `check` again once.
6. After the analysis, record what it learned. Run `signature attach` for the stack. Run `link --relation suspected` for an issue that looks related. Run `note` for a fact a later reader needs. Propose a `rule` to the user only when a person confirmed the duplicate.

## Register a known-issue rule

1. Confirm the duplicate. `cubrid-jira-dup candidate-find` suggests candidates, and the user confirms one.
2. Choose the narrowest signature that matches every known occurrence. For CBRD-28018 that is `pgbuf_fix_debug` under `vacuum_heap_page`, `vacuum_heap`, and `vacuum_process_log_block`, with `was_interrupted=false`. Do not use line numbers, because they differ by branch (`vacuum.c` line 1678 on `develop`, line 1776 on `feature/oos-merge` at `cd24a21`).
3. Run `rule add` without `--yes`, and show the result to the user.
4. After approval, run it again with `--yes --approved-by <name>`.
5. Prove the rule. `check` with the motivating stack returns `known`. `check` with another stack from the same testcase, if one exists, returns `no_match`.

## Migration

1. Create the CBRD-28018 records from the `main` entry added in commit `0b0707d`: signature `cbrd_27179-vacuum-deallocated-page` on `cbrd_27179`, an `origin` link to CBRD-27179, a `tracks` link to CBRD-28018, and the rule with approval by the user. Attach the signature to the run 42868959374 occurrence, and record PRs #8469 and #8404 as a note until their runs are synced into Chronicle.
2. Create the `sql_by_cci` job rule with `expires = 2026-12-09`.
3. Run `validate`. Then run `check` for each case: the job `shard sql_by_cci 01` returns `known`, the `cbrd_27179` stack returns `known`, another stack returns `no_match`, and `--offline` returns `unknown`.
4. Replace the entries section of `known-ci-issues.md` with the routine and the verdict table.

## Not built

- Collecting failure history again. Chronicle owns it. Improve Chronicle when a field is missing.
- Stack extraction from cores. No current tool extracts stacks. The agent supplies the backtrace text, and the CLI parses and matches it.
- Fuzzy or embedding matching. `cubrid-jira-dup` does that before a link becomes `tracks`.
- Rules created without a person's approval.
- Jira writes, such as a reopen comment on `fix_present`.
- A history view for `test_sql_by_cci`, until Chronicle indexes that suite.
- Expiry for issue-backed rules. The Jira state replaces it.

## Decisions for the user

On 2026-11-11 the user confirmed SQLite storage. The user also confirmed an unlimited default window that shortens to 60 days past 50 failures. The 50-failure threshold is an estimate, to be tuned in use. The user then accepted the default of decisions 1 to 4 below. Decision 5 is settled, because the branch was merged into `main` as `0b0707d` and deleted.

1. **The new repository and the name.** The default is `~/gh/cubrid-tc-registry` with the command `cubrid-tcr`. You can instead ask for these records as a separate database inside Chronicle, with `cubrid-tcc note` and related commands. That gives one tool, but it puts curated data next to an index that Chronicle can rebuild, and it adds Jira reads to a tool that is offline today.
2. **Who may write a `suspected` link or a note.** The default lets agents write both without asking, because neither changes a verdict. You can require approval for links as well.
3. **Expiry for issue-backed rules.** The default drops it. You can add an optional `review_by` date.
4. **Policy on `fix_present`.** The default stops applying the rule and analyzes the failure as new.
5. **The branch `known-issue-cbrd-28018`.** The default leaves it in place.
