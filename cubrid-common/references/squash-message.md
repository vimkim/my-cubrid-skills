# Squash commit message convention

Every CUBRID PR lands on its target branch as one squash commit. The squash commit message is the permanent record of the change, so write it for a developer who reads `git log` years later without the PR page. GitHub's default body, a list of every commit in the PR, is not the convention. The convention below comes from the `develop` history of `CUBRID/cubrid` (64 of 80 recent squash commits start the body with the JIRA URL, and 67 of 80 use the title form) and applies to `CUBRID/cubrid-testcases` and `CUBRID/cubrid-testcases-private-ex` too.

## Format

```text
[CBRD-NNNNN] <PR title> (#<PR number>)

https://jira.cubrid.org/browse/CBRD-NNNNN

<What was wrong or missing, and why it mattered.>

<What the change does.>

- <file or function>: <one change>
- <file or function>: <one change>

Co-Authored-By: <attribution trailer when the session requires one>
```

- **Title**: the issue key in brackets, the PR title, and `(#N)` with the PR number. When `commit_title` is passed to the merge API, GitHub does not add `(#N)`; write it yourself.
- **Blank line** between the title and the body.
- **First body line**: the JIRA URL of the same issue key.
- **English only.** The whole message is ASCII. A Korean PR title or body is rewritten in English, as a summary, not a line-by-line translation.
- **Body lines fit 72 columns.** A line that holds only a URL may be longer.
- **Summary, not history.** Describe the final change. Leave out review rounds, rebases, sync commits, and `* [KEY] ...` commit lists.

## Content

- **Engine PR**: start with the problem (the AS-IS behavior and its consequence), then the fix (the TO-BE behavior). Add one bullet per significant change, named by file and function as in `heap_file.c: add heap_attrinfo_transform_to_disk_keep_form ()`. State what does not change when a reader would ask (`The log format does not change.`). Name PRs or issues that this one replaces.
- **Testcase PR**: name each added or changed testcase path and the engine PR it covers (`CUBRID/cubrid#N`). Say what each case checks, as a short list when there are several checks.
- Read the PR body, the diff (`gh pr diff`), and the linked issue. The commit list is not a source; it describes how the work went, not what it does.

## Check

`pr-final-merge-handoff lint-message FILE --pr N --ticket CBRD-NNNNN` checks a message file (title line, blank line, body) against the format rules above. `pr-final-merge-handoff plan` and `execute` run the same check on every `--message` file and refuse a merge without one.

## Example

`CUBRID/cubrid#8514` (CBRD-28073):

```text
[CBRD-28073] Keep serial row storage form in NEXT VALUE (#8514)

https://jira.cubrid.org/browse/CBRD-28073

NEXT VALUE writes a _db_serial row under a redo-only log record. While
it re-encoded the row, it moved a long comment into a new OOS chain,
which a rollback can undo. On a 4K page database every NEXT VALUE left
one chain behind (CBRD-28035), and after a rollback in SA mode the row
pointed to a deleted chain and failed with -1398 (CBRD-28052).

NEXT VALUE now keeps the storage form of every column. An inline comment
stays inline, and a comment already in OOS keeps pointing to its chain.

- heap_file.c: add heap_attrinfo_transform_to_disk_keep_form (). It
  encodes like heap_attrinfo_transform_to_disk (), but each variable
  column follows the form of the record it replaces. It does not move a
  column out of the row and does not insert OOS records.
- serial.c: serial_update_serial_object () (NEXT VALUE and the cache
  write), serial_row_write_keep_value () (the DDL merge) and
  serial_repl_rebuild_image () (HA apply) use it.
- The log format does not change.

This replaces #8492 (CBRD-28035) and #8496 (CBRD-28052).
```
