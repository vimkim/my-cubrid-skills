# Artifact and publication workflow

Read this reference before choosing the report path. Use its publication steps after the saved report passes the review in `SKILL.md`. These are the existing artifact and publication rules; the triage rewrite does not expand their scope. Explicit requests for a local draft or another publication limit take precedence. Editing this skill or discussing issue-writing guidance is not a request to publish an issue.

## Artifact and output requirements

- **Save location**: `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-short-slug_<SHORT_SHA>_<AGENT>.md`. If the directory does not exist, **stop and tell the user** to clone/create the repo. Do NOT create it yourself. If no ticket number is known, ask whether one should be supplied; only after the user confirms this is a ticket-free draft, use `descriptive-slug_<SHORT_SHA>_<AGENT>.md`.
- **Characters**: use BMP text and no emoji for JIRA compatibility. Korean/CJK, box-drawing characters, ordinary typography, and ASCII forms are allowed when they aid readability. Follow the language, heading, and audience rules in `SKILL.md`.

## Automatic Completion Contract

A request that triggers this skill authorizes the complete workflow for an existing `CBRD-XXXXX` issue: write and review the report, commit only that report in `my-cubrid-jira`, push it to `origin/main`, and publish it as the matching live JIRA description through the `cubrid-jira` skill. Show previews for visibility, but do not pause for another confirmation.

Keep this authorization inside these exact boundaries:

- Require the local repository at `/home/vimkim/gh/my-cubrid-jira` to be on `main` with `origin` pointing to `github.com/vimkim/my-cubrid-jira` in HTTPS or SSH form.
- Preserve unrelated worktree and index changes. Stage and commit only the resolved issue file.
- Require the issue key derived from the filename to equal the JIRA target key.
- Push the Markdown commit successfully before the live JIRA update. If the push fails, stop before uploading.
- Use the `cubrid-jira` skill's publish-description workflow, including its dry-run, live update with `--yes`, and live read-back verification.
- If the live update fails after the push, keep the pushed commit, report the exact JIRA error and the partial-completion state, and do not claim success.

A ticket-free draft has no upload target. Save, review, commit, and push it like any other report, then report that only the JIRA upload was skipped. Creating a new JIRA issue is a separate workflow requiring the project, issue type, summary, and other required fields.

## Artifact Identity

Resolve the filename before writing the draft:

1. Set `SOURCE_COMMIT` to the specific CUBRID commit or PR head analyzed by the issue when one is supplied. Otherwise use `git rev-parse HEAD` in the current CUBRID worktree. Never use the `my-cubrid-jira` repository commit. If no relevant CUBRID commit or worktree can be identified, ask the user.
2. Validate `SOURCE_COMMIT` and take its first seven hexadecimal characters as `SHORT_SHA`.
3. Set `AGENT` from the active AI host's runtime identity. Use `codex` for Codex and `claude` for Claude Code. For another host, use its stable lowercase agent name. Do not infer the host from installed binaries because multiple AI CLIs may coexist; if runtime identity is unclear, ask the user.
4. Compute the output path once and reuse that exact file through revision and final handoff. The basename must end with `_<SHORT_SHA>_<AGENT>.md`.

For example, Codex documenting `f5794fb...` writes `CBRD-26972-oos-show-heap-capacity_f5794fb_codex.md`; Claude Code writes `CBRD-26972-oos-show-heap-capacity_f5794fb_claude.md`.

## Publish the reviewed report

1. Show an informational preview: report path, source commit, agent name, recommended JIRA type and categories, and the Issue Triage block. Follow any explicit user limit on publication; otherwise continue under the Automatic Completion Contract.
2. Validate the notes repository, remote, target key, and report against that contract. Preserve unrelated worktree and index changes.
3. Commit only the issue file and push it:

   ```bash
   issue_rel="issues/$(basename "$issue_file")"
   git -C /home/vimkim/gh/my-cubrid-jira add -- "$issue_rel"
   git -C /home/vimkim/gh/my-cubrid-jira commit \
     -m "docs(CBRD-XXXXX): add <short-slug> issue report" -- "$issue_rel"
   git -C /home/vimkim/gh/my-cubrid-jira push origin main
   ```

   If the intended file is already committed, skip the empty commit and still verify that `origin/main` contains it. Verify that the created commit contains only `issue_rel`; leave unrelated staged or untracked files untouched.
4. For a keyed report, hand off the matching ticket key and absolute `issue_file` to the `cubrid-jira` skill's publish-description workflow with delegated authorization for the live `--yes` update. It performs the dry-run, target check, update, and live read-back. Skip the upload only for an explicitly ticket-free draft or an explicit user publication limit.
5. Report the Markdown commit and pushed branch; for a keyed report, also report the live JIRA URL and read-back result. A keyed workflow is complete only when push and upload verification both succeed. Report the exact error and completed stages on failure. For a ticket-free draft, state that no JIRA target existed.
