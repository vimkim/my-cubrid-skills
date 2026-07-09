---
name: cubrid-jira
description: Look up CUBRID JIRA issue context. Use when a CBRD-XXXXX ticket is mentioned or when the user asks about a JIRA issue.
argument-hint: <CBRD-XXXXX>
---

Look up CUBRID JIRA issue context.

Given a JIRA ticket ID (e.g., CBRD-25123), fetch the issue details from the CUBRID JIRA REST API and present a comprehensive summary. The argument is the ticket ID.

If no ticket ID is provided, ask for one.

$ARGUMENTS

Steps:
1. Verify `cubrid-jira` exists in PATH by running `which cubrid-jira`. If it does not exist, **halt immediately** and tell the user:

   ```
   Error: `cubrid-jira` is not installed.

   Install it:
       uv tool install git+https://github.com/vimkim/cubrid-jira
   ```

2. Use the Bash tool to run:

   ```
   cubrid-jira search TICKET_ID
   ```

3. Present the output to the user as-is. The command searches local cache first and fetches from JIRA if missing, outputting readable markdown.
4. If the command fails after a successful preflight, the JIRA instance is likely unreachable — report the exact error to the user rather than guessing.
