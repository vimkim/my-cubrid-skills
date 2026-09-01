---
name: cubrid-code-survey
description: "Survey one CUBRID mechanism against its nearest PostgreSQL and MySQL implementations, then answer narrow runtime questions with focused reversible CUBRID probes. Use for cross-database source comparison, a traced CUBRID call path, or lightweight logging/probe validation. Triggers on phrases like 'survey CUBRID vacuum', 'compare this CUBRID code with PostgreSQL and MySQL', 'trace this CUBRID mechanism', or 'probe this CUBRID code path'."
---

# CUBRID Code Survey

Answer one concrete CUBRID mechanism question with a concise, source-traceable PostgreSQL/MySQL survey and the smallest useful CUBRID runtime observation. The deliverable is one Markdown note and, only when reproduction requires it, one small runner.

## 1. Frame the Question

1. Require one primary mechanism or behavior question. If the request spans independent mechanisms, ask which one is primary.
2. Define one shared scenario that can be followed through all three databases. Compare only the axes relevant to that scenario.
3. Treat the current Git worktree as CUBRID after checking its repository identity and source markers. Default the comparison roots to `/home/vimkim/gh/pg/postgres` and `/home/vimkim/gh/mysql/mysql-server`; require both to be valid Git source trees.
4. Record each tree's absolute root and full `HEAD`. Record the CUBRID branch and worktree status; cite dirty source as `WORKTREE` rather than pretending it matches `HEAD`.
5. Search `/home/vimkim/gh/my-cubrid-docs` before external sources for CUBRID context. Search `/home/vimkim/gh/my-cubrid-jira` when a CBRD ticket is part of the request or local notes.
6. Treat `--output` as an exact absolute `.md` path. Otherwise write `/home/vimkim/gh/my-cubrid-docs/code-surveys/<topic-slug>/<cubrid-short-sha>.md`.

Finish this step when the question, scenario, roots, revisions, and output path are explicit.

## 2. Trace the Three Implementations

1. Trace the CUBRID path from the scenario's entry point through the responsible functions. Read complete functions and reachable callers/callees around matches; identifiers and comments are leads, not evidence.
2. Trace the nearest PostgreSQL mechanism along the same relevant axes.
3. Trace the nearest MySQL mechanism and name the responsible storage engine, such as InnoDB, when ownership lives there.
4. Compare responsibility, caller obligations, state transitions, concurrency/durability behavior, observability, and trade-offs only where they bear on the question.
5. Classify each mapping as `equivalent`, `partial analogy`, or `no equivalent`. Similar names do not prove equivalence; a negative claim records the areas and alternate terms searched.
6. Keep source facts, documented intent, runtime observations, and inference visibly separate. Cite revision, repository-relative path, symbol, and line range for substantive conclusions.

Finish this step when the shared scenario has a supported CUBRID trace and the nearest PostgreSQL/MySQL mapping, including honest gaps.

## 3. Choose Focused CUBRID Probes

Turn only material unknowns that static tracing cannot settle into runtime hypotheses. Run one probe by default and at most three unless the user requests a wider experiment.

Use the least invasive observation that can distinguish the hypothesis:

1. existing SQL-visible behavior, tests, logs, counters, or utilities;
2. debugger observation;
3. temporary, uniquely marked logging or a local probe function at a stable observation point.

Read [references/probe-safety.md](references/probe-safety.md) before running a probe or changing CUBRID source. PostgreSQL and MySQL remain source surveys unless the user explicitly requests their runtimes.

Finish this step when every planned probe names its hypothesis, action, observable result, and falsifying result.

## 4. Observe and Restore

For a non-mutating probe, use uniquely named owned resources, record the exact command and relevant output, and clean up only those resources.

For temporary CUBRID instrumentation:

1. Capture the baseline status and binary diff, require every target file to be clean, and run `just build` from the CUBRID worktree.
2. Add the smallest patch with a unique `CUBRID_CODE_SURVEY_<id>` marker. Preserve existing indentation exactly and obey the repository's `/* *INDENT-OFF* */` rules for C++ syntax in legacy `.c`/`.h` files.
3. Run `just build`, execute the focused reproducer, and record observer effects and alternative explanations.
4. Reverse only the exact instrumentation patch, verify the baseline status and diff are restored, and run `just build` again so installed binaries are clean.
5. Confirm that owned databases, files, watchers, and instrumented processes are gone. Stop and report exact evidence if restoration or cleanup cannot be proven.

Temporary probes are evidence, not product changes. Keep them only when the user separately asks for a permanent implementation.

## 5. Write the Survey

Write in the user's language and target roughly 500-1,200 words unless the question genuinely requires more. Use these sections:

1. `## Verdict` - the shortest defensible answer;
2. `## Shared Scenario` - the operation compared;
3. `## CUBRID Trace` - the relevant call path and state changes;
4. `## PostgreSQL and MySQL` - a compact three-engine comparison table plus important mismatches;
5. `## Runtime Probe` - hypothesis, command or patch point, observation, interpretation, and cleanup status, or why no safe probe was useful;
6. `## Unknowns` - unresolved questions and what would settle them;
7. `## Source Revisions` - roots, commits, and cited source locations.

Include only short decisive log excerpts. Preserve a separate reproducer only when inline commands would not be reliably repeatable; the Markdown note and optional reproducer are the complete artifact set.

Report the Markdown path, main conclusion, probes run, restoration status, and remaining unknowns.
