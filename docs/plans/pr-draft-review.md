# Review PR material before publication

Status: implemented and validated on `skill/pr-draft-review`; awaiting review for
local integration and separate installation/publication authorization.

The user wants `cubrid-pr-create` to save the proposed PR body as Markdown in
`my-cubrid-docs`, allow human review and editing, and publish only after confirmation.
This applies to creating a PR and updating an existing PR's description.

## Accepted decisions

- Save the exact PR body as a persistent Markdown file. A detailed explanation is
  optional, warranted by the complexity of the change. The user reviews every
  document that will be published.
- Present the publication operations alongside the draft. One explicit
  confirmation authorizes that listed bundle, including necessary source and
  documentation pushes when listed. A description-only update does not authorize
  a source push.
- Update an existing PR's body by default. Change its title only when that title
  change was explicitly presented for review. Preserve its draft/ready status.
- When the user edits a saved draft and confirms publication, their confirmation
  covers the file's current contents. Reread and validate that file, then publish
  it unchanged. A validation failure requires an explanation; any agent rewrite
  returns to the user for review.
- Support resuming in a later session. Save a companion context file with the
  source commit, target PR or branches, proposed title, and intended publication
  operations. Keep this metadata out of the PR body. The presence of a saved draft
  or context file never constitutes publication approval.
- A source commit change or an edit to the existing description on GitHub requires
  reconciliation and another review before publication. Start existing-PR drafts
  from the current GitHub description and preserve manual content unless the
  requested revision changes it.

## Agreed workflow

1. Gather source and PR context, identify create versus update, and prepare the
   saved PR body in a `my-cubrid-docs` task worktree. Prepare a detailed explanation
   when warranted and save the companion context needed to resume.
2. Validate the material and present file links, the proposed title, publication
   target, and exact operations. End preparation here for human review.
3. Accept user edits and explicit publication confirmation. Reread the saved
   files, validate them without rewriting, and recheck the source and remote PR.
4. If the review remains current, execute only the listed and approved operations.
   Create a draft PR or update the identified existing PR using the saved body
   directly. Preserve the existing PR's status and any unapproved title.
5. Verify the published result and report its URL. An unchanged retry uses the
   existing authorization; a changed target, expanded operation list, or revised
   material returns to review.

## Implementation and verification scope

- Keep one `cubrid-pr-create` skill with preparation and confirmed-publication
  phases. Preserve existing language, title, and body-section conventions.
- Replace all automatic-publication instructions consistently and make detailed
  explanation generation and linking conditional.
- Use persistent Markdown paths following existing ticket, source-commit, and
  agent naming conventions. Keep the PR body suitable for direct `--body-file`
  use and separate from resume context.
- Respect the repository worktree and local merge workflow; distinguish local
  task commits from remote publication, and list any necessary merge/push steps
  in the publication proposal.
- Validate skill structure and exercise the material checker with body-only and
  body-plus-detail inputs, including invalid material. Review the workflow against
  creation, update, user edits, resumed publication, stale review, and retry cases.
- Make the skill-source edits in the sibling topic worktree and prepare them for
  review. Installation sync, repository push, and local integration remain subject
  to the applicable completion workflow.

## Prior implementation

The prior skill authorized automatic publication in its description, contract,
execution steps, and document-review completion rule. It stored the PR body in a
temporary file, required a detailed explanation for every PR, and lacked an explicit
existing-PR update procedure. These rules were replaced consistently.

The bundled material checker already accepts a persistent body file and does not
modify it. Existing Markdown body files in `my-cubrid-docs` provide a naming precedent.

## Verification

Validated on 2026-10-06 without GitHub writes or installed-skill changes:

- Skill frontmatter and scaffold validation passed with the bundled
  `quick_validate.py`, using `/usr/bin/python3` with its existing PyYAML package.
- Bash syntax checks passed for the checker and documented Bash command blocks.
- The documented material-check invocation passed ten temporary-fixture cases:
  body only, body with explanation, local path in body, local path in explanation,
  personal task-runner recipe, extra body section, missing section, wrong section
  order, missing explanation file, and missing body file. Valid inputs passed;
  invalid inputs failed. Existing input bytes remained unchanged in every case.
- Relative documentation links and whitespace checks passed. Local `gh` help
  confirmed the create, explicit-PR edit, body-file, and JSON field interfaces.

The following workflow cases were reviewed against the instructions; these are
manual contract checks, not live end-to-end GitHub tests:

| Case | Required result covered by the revised workflow |
| --- | --- |
| New PR request | Save body/context and stop for review before remote writes. |
| Simple change | Prepare body/context without requiring an explanation or link. |
| User edits then confirms | Read, validate, and upload the current file unchanged. |
| Approved text fails validation | Explain the failure and return any agent revision to review. |
| Resume with or without prior confirmation | Reuse established permission; otherwise request confirmation of the saved proposal. |
| Source revision or remote description changes | Preserve drafts, reconcile changes, and require another review. |
| Existing PR body update | Start from its current body; preserve status and any unapproved title. |
| New PR appears during review | Present the changed operation for review instead of creating a duplicate. |
| Source or GitHub write times out after success | Inspect and recognize the completed result; retry only unfinished approved operations. |
| Docs task worktree publishes an explanation | Integrate the reviewed content before pushing the destination branch, retain the body through the PR write, and clean up only merged work. |
