---
name: cubrid-xref
description: Look up linked JIRA issues from a CUBRID GitHub PR or look up bundled engine and testcase PRs from a JIRA key with 24-hour local SQLite caching. Use when given only a PR URL or number to find its CBRD issue, or when given a CBRD ticket to list all associated engine, tc-private, tc-public, and follow-up PRs. Triggers on phrases like 'which JIRA issue is this PR for', 'find PRs for CBRD-XXXXX', 'PR to JIRA', 'JIRA to PR', 'cubrid-xref', 'find linked TC PRs'.
argument-hint: "<PR-URL|PR-number|CBRD-XXXXX|JIRA-URL>"
---

# CUBRID Cross-Reference Lookup (`cubrid-xref`)

Use the standalone `cubrid-xref` CLI to resolve bidirectional links between CUBRID GitHub pull requests (`CUBRID/cubrid`, `CUBRID/cubrid-testcases-private-ex`, `CUBRID/cubrid-testcases-private`, `CUBRID/cubrid-testcases`) and CUBRID JIRA issues (`CBRD-*`, `LETS-*`, `APIS-*`, etc.).

## 1. Check CLI preflight

Verify `cubrid-xref` is on `PATH`:

```bash
command -v cubrid-xref
```

If missing, install it from the local checkout or GitHub before continuing:

```bash
cd ~/gh/cubrid-xref && just sync
# or: uv tool install git+https://github.com/vimkim/cubrid-xref
```

## 2. Run the lookup

`cubrid-xref` auto-detects PR vs JIRA targets and caches results for **24 hours** in `~/.cache/cubrid-xref/cache.sqlite3` (WAL SQLite, `0700` dir / `0600` file). Looking up a JIRA issue also cross-populates single-issue PR cache entries for its bundles.

- **PR -> JIRA** (also discovers sibling `engine`, `tc-private`, and `tc-public` PRs via `tc/pr-<N>`):

  ```bash
  cubrid-xref https://github.com/CUBRID/cubrid/pull/8693
  cubrid-xref 8693
  cubrid-xref cubrid-testcases-private-ex#5098
  cubrid-xref pr 4400 --repo CUBRID/cubrid-testcases
  ```

- **JIRA -> PR** (groups each engine PR with its `tc-private` and `tc-public` PRs into bundles):

  ```bash
  cubrid-xref CBRD-28257
  cubrid-xref https://jira.cubrid.org/browse/CBRD-28257
  cubrid-xref jira 28257
  ```

- **Cache refresh, offline reads, follow-ups, and output formats**:

  ```bash
  cubrid-xref --refresh CBRD-28257      # bypass fresh cache and update stored entry
  cubrid-xref --cache-only CBRD-28257   # read cached entry offline (even if expired)
  cubrid-xref --no-cache 8693           # bypass cache read and write
  cubrid-xref --ttl 12 CBRD-28257       # custom TTL in hours (default: 24)
  cubrid-xref cache status              # inspect cache path, size, and entry counts
  cubrid-xref cache clear --expired     # prune expired entries (omit --expired for full wipe)
  cubrid-xref CBRD-28257 --follow-links # also resolve PRs for linked/subtask JIRA issues
  cubrid-xref CBRD-28257 --include-mentions
  cubrid-xref CBRD-28257 --no-jira
  cubrid-xref --json 8693
  cubrid-xref --plain CBRD-28257
  ```

## 3. Present results clearly

- **PR -> JIRA**: report the target PR, all linked primary JIRA issue keys with status/summary/URL (handling rare multi-CBRD PRs where multiple keys appear in the title), and the sibling `engine`, `tc-private`, and `tc-public` PRs.
- **JIRA -> PR**: present each PR bundle grouped as `engine` + `tc-private` + `tc-public`, keeping closed/reopened/reverted PRs visible with their state (`[OPEN]`, `[DRAFT]`, `[MERGED]`, `[CLOSED]`, `[CLOSED/DRAFT]`).
- Mention `Standalone TC PRs` (such as legacy pre-`tc/pr-N` TC PRs, release backport TC PRs, or `cubrid-testcases-private` HA shell PRs) and `Other Repository PRs` when present.
- When `Related JIRA Issues` appear without `--follow-links`, note them and offer or run `--follow-links` (with `--max-related N`, default `10`) if the user also wants PRs for follow-up or subtask issues.
- If a cached hit looks outdated for an actively changing PR, re-run with `--refresh` (or `-r` / `-u` / `--update`).

## 4. Handle edge cases

- **Legacy engine PRs with no TC PRs**: `tc-private: (none)` and `tc-public: (none)` is expected when an engine PR predates `tc/pr-N` automation or has no TC change.
- **Ambiguous bare digits**: bare digits such as `8693` default to `CUBRID/cubrid#8693`; pass `jira 28257` or `CBRD-28257` for JIRA keys, or `--repo OWNER/REPO` for a non-engine PR number.
- **JIRA unreachable or unauthenticated**: the CLI warns on stderr and still returns GitHub results (without caching degraded results); pass `--no-jira` to skip JIRA queries intentionally.
- **Exit codes**: `0` success, `1` not found or offline cache miss, `2` invalid target/usage, `75` transient upstream/rate-limit failure, `78` missing or invalid auth.
