---
name: my-cubrid-skills-create
description: "Create a new CUBRID-related skill in the my-cubrid-skills collection. Use when the user wants to turn a workflow into a reusable skill, capture what they just did as a skill, or create a new skill for their CUBRID toolbox. Triggers on phrases like 'make this a skill', 'create a skill for this', 'save this as a skill', 'add a new skill to my-cubrid-skills'."
argument-hint: "<skill-name-or-description>"
---

# Create a New CUBRID Skill

This skill creates new skills in the `my-cubrid-skills` collection at `/home/vimkim/temp/my-cubrid-skills/`, which can later be installed via `npx @anthropic-ai/claude-code-skills`.

## Instructions

1. **Determine the skill name and purpose** from `$ARGUMENTS` and conversation context. If the user says "make what I just did as a skill", extract the workflow from the current conversation history — the tools used, the sequence of steps, commands that worked, and corrections the user made.

2. **Create the skill directory** at `/home/vimkim/temp/my-cubrid-skills/<skill-name>/`.

3. **Invoke `/skill-creator`** with the target path to handle the full skill creation workflow (drafting SKILL.md, writing test cases, evaluation, iteration):

   ```
   /skill-creator /home/vimkim/temp/my-cubrid-skills/<skill-name>
   ```

   Pass along all context you've gathered — the workflow steps, commands, edge cases, and any user preferences.

4. After the skill is created, remind the user they can install it with:
   ```bash
   just install
   ```

## Conventions

- Skill names should be kebab-case (e.g., `resolve-greptile-comments`)
- Follow the same structure as existing skills in the directory
- CUBRID-specific skills should reference `gh` CLI for GitHub operations where applicable
- Keep skills focused — one workflow per skill
