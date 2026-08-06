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

1. Require an existing Markdown file and verify that its basename starts with the same issue key. Reject a mismatch rather than risking an update to the wrong issue.
2. Fetch the current issue with `cubrid-jira search TICKET_ID` to verify that the target exists and to record what will be replaced.
3. Run the default dry-run and inspect its resolved target:

   ```bash
   cubrid-jira update TICKET_ID \
     --description-file ISSUE_FILE \
     --from markdown \
     --output json
   ```

4. If publication is authorized and the dry-run target is correct, perform the live update without pausing:

   ```bash
   cubrid-jira update TICKET_ID \
     --description-file ISSUE_FILE \
     --from markdown \
     --yes \
     --output json
   ```

5. Verify the live result with `cubrid-jira search TICKET_ID`. Report the issue URL and the update result.

Without explicit or delegated authorization, stop after the dry-run and ask before adding `--yes`. If any command fails, report the exact error and do not claim that the issue was uploaded.

$ARGUMENTS
