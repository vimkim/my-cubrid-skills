# JIRA writing skill revision

## Decision

The user requested a design discussion before revising `cubrid-jira-issue-write`,
starting from `/home/vimkim/tmp/handoff-jira-background-first-yeo6_h5p.md`.
The final direction agreed on 2026-10-01 is:

- Simplify accumulated writing corrections, retaining essential workflow constraints
  and a small set of useful writing principles.
- Preserve the team's required opening fields: 목적, 이유, 영향, 이슈 수행 방안.
- Preserve the explicit `AI-Generated Context` divider below those fields.
- Keep a summary of 이유 above the divider. Below it, explain the background and
  causes in detail; repeating and expanding the summary is allowed.

The initial suggestion to remove the fixed fields and divider was superseded by the
user's clarification that the team leader requires them. Background-first writing
therefore governs the detailed explanation, while the opening remains a summary.

The motivation for simplifying the skill is the user's experience that improved
models need less corrective instruction. This is a design preference informed by
experience, not a measured claim about model accuracy.

## Changes

The revision removes the fixed 10-second reading target, absolute cross-layer
fact-deduplication rule, and accumulated sentence-level correction lists. A concise
set of writing principles replaces them. The structure, drafting steps,
and review criteria all allow summary followed by detailed explanation.
Worked issue examples and the reference-issue catalog are removed from the skill,
following the user's request to rely on the model's existing writing capability.
The local sample remains a verification artifact outside the skill.

The workflow still preserves artifact naming, storage, language and character
constraints, target verification, and the existing publication procedure. Existing
JIRA issues are reference material; this task does not publish or revise them.

These are reversible editorial choices, so a separate architecture decision record
and a project glossary are unnecessary.

## Verification

The [local sample](jira-writing-sample.md) rewrites the opening and background of
CBRD-27539 using the saved issue and the user's clarification. It is a review
artifact, not a complete replacement report or publication target. It demonstrates
four visible top fields, an explicit divider, and repeated reasons developed into
an explanation below it. Historical details are attributed to the saved report;
this task does not independently re-audit CUBRID source history.

Validation covers skill frontmatter, whitespace, unchanged operational sections,
and manual comparison of the revised guidance and sample. This supports the
editorial change; it does not establish behavior across different models or future
issues.

Checks passed using the skill-creator validator in an isolated `uv` environment
with PyYAML, `git diff --check`, and a comparison confirming that Hard Constraints,
Automatic Completion Contract, Artifact Identity, Issue Types, and publication
steps are unchanged. The sample passes the four-field, character, heading, and
portable-command checks and was read against the revised criteria.
