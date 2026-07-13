---
name: cubrid-oos-context
description: Load the authoritative CUBRID OOS (Out-of-row Overflow Storage) project context before answering, reviewing, debugging, testing, or implementing OOS work. Use whenever OOS is mentioned; on feat/oos or a derived branch; for OOS CBRD tickets; when touching OOS-related heap, vacuum, replication, recovery, file-manager, object-representation, or utility code; or when identifiers such as OR_MVCC_FLAG_HAS_OOS, OR_VAR_BIT_OOS, FILE_OOS, OR_OOS_INLINE_SIZE, oos_insert, oos_read, oos_delete, or heap_record_replace_oos_oids appear.
---

# CUBRID OOS Context

This skill loads context about the **OOS (Out-of-row Overflow Storage)** project — a CUBRID feature that separates large variable-length columns from heap records into dedicated OOS files to reduce unnecessary disk I/O.

$ARGUMENTS

## Step 0: Load the source of truth

Read the complete authoritative context before answering or taking action:

```bash
context_file="${CUBRID_OOS_CONTEXT_FILE:-/home/vimkim/gh/cubrid-oos-context/OOS-CONTEXT.md}"
test -r "$context_file"
```

Then read `$context_file` through EOF. Resolve relative links such as `docs/adr/...` against the directory containing that file and read the linked document when its decision or rationale is relevant.

If the file is missing or unreadable, stop and report the resolved path. Do not substitute remembered OOS facts, the summary from a previous turn, or the deleted quick reference from this skill.

`OOS-CONTEXT.md` is the normative specification and single source of truth for OOS. This skill is only its loader and usage policy; it must not duplicate thresholds, layouts, invariants, ticket states, milestone dates, or implementation status.

## Step 1: Validate the workspace when needed

Run the bundled validation script when the request involves source inspection, implementation, debugging, building, or testing:

```bash
bash <skill-path>/scripts/validate-env.sh "$PWD"
```

Do not run it for a documentation-only or conceptual question unless the answer requires checking the current implementation. The script checks that:

- You're in a **git repository** (or worktree) — needed for code search, grep, and git features
- The directory is a **CUBRID source tree** (has CMakeLists.txt + CMakePresets.json)
- **OOS source files** exist (oos_file.cpp — indicates you're on a feat/oos branch)
- **PRESET_MODE** is set and a **build directory** exists (build_preset_*)
- **compile_commands.json** is present at the project root — this is essential for LSP features (hover, goto-definition, find-references via clangd)
- **clangd** and **just** are available

**If the script reports errors (exit code 1):**
- Warn the user about what's missing and how to fix it
- If `compile_commands.json` is missing, tell the user to run `just build` (which generates it via CMake's `CMAKE_EXPORT_COMPILE_COMMANDS=ON`) and then symlink it: `ln -sf build_preset_${PRESET_MODE}/compile_commands.json .`
- If not in a git repo, suggest switching to a CUBRID worktree (e.g., one under `~/gh/cb/`)
- Continue any safe work that does not depend on the missing capability, and state the limitation

**If the script reports only warnings (exit code 0):**
- Note the warnings but proceed normally — the environment is usable

## Step 2: Check freshness and reconcile evidence

Treat volatile statements in the context file—ticket status, branch status, line numbers, milestone dates, and labels such as proposed, pending, open, or merged—as dated observations, not timeless facts.

When the request depends on current state:

1. Note the context file's `Last updated` date.
2. Check the current worktree branch and relevant source/history.
3. For a named CBRD ticket or live ticket status, use the `cubrid-jira` skill and consult `/home/vimkim/gh/my-cubrid-jira` as supporting local context.
4. Consult `/home/vimkim/gh/my-cubrid-docs` for newer OOS design notes, reviews, and verification reports before searching the web.

Use this authority and reconciliation rule:

- The normative context file is authoritative for required OOS behavior, terminology, layout, and invariants.
- The checked-out source is evidence of what that exact revision currently implements; it does not override the specification.
- JIRA is authoritative for current ticket workflow state.
- ADRs are authoritative for accepted decisions within their stated scope.
- Local reports and reviews are supporting evidence, not automatically accepted design.

If source and specification disagree, classify the difference as an implementation conformance gap unless the specification explicitly marks the behavior proposed, historical, or non-normative. State the conflict and identify the revision/date involved. Ask for clarification only when the specification itself is ambiguous or internally inconsistent.

## Step 3: Answer or act

- Distinguish current implementation, accepted design, proposed work, known defect, and historical behavior.
- Do not treat incomplete `feat/oos` implementation or temporary merge-readiness instrumentation as normative behavior.
- Use the terminology and writing conventions from the context file.
- Cite source functions, commits, tickets, or ADRs when they materially support a claim.
- Do not describe an experimental branch implementation as merged into `feat/oos` without verification.
- When asked to update OOS knowledge, edit the authoritative context repository rather than adding facts to this loader.
