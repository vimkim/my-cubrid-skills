# Publish reviewed material

Read this reference after the user confirms the saved draft and listed operations.
The Review and Publication Contract in `SKILL.md` governs authorization.

## Recheck the Review

For an interrupted attempt, first inspect completed operations using the retry
rules below before classifying remote differences as outside changes.

1. Locate the saved context and files, and inspect the actual source/docs worktrees,
   branches, remotes, and status. Read the context as data, never as executable shell
   input. If several drafts match a ticket, ask which one the user reviewed.
2. Establish the user's confirmation from the conversation. If it cannot be
   established in a resumed session, present the saved material and operations for
   confirmation. If it already applies, continue without asking again.
3. Reread the body and any explanation. A user's edits made before their confirmation
   are authoritative. Run the material checker without rewriting anything, verify
   the other writing conventions, and record content fingerprints for this attempt.
   On retry, compare with that attempt's fingerprints; do not replace them with
   hashes of changed files under the earlier confirmation.
   Recheck these before each remote write; if files change during publication,
   stop and return the changed material to review.
4. Require local source `HEAD` to equal `SOURCE_COMMIT`. Read the live remote head
   and compare it with the preparation snapshot (or a verified result of an approved
   source push). A source change requires reconciliation and another review.
5. For updates, fetch the exact PR's metadata and body again. Require the same
   repository, head/base branches, open/closed state, and draft/ready status.
   Compare the source revision with the recorded remote head before an approved
   push, and with `SOURCE_COMMIT` after it. Compare the decoded body fingerprint
   with the saved baseline or a verified result from this attempt. A changed
   GitHub body requires reconciliation with the local draft and another review;
   never silently overwrite it. If a title change is approved, check its original
   value too. For body-only updates, preserve any current title.
6. For creates, recheck for an existing PR matching the exact head repository/branch
   and base. An unexpectedly created PR changes the operation: present an update
   proposal for review rather than creating a duplicate or overwriting it.

If text needs changing, preserve the user's version, prepare the revised material,
and return to the review handoff. If the destination or operations differ from the
proposal, obtain confirmation of the revised proposal before remote writes.

## Execute Only the Confirmed Operations

Keep the PR body file available through the GitHub write and verification. Do not
remove its task worktree during docs integration.

### Documentation, when listed

Commit only intended files, preserving unrelated changes and staged entries.
Re-run the material checker before committing PR material. If publishing docs is
listed, inspect the outgoing commits and ensure they contain only the approved
scope. Validate the docs remote's push URL again.

Follow the local integration workflow: confirm the destination worktree is clean
and on the recorded integration branch, rebase the docs task branch onto it, inspect
and validate the result, and fast-forward merge from the destination worktree.
The publication confirmation covers these steps when they were listed. If resolving
a conflict changes reviewed body or explanation text, return that text to review.
Push the actual destination branch from the destination worktree; do not blindly
push `main` from a task worktree. Never force-push to resolve divergence.

For a linked explanation, verify its reviewed contents are accessible at the exact
public URL before writing the PR. Keep that URL unchanged in the approved body.
Body-only drafts can remain locally committed when docs publication was not listed.

### Source push, when listed

Recheck the local source revision, branch, and push remote against the proposal.
Push the approved source branch to the recorded repository and verify its remote
commit equals `SOURCE_COMMIT`. Record that result so the skill's own successful
push is not mistaken for an outside source change on retry. Skip an already
completed push; do not force-push or include unreviewed commits. A remote change
outside the verified approved operations returns to review.

### GitHub create or update

Immediately before the write, repeat the file fingerprints, material checker, and
applicable source/PR freshness checks. Use the persistent body directly with
`--body-file`; keep its contents and intentional newlines intact.
Require the published source head to equal `SOURCE_COMMIT`. If a necessary source
push was not in the confirmed proposal, return that operation for review first.

For creation, resolve these variables from the confirmed proposal. Use
`head_spec=vimkim:<branch>` for the personal fork, or the branch name alone when
the source is in the target repository; `gh` does not support an organization name
in the `<user>:<branch>` form. The default `vimkim` assignment must be listed in
the proposal along with creation:

```bash
gh pr create --repo "$target_repo" \
  --draft --base "$base_branch" --head "$head_spec" \
  --assignee vimkim --title "$proposed_title" --body-file "$body_file"
```

For an existing PR, identify it explicitly:

```bash
gh pr edit "$pr_number" --repo "$target_repo" --body-file "$body_file"
```

Add `--title "$proposed_title"` only when that title change was listed and approved.
Do not change the PR's base, head, assignees, or draft/ready status during a body update.

## Verify, Retry, and Finish

Fetch the resulting PR and compare its decoded body with the uploaded file; also
verify its target, source revision, title when applicable, and expected status.
Report the PR URL, completed operations, and any failure. Record the resulting PR
identity and published content fingerprints in the context; these are execution
results, not authorization for future changes.

If a command times out or partially succeeds, inspect actual remote state before
retrying. Recognize verified completed operations, including a PR created by this
attempt, and continue only unfinished operations with unchanged approved material.
An exact result can be recognized from remote state after an interrupted session;
uncertain provenance or a differing result requires reconciliation before mutation.
Do not create another PR, repeat successful writes, regenerate the body, or ask for
approval again solely because an unchanged authorized operation needs a retry.

Commit meaningful context updates locally. If docs integration was listed, include
these final execution-record commits in the approved local rebase/fast-forward
workflow; push them only if that push was also listed. Then follow the worktree
cleanup policy: verify the task tip is merged, preserve valuable files, and remove
only the merged task worktree and branch without force. If local integration was
not authorized, retain the worktree for review. Report any blocked cleanup and the
surviving body/context paths so reviewed material remains discoverable.
