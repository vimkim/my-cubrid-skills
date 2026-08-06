---
name: cubrid-code-analysis-report
description: "Produce an evidence-backed Korean HTML book that reconstructs a CUBRID subsystem from local source, compares its nearest PostgreSQL and MySQL mechanisms, validates central behavior with CUBRID experiments, creates reproducible Korean quizzes, and finishes with an adaptive Korean mastery grill. Use for a free-form CUBRID topic such as page buffer, vacuum, lock manager, logging, recovery, or query execution when the reader needs a source-traceable conceptual and behavioral reimplementation blueprint. Triggers on phrases like 'analyze CUBRID page buffer', 'write a deep CUBRID vacuum report', 'compare this CUBRID module with PostgreSQL and MySQL', 'CUBRID code analysis report', or 'create a CUBRID subsystem report and grill me'."
---

# CUBRID Code Analysis Report

Build an offline, multi-page Korean HTML book from three pinned local source trees. Treat the report as a source-derived conceptual and behavioral reimplementation blueprint within an explicit scope, not as an unprovable promise of ABI, on-disk, timing, or bit-for-bit compatibility.

## Fixed Contract

- Accept one required free-form topic and an optional exact output directory. A focus request may add emphasis but never remove mandatory coverage.
- Treat the current Git worktree as the CUBRID source only after validation.
- Default PostgreSQL to `/home/vimkim/gh/pg/postgres`, MySQL to `/home/vimkim/gh/mysql/mysql-server`, and the docs root to `/home/vimkim/gh/my-cubrid-docs`.
- Write final HTML, quiz prose, answers, and live grilling in Korean. Preserve English technical terms, code identifiers, SQL, scripts, commands, paths, and raw research notes.
- Compare both PostgreSQL and MySQL on every topic. Choose the nearest mechanism and label `equivalent`, `partial analogy`, or `no equivalent`; never force symmetry.
- Require CUBRID runtime experiments. Treat instrumentation as conditional. PostgreSQL/MySQL servers are never quiz or experiment dependencies.
- Use parallel research roles when the host supports agents; execute the same role checklists sequentially otherwise.
- Use the main agent as the only final-book writer and the only owner of CUBRID source mutations.
- Finish with a live grill that asks exactly one Korean question per user turn. Static quizzes do not replace the live grill.

## Required Resources

Before acting, read these files completely:

1. `CONTEXT.md` for the exact domain language used by this workflow.
2. `references/research-and-evidence.md` for source tracing, comparison, claim IDs, and provenance.
3. `references/report-contract.md` for the Korean book schema and reimplementation standard.
4. `references/experiments-and-safety.md` for runtime evidence and reversible instrumentation.
5. `references/quiz-and-grill.md` for reproducible quiz artifacts and the mastery state machine.
6. `references/agent-roles.md` before delegating any research or audit work.
7. `references/artifact-schemas.md` for exact JSON contracts enforced by `reportctl.py`.

Use `scripts/reportctl.py` as the single deterministic interface for report initialization, command capture, and verification. Use `assets/report.css` unchanged unless a topic has a demonstrated presentation need that the stylesheet cannot express.

## Execution Steps

### Step 1: Parse the Request

Require exactly one primary topic. Accept natural language, `$cubrid-code-analysis-report <topic>`, or a host slash-command equivalent. Do not rely on slash-command availability.

- If the topic is empty, ask for it and stop.
- If independent topics are listed, ask whether one is primary or a combined scope is intended.
- Treat `--output <absolute-directory>` as an exact report directory. Reject relative paths and HTML filenames.
- Ask only when ambiguity would materially change the module boundary. Discover facts from local files instead of asking.
- Determine the active agent from runtime identity (`codex`, `claude`, or another stable lowercase name). Do not infer it from installed binaries; ask if unclear.

### Step 2: Validate and Initialize

Resolve the skill directory and run:

```bash
python3 "<skill-dir>/scripts/reportctl.py" init \
  --topic "<topic>" \
  --cubrid-root "$PWD" \
  --postgres-root /home/vimkim/gh/pg/postgres \
  --mysql-root /home/vimkim/gh/mysql/mysql-server \
  --agent "<agent>"
```

Add `--output "<absolute-directory>"` only when explicitly requested. Parse the JSON response and keep its `report_dir` unchanged for the entire run.

The initializer must prove all three project remotes and source roots; capture commits, dirty fingerprints, OS, build environment, and tool identities; and refuse an identity collision. If it reports an existing matching report, resume it without overwriting completed content. Surface any other failure and stop.

Read all applicable `AGENTS.md` or `CLAUDE.md` files. Search `/home/vimkim/gh/my-cubrid-docs` before web search for CUBRID context. Search `/home/vimkim/gh/my-cubrid-jira` when the topic or local notes mention a CBRD ticket. Compose topic-specific skills when they trigger; OOS work, for example, must load `cubrid-oos-context`.

### Step 3: Freeze Scope and Questions

Write `research/scope.md` before deep tracing. Define:

- the topic in one sentence;
- included code, dependency seams, callers, and neighboring modules;
- explicitly excluded behavior;
- the shared scenario used across all three databases;
- the questions every chapter must answer;
- a coverage matrix for every obligation in `report.json`.

Hash `research/scope.md`, set `report.json.scope.frozen=true`, and never narrow it merely to obtain readiness. Declare every central mechanism in `report.json.central_behaviors` using `references/artifact-schemas.md`; each must map Claims, Coverage Obligations, Experiments, Quizzes, Book anchors, and Live Grill concepts.

Use the deep-module vocabulary consistently:

- **Module**: the behavior under study.
- **Interface**: every caller obligation, including invariants, ordering, errors, configuration, and performance.
- **Seam**: where behavior can vary without editing the caller.
- **Implementation**: the code behind the Interface.

When the source reveals that the original topic crosses multiple Modules, update the scope explicitly. Do not silently expand until the report becomes an unbounded tour of the engine.

### Step 4: Gather Evidence

When agents are available, launch the read-only roles in `references/agent-roles.md` in parallel. Give each role the topic, scope, immutable roots/commits, evidence schema, and only the role-specific task. Agents return evidence packets; they do not write final HTML or modify source.

Whether parallel or sequential:

1. Trace CUBRID end to end: entry points, callers, Interfaces, data ownership, lifetimes, state transitions, fast/slow/error paths, concurrency, persistence, recovery, configuration, observability, and shutdown.
2. Trace the nearest PostgreSQL mechanism on the same comparison axes.
3. Trace the nearest MySQL mechanism, naming the concrete storage engine such as InnoDB when responsibility lives there.
4. Resolve disagreements by reopening primary source. Agent consensus is not evidence.
5. Record every substantive claim in `evidence/claims.jsonl` using `references/research-and-evidence.md`.

Use `rg` or `rg --files` for discovery. Read complete functions and reachable call paths around matches. A symbol-name match alone never proves behavior. Record negative-search scope for claims that something does not exist.

### Step 5: Plan and Run Experiments

Create at least one reproducible CUBRID runtime experiment for every central behavior class that can be observed safely. Each experiment uses:

```text
Question -> Hypothesis -> Setup -> Action -> Observation
-> Interpretation -> Alternative explanations -> Cleanup
```

Store it under `experiments/experiment-N/`. Capture every build, command, and quiz run through:

```bash
python3 "<skill-dir>/scripts/reportctl.py" record \
  --report-dir "<report-dir>" \
  --id "<stable-run-id>" \
  --cwd "<absolute-cwd>" \
  --expect-exit 0 \
  --runtime-tools-snapshot "evidence/runtime-tools-<stage>.json" \
  -- <command> <arg> ...
```

Use `--runtime-tools-snapshot` for Experiment and Quiz observation runs; omit it for the build that creates the snapshot. The command after `--` is an argv vector, not shell syntax. Put pipes, redirection, environment setup, and multi-step logic in separately captured scripts.

Before any runtime Experiment, perform this mandatory build/identity gate even when instrumentation is not used:

1. Capture `just build` as `runtime-baseline-build` from the pinned CUBRID root.
2. Stop on a nonzero build.
3. Run `reportctl.py runtime-snapshot --report-dir "<report-dir>" --id baseline --build-run-id runtime-baseline-build`. It resolves tools through the pinned worktree's `direnv` environment; rejects `csql`, `cubrid`, `cub_server`, or `cubrid_rel` outside that environment's absolute `$CUBRID` install root; and captures `cubrid_rel` release output.
4. Bind `report.json.runtime.runtime_build_run_id`, `baseline_tools_snapshot`, and `active_tools_snapshot` to that evidence.
5. Start Experiment runs only after the snapshot timestamp.

The v1 verifier accepts a mandatory observation run only when its exact `runner_argv` directly executes the captured `csql` binary with a hashed SQL input through `-i` or `--input-file`. `cubrid` may be used in separately captured setup/cleanup commands. A shell wrapper may prepare owned resources, but merely naming `run.sh` in another command or self-attesting that it called CUBRID is not runtime proof. Capture setup and cleanup separately.

Give every experiment a hashed runner, `manifest.json`, `expected-oracle.md`, central-behavior/Claim links, controls, alternative explanations, repetition count, and cleanup result using `references/artifact-schemas.md`.

Try SQL, existing utilities, logs, counters, debugger observation, and unmodified runtime behavior first. If a named evidence gap remains, follow `references/experiments-and-safety.md` exactly for temporary logs/assertions and `just build`. Capture separate `instrumented` and `post-clean` runtime snapshots after their distinct builds. A baseline build failure, overlapping user edit, unexpected file change, failed cleanup, or failed post-clean rebuild is a hard stop.

### Step 6: Synthesize the Korean Book

Generate an offline multi-page book unless a genuinely narrow topic is clearer as one page. Even a single-page report must satisfy every coverage obligation or give an evidence-backed `Not applicable` explanation.

- Use `index.html` as the reading map and provenance summary.
- Put chapters in `chapters/` and shared local resources in `assets/`.
- Use `assets/report.css`; do not use CDNs, remote fonts, Mermaid, or network-dependent scripts.
- Prefer HTML/CSS diagrams, inline SVG, tables, timelines, and state machines when relationships are easier to understand visually. Every diagram needs a Korean text alternative and claim IDs.
- Explain each topic in layers: intuition -> concrete scenario -> exact mechanism -> invariants/failures -> design comparison -> reimplementation blueprint.
- Define every CUBRID-specific term on first use. Assume second-year university CS knowledge, not prior DBMS-internals knowledge.
- Keep source citations near claims, but make the explanation stand alone when the source link is closed.
- Mark direct source facts, runtime observations, inferences, unknowns, and semantic analogies distinctly.

Follow every chapter and readiness rule in `references/report-contract.md`. Never declare `READY WITHIN DECLARED SCOPE` while a required behavior says only “read the source,” while a central claim is unsupported, or while compatibility limits are hidden.

### Step 7: Build and Execute Quizzes

Create contiguous `quiz/quiz-1`, `quiz/quiz-2`, and so on. Every directory contains:

- Korean `quiz.md`;
- Korean `answer.md`;
- at least one reproducible `.sql`, `.sh`, or other executable script;
- any setup, cleanup, expected, or raw-output files that genuinely help reproduction.

Treat `references/quiz-and-grill.md` as the authoring prompt. Keep the Quiz useful and reproducible without forcing bookkeeping that adds no teaching value. Run it enough to trust the supplied answer; a `quiz.json`, captured run receipt, repeated run, or separate setup/cleanup script is optional when it materially improves the artifact. Quiz scripts may require CUBRID only. Never reveal the answer in the question or script comments.

### Step 8: Audit the Draft

Ask a fresh reviewer agent, when available, to audit the raw report directory without receiving the intended conclusion. The reviewer checks the report contract, claim ledger, three-database mappings, experiments, Korean pedagogy, quizzes, source restoration, and reimplementation readiness.

Require a final line exactly `VERDICT: APPROVED` or `VERDICT: REVISE`. On `REVISE`, fix every numbered item and repeat up to five rounds. If no valid verdict is returned, reprompt once; stop rather than self-approve if it remains malformed. Research-agent unavailability permits sequential research, but an isolated Completeness Audit is mandatory; if the host cannot isolate a reviewer, leave the run `DRAFT` and stop.

Set `report.json.status=REPORT_READY`. Run `reportctl.py materials --phase report`, give that exact digest set to the approved reviewer, and save `evidence/report-audit.md` plus its `report-audit.json` seal using `references/artifact-schemas.md`.

Treat reviewer isolation as an operational host boundary: the seal proves exactly which files a declared reviewer approved, but a report-authored `isolated_reviewer=true` boolean is not cryptographic proof of independence. Preserve a host task/reviewer receipt when the host exposes one; otherwise state this limitation honestly.

Run the report-phase verifier:

```bash
python3 "<skill-dir>/scripts/reportctl.py" verify \
  --report-dir "<report-dir>" \
  --phase report
```

Fix every failure. Structural success does not override an auditor rejection or weak content.

### Step 9: Conduct the Live Grill

After the report phase passes, follow the state machine in `references/quiz-and-grill.md`.

- Ask exactly one Korean question per turn.
- Start from the learner's mental model, then cover Interface, core lifecycle, concurrency, durability/failure, performance trade-offs, experiments, and PostgreSQL/MySQL differences.
- Do not show the answer before evaluating the learner's response.
- Split misconceptions into smaller causal questions and point back to a chapter or quiz after repeated difficulty.
- If the learner finds a report defect, return to evidence gathering, revise the book, re-audit it, and then resume.
- Require a final end-to-end teach-back before mastery.

Persist the grill under `grill/` so it survives host turns. If the user pauses, mark the report `GRILL_PAUSED`; do not claim completion.

### Step 10: Final Verification and Handoff

After mastery, set `report.json.status=COMPLETE`. Run a fresh isolated complete audit over the report plus the actual grill artifacts, save `evidence/complete-audit.md` and `complete-audit.json`, then run:

```bash
python3 "<skill-dir>/scripts/reportctl.py" verify \
  --report-dir "<report-dir>" \
  --phase complete
```

Recheck all three HEADs, dirty fingerprints, cited-file hashes, experiment evidence, quiz evidence, instrumentation markers, and the clean-binary rebuild. If any identity or evidence changed, return only the affected portion to research and audit.

Report the saved `index.html`, readiness declaration, experiment count, quiz count, auditor verdict, grill mastery summary, unresolved unknowns, and source-restoration status. Never install skills, commit, push, publish, or modify GitHub as part of this analysis workflow.

## Hard Stops

Stop and report exact evidence when any of these occurs:

- a source root or repository identity is wrong;
- the report directory conflicts with different provenance;
- a pinned revision changes during the run;
- a central comparison cannot be supported from local source;
- an experiment would touch a user-owned database/service without authority;
- instrumentation overlaps existing edits or cannot be removed exactly;
- the restored-source build fails or an instrumented process remains;
- mandatory runtime behavior cannot be reproduced;
- report, quiz, audit, or complete-phase verification fails after the allowed revision loop.

Research-agent unavailability is not a hard stop; run the research roles sequentially. Inability to perform an isolated Completeness Audit is a hard stop.
