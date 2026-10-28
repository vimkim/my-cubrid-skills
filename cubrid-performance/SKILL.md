---
name: cubrid-performance
description: "Optimize CUBRID workloads, engine code, and utilities on Linux. Use for performance improvements, bottleneck diagnosis, scaling, or regression comparisons, with or without a baseline or existing profile. Triggers on phrases like 'make this faster', 'optimize CUBRID', 'compare performance with baseline', 'profile this without a baseline'."
---

# CUBRID Performance

Connect a performance goal to evidence, a focused change, and validation under the original workload conditions.
Support both comparative experiments and investigations of one implementation.
Use the caller's requested scope: diagnosis, source review, implementation, or measurement.

## 1. Establish the task and comparison mode

Read `/home/vimkim/my-cubrid/CUBRID.md` and applicable repository instructions.
Inspect the source checkout, branch, worktrees, and changes before selecting a task checkout.
Search `my-cubrid-docs` for relevant design and experiment evidence.
Consult `my-cubrid-jira` when a ticket or PR supplies acceptance criteria.

Define the workload, successful completion unit, primary metric, and correctness constraints.
Examples include query elapsed, commit p99, utility runtime, throughput at a stated load, or CPU cost per successful transaction.
Record the requested target and the experiment budget when supplied.
Otherwise state a reasonable scope and choose bounded measurements.
Ask only for missing information that changes the workload, acceptance criteria, or authorized environment.

| Available context | Action | Permitted conclusion |
| --- | --- | --- |
| Named baseline revision, branch, binary, or prior run | Identify both implementations and check comparability before A/B measurement. | Quantify change against that baseline within the measured conditions. |
| Runnable current implementation, no supplied baseline | Measure the current workload and locate its limiter. Preserve a pre-change measurement when practical. | Report current costs. Claim an improvement only with a valid comparison. |
| Explicit request without comparison | Measure the chosen implementation against its absolute target and investigate its costs. | Report target attainment and bottleneck evidence. A speedup remains unmeasured. |
| Source only, missing runtime, or unavailable workload | Examine the relevant path and prepare a bounded reproducer if feasible. | Report optimization candidates and validation gaps. Runtime gains remain unverified. |

An absent baseline is not a blocker.
An explicit no-comparison request does not require building a historical version.
Treat imported benchmark numbers as context until their workload, environment, and binary identities match.

## 2. Prepare a valid experiment

Read [experiments.md](references/experiments.md) before preparing builds, workload state, or performance comparisons.
Use `cubrid-build` and the live preset-aware `just` interface for engine builds.
Performance measurement warrants an optimized preset, normally `release_gcc` when available.
Check actual optimization, assertions, symbols, install prefix, and loaded runtime.
Keep debugger and sanitizer builds separate from final timing builds.

Identify the actual server, broker, client, utility, and background processes needed for the question.
Check their binary paths and build identities.
Read the host-workenv reference required by `CUBRID.md` before host DB setup or daemon startup.
Use separate install and database locations for incompatible builds.
Preserve the input, configuration, expected results, and commands with the experiment artifacts.

Finish this step with a runnable workload and a correctness check, or a concrete explanation of the unavailable prerequisite.
Continue independent source analysis when execution is unavailable.

## 3. Identify the limiting work or wait

Read [measurement.md](references/measurement.md) when collecting or interpreting runtime evidence.
Start with workload errors, host errors, resource pressure, and request-related thread states.
Check utilization, saturation, and errors for relevant resources.
Record unavailable observations as `unknown` with their reason.
Identify client limits, CPU quota, or environmental interference before attributing a result to engine code.

Write plausible competing explanations and select the smallest measurement that distinguishes them.
For each hypothesis, state its supporting evidence, predicted change, and refutation condition.
Normalize counters by successful completed work from the same collection interval.

Route detailed work only when the evidence requires it:

- Use `linux-perf` for CPU counters, call paths, cache contention, or low/high-concurrency profiles.
- Use `performance-patterns` for a matching source or profile pattern, including a source-only review.
- Use `cubrid-manual-search` for version-specific plan, statistics, configuration, or utility commands.
- Use `cubrid-oos-context` when required OOS behavior constrains the proposed change.

Treat pattern matches, IPC cutoffs, and HITM percentages as hypotheses.
Check PMU support, event meaning, and the actual code and data path.
When profiling is unavailable, use workload timing, DB counters, supported software events, or bounded internal instrumentation.
Label the evidence these alternatives cannot supply.

## 4. Make one explained change

For implementation requests, connect the chosen change to the predicted limiting cost.
Examples include eliminating repeated work, reducing allocations or copying, batching, shortening lock hold time, or improving locality.
Inspect compiler diagnostics and the executed assembly when a loop or code-generation claim needs them.
Use a representative microbenchmark to isolate alternatives when useful.
Check their relevance to the original workload separately.

Preserve SQL results, error behavior, object lifetime, concurrency contracts, durability, and supported hardware behavior.
Check invariants before moving validation or caching results across iterations.
Check alignment, bounds, aliasing, numerical semantics, and ISA dispatch before vectorization changes.
Keep build flags, allocator changes, PGO, LTO, and host tuning as individually attributable experiments.

Use thread-local counters or histograms for frequent instrumentation.
Measure instrumentation overhead and remove temporary probes unless retained observability serves the task.
Preserve unrelated edits when reverting an unsuccessful experiment.
Retain measured optimizations that meet the correctness constraints and performance goal.
For unmeasured implementations, report the provisional result and remaining checks.
If a candidate fails, test the next supported hypothesis within the task's scope and budget.
For diagnosis or source-review requests, stop at evidence and recommendations within that scope.

## 5. Check the goal and report the limit of the evidence

Run the relevant build and focused correctness checks after implementation.
Use the SQL, shell, or medium runner skill when that regression suite is necessary.
Run sanitizer or race checks when the changed behavior warrants them.
Record checks that could not run and their reasons.

Repeat final measurements with the original optimized runtime conditions and minimal collection overhead.
For comparisons, use matched state and serial, alternating or randomized A/B runs.
For one implementation, repeat its absolute measurements and assess the stated target.
Preserve individual results, successful completion counts, errors, and observed variation.
Report improvements smaller than unresolved variation as inconclusive.
Stop at the agreed scope or budget when evidence remains inconclusive.
Give the next experiment that would resolve the uncertainty.

Store substantive experiment records in the task's directory in `my-cubrid-docs`.
Follow that repository's worktree and commit workflow for saved records.
Keep large raw profiles outside Git unless the repository explicitly tracks such artifacts.
Link their retained locations from the record.
Use the fields in [experiments.md](references/experiments.md#experiment-record).

Report the outcome first: measured improvement, target met or missed, candidate change awaiting measurement, or unresolved diagnosis.
Include the limiter evidence, relevant code change, correctness results, measurement scope, and remaining uncertainty.
Identify the comparison denominator for every percentage.
A diagnosis, source cleanup, smaller instruction count, or faster microbenchmark alone does not establish an end-to-end gain.

Read [sources.md](references/sources.md) for the source guides and their roles.
