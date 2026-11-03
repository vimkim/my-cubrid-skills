---
name: cubrid-jira
description: Look up CUBRID JIRA issue context and publish a reviewed Markdown file as an existing issue's description. Use when a CBRD-XXXXX ticket is mentioned, when the user asks about a JIRA issue, or when another authorized workflow needs to upload a finished issue report.
---

Read or update CUBRID JIRA issues with the `cubrid-jira` CLI.

## Preflight

Verify `cubrid-jira` exists in PATH by running `command -v cubrid-jira`. If it does not exist, halt immediately and tell the user:

```text
Error: `cubrid-jira` is not installed.

Install it:
    uv tool install git+https://github.com/vimkim/cubrid-jira
```

Require a concrete issue key such as `CBRD-25123`. If none is available, ask for one.

## Read an issue

Run:

```bash
cubrid-jira search TICKET_ID
```

Present the output as-is. Search contacts JIRA by default and refreshes the local cache. If the command fails after preflight, report the exact error rather than guessing.

## Publish a Markdown description

Use this mode only when the user explicitly asks to upload the specified issue report, or when a calling skill states that its triggering request pre-authorizes publication. Do not request another confirmation in the pre-authorized case.

Read [Links in shared material](../cubrid-common/references/shared-links.md),
including for direct uploads that did not use the issue writer. Resolve
`link_checker` to `../cubrid-common/scripts/check-shared-links.py` relative to this
skill. Validation is read-only; report failures and return necessary changes to
review rather than rewriting an approved file.

1. Require an existing Markdown file. Extract the complete leading issue key with `^([A-Z][A-Z0-9]*-[0-9]+)(?=[_.-]|$)` and require exact equality with the target key. For example, `CBRD-12345` must not match a file for `CBRD-123456`. Reject a missing key or mismatch. Run `python3 "$link_checker" ISSUE_FILE` on that exact file and stop on failure.
2. Fetch the current issue with `cubrid-jira search TICKET_ID` to verify that the target exists and record its summary and description. This workflow replaces only the description. A local title heading is a proposed title or description heading; changing the live summary requires separate explicit authorization and a summary-field update workflow.
3. Run the default dry-run, inspect its resolved target and converted description, and retain that converted payload for verification:

   ```bash
   cubrid-jira update TICKET_ID \
     --description-file ISSUE_FILE \
     --from markdown \
     --output json
   ```

4. If publication is authorized and the dry-run target is correct, rerun `python3 "$link_checker" ISSUE_FILE` immediately before the live update and stop on failure. If it passes, perform the live update without pausing:

   ```bash
   cubrid-jira update TICKET_ID \
     --description-file ISSUE_FILE \
     --from markdown \
     --yes \
     --output json
   ```

5. Read the live description with `cubrid-jira search TICKET_ID` and compare it with the approved dry-run converted payload. Allow only documented normalization, not missing or changed content. If search exposes only rendered text, compare headings, links, tables, code blocks, and meaning as applicable, and report that raw payload equality was not verified. Report the issue URL and comparison result. A mismatch is partial completion. Report the differences without silently rewriting the approved file or claiming publication is verified.

Without explicit or delegated authorization, stop after the dry-run and ask before adding `--yes`. If any command fails, report the exact error and do not claim that the issue was uploaded.

$ARGUMENTS
