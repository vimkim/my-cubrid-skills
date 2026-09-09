---
name: my-cubrid-skills-create
description: "Create a new skill in the my-cubrid-skills collection. Use when the user wants to turn a workflow into a reusable skill, capture what they just did as a skill, or add a new skill to their CUBRID toolbox. Triggers on phrases like 'make this a skill', 'create a skill for this', 'save this as a skill', 'add a new skill to my-cubrid-skills'."
argument-hint: "<skill-name-or-description>"
---

# Create a New Skill in my-cubrid-skills

Scaffolds a new skill directory and writes a complete `SKILL.md` inline from gathered context.

## Steps

### Step 1: Determine the collection root

Walk up from cwd looking for a `justfile` containing `npx skills add`. If found, that directory is the collection root. Otherwise ask the user for the path.

### Step 2: Derive a candidate skill name

If `$ARGUMENTS` is empty, or would produce an empty or tautological name (e.g. `"save this as a skill"` collapses to nothing after filler removal), skip naming for now and proceed to Step 4 to gather workflow context first — then derive the name from the workflow's primary verb + object.

Otherwise, from `$ARGUMENTS`:

- Drop filler words: `a`, `the`, `this`, `that`, `which`, `skill`, `save`, `as`.
- Convert verbs to imperative form and lowercase-hyphenate — e.g. `"a skill that closes greptile comments"` → `close-greptile-comments`.
- Apply the `cubrid-` prefix when the skill touches CUBRID source, tests, JIRA tooling, or CI. The prefix rule applies even when the input is already kebab-case.

**Propose** the candidate name and wait for confirmation or correction before continuing.

### Step 3: Check for conflicts

Confirm `<collection-root>/<skill-name>/` does not already exist. If it does, ask: update the existing skill, or pick a different name?

### Step 4: Gather context

From the current conversation collect:
- **Workflow**: the sequence of commands, tools, or actions the skill automates
- **Tools**: CLI tools, APIs, or Claude skills involved
- **Edge cases**: failure modes or conditions the user mentioned

If Step 2 was deferred, derive the skill name now from the workflow's verb + object, confirm with the user, then run Step 3's conflict check before continuing.

### Step 5: Write the SKILL.md

Create `<collection-root>/<skill-name>/SKILL.md` with complete content — no placeholder comments. Follow the valid skill structure below.

Note: `SKILL.md` is installed to both Claude Code and Codex via `just install`. Use `$ARGUMENTS` for input; avoid Claude-Code-only constructs unless explicitly flagged.

### Step 6: Validate the SKILL.md

Review the saved file in the current session against the workflow gathered in Step 4 and the valid skill structure below:

- Description and concrete trigger phrases match the intended scope.
- Steps are executable, reference exact CLI commands where needed, and handle the known edge cases.
- Frontmatter and naming are valid; the CUBRID prefix is applied where relevant.
- Instructions work for Claude Code and Codex, with any harness-specific behavior explicitly identified.
- The file contains no placeholders or `<!-- ... -->` comments.

Correct defects in place and run appropriate source-level checks for supporting scripts or assets. Ask a concise clarification only for a decision or required input that the conversation and local sources cannot resolve.

Use an independent reviewer only when the user requests one; provide the saved file, workflow context, and these criteria, and request concrete findings. A design interview is a separate user-requested activity, not an installation prerequisite.

### Step 7: Confirm publication, reinstall, and verify

After validation, ask whether to reinstall the skills and commit and push the intended repository changes, as required by the collection's `AGENTS.md`. Run only the publication actions explicitly authorized by the user.

For an authorized reinstall, run from the collection root:

```bash
just reinstall
just list
```

Verify that the frontmatter `name:` appears for both Claude Code and Codex. For an authorized commit and push, inspect the diff and staging area, include only the intended skill files, and preserve unrelated changes. Match the commit scope to the style of `git log --oneline -10`, push to the intended repository branch, and report the result.

## Valid skill structure

- Frontmatter: `name` (kebab-case) and `description`.
- `description`: imperative phrase, "Use when …", ends with `Triggers on phrases like 'X', 'Y', 'Z'.`
- Body: `# Title` heading and numbered execution steps.
- No placeholders or `<!-- ... -->` comments in the final file.

Real examples: `resolve-greptile-comments/SKILL.md`, `cubrid-pr-create/SKILL.md`.
