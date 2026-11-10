---
name: cubrid-jira-dup
description: Find existing CBRD JIRA issues that a draft or an issue may duplicate, with the `cubrid-jira-dup candidate-find` CLI, and judge each candidate. Use before you create a CBRD issue, before you publish an issue description, or when the user asks whether an issue already exists. Triggers on phrases like 'check for duplicate issues', 'is there already a JIRA issue for this', 'find related CBRD issues', '중복 이슈 찾아줘', '비슷한 이슈 있어?'.
---

# CUBRID JIRA Duplicate Check

The `cubrid-jira-dup candidate-find` CLI suggests existing CBRD issues. It does not decide. You read the candidates and decide which ones are duplicates or related issues. This check never writes to JIRA.

## 1. Preflight

Run `command -v cubrid-jira-dup`. If the command is not found, stop and tell the user:

```text
Error: `cubrid-jira-dup` is not installed.

Install it:
    uv tool install git+https://github.com/vimkim/cubrid-jira-duplicate-poc
```

The first run builds a local index of all anonymously visible CBRD issues and downloads an embedding model of about 470 MB. This takes 13 to 36 minutes on a CPU and uses about 670 MB of disk under `~/.cache/cubrid-jira-dup`. If `~/.cache/cubrid-jira-dup/index.db` does not exist, tell the user this before you start. Run the first build in the background when the harness lets you, and continue other work while it runs.

## 2. Select the input

Use exactly one input:

- A saved Markdown draft. The first `# ` line is the title and the remaining text is the body:

  ```bash
  cubrid-jira-dup candidate-find DRAFT_FILE --json > CANDIDATES_JSON
  ```

- An existing issue key. The tool excludes that issue from the candidates:

  ```bash
  cubrid-jira-dup candidate-find CBRD-NNNNN --json > CANDIDATES_JSON
  ```

- A title and a body that are not in a file. Send the body on stdin:

  ```bash
  printf '%s\n' "$body" | cubrid-jira-dup candidate-find --title "$title" --json > CANDIDATES_JSON
  ```

Write `CANDIDATES_JSON` to a scratch or temporary directory, not to a repository. Keep the default of 20 candidates. Use `--no-sync` only when JIRA is not reachable or the user asks for it.

## 3. Read the result

Use these fields:

- `complete` and `errors`: if `complete` is `false`, the sync failed and the search used the old index. Report this to the user.
- If the draft is for an existing issue, that issue can appear as a candidate. Ignore it.
- `candidates[]`: `rank`, `key`, `url`, `summary`, `issuetype`, `status`, `resolution`, `created`, and `signals`. The signals show why the tool ranked the candidate, for example shared identifiers or error codes.

Exit codes:

- `0`: the sync and the search completed. Zero candidates is a valid result.
- `2`: bad input, no index, or an incomplete sync. If stdout still contains JSON, use the candidates and report the incomplete sync. If stdout is empty, report the exact stderr text and stop the check. Do not claim that no duplicates exist.

## 4. Judge the candidates

1. Read the summary and signals of all candidates.
2. For each candidate that can be about the same problem, read the issue with `cubrid-jira search CBRD-NNNNN`. Read at most 8 issues unless the user asks for more.
3. Classify each candidate that you read:
   - **Duplicate**: the same problem, the same cause or the same requested outcome. A new issue would repeat it.
   - **Related**: the same component or symptom, but a different problem. Link it or mention it in the new issue.
   - **Unrelated**: do not report it.
4. Base each verdict on the issue text. Do not base a verdict on rank or on title words alone. If the evidence is not sufficient, say "possibly duplicate" and state what is missing.

## 5. Report

Report in the user's language:

- the input and the index state (`complete`, `synced_at`),
- a table of the duplicate and related candidates: key with URL, summary, status and resolution, verdict, and one line of evidence,
- a recommendation.

Recommendations:

- One or more duplicates: recommend that the user does not create the new issue. Recommend a comment on the existing issue instead, or a narrower new issue that states the difference.
- Related issues only: recommend that the new issue mentions them, for example in its Description.
- None: say that no duplicate was found in the top 20, and that the tool finds about 8 of 10 known duplicates. It is not proof that no duplicate exists.

## Rules

- Do not write to JIRA in this skill. Comments, links, and issue creation need the user's explicit approval through the `cubrid-jira` workflow.
- Do not block a JIRA write on this check. Report the result and let the user decide.
- You can run the check on internal drafts. The draft text stays on this computer.
